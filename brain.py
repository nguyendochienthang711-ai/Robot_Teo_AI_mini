import asyncio
import json
import logging
import re
import threading
import time
from dataclasses import dataclass
from typing import Callable

import aiohttp
from openai import AsyncOpenAI

from audio_io import (
    fetch_tts_bytes_smart,
    play_audio_bytes_sync,
    set_background_music_volume,
    stop_audio_playback,
)
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, MODEL_NAME, SYSTEM_PROMPT
from teo_harness import (
    PRIO_DOC_READER,
    PRIO_SPEECH,
    TurnTrace,
    compute_prompt_cache_fingerprint,
    record_turn_trace,
    state_machine,
)
from tools import TOOLS_SCHEMA, ToolResult, TurnContext, run_tool
from tools.documents import _split_into_sentences, _wrap_long
from tools.guardrails import (
    check_input_guardrail,
    clear_pending_action,
    detect_hitl_intent,
    get_pending_action,
    sanitize_output_guardrail,
)
from tools.policy import TOOL_SPECS, risk_of

log = logging.getLogger("teo.brain")

SENT_RE = re.compile(r"(?<![.\d])([.!?])(?![.\d])\s+")
_ABBREV_TAIL_RE = re.compile(r"(?:^|\s)(?:tp|ts|gs|bs|ks|mr|dr|ms|st|ths|pgs|q|p)\.$", re.I)
_SYS_TIME_PREFIX_RE = re.compile(r"^\[Giờ hệ thống:[^\]]+\]\s*")

TOOL_TIMEOUT: dict[str, float] = {
    "nhin_man_hinh_laptop": 25.0,
    "tra_cuu_thong_tin_truc_tuyen": 10.0,
    "phat_nhac_va_dieu_khien_media": 10.0,
}
DEFAULT_TOOL_TIMEOUT = 8.0
MAX_TOOL_ROUNDS = 2
MAX_HISTORY_TURNS = 8


@dataclass
class SpeakItem:
    text: str
    on_done: Callable[[], None] | None = None
    priority: int = PRIO_SPEECH


_llm_client: AsyncOpenAI | None = None
_abort_speaking = threading.Event()


def get_llm_client() -> AsyncOpenAI:
    """Lazy-initialize AsyncOpenAI client (avoids import-time exit during testing)."""
    global _llm_client
    if _llm_client is None:
        _llm_client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY or "missing-api-key",
            base_url=DEEPSEEK_BASE_URL,
            timeout=30.0,
        )
    return _llm_client


def stop_speaking() -> None:
    """Abort current TTS synthesis and immediately stop audio playback (R-24)."""
    _abort_speaking.set()
    stop_audio_playback()


chat_history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]


def trim_chat_history(history: list[dict], max_turns: int = MAX_HISTORY_TURNS) -> None:
    """
    Keep system prompt at index 0 and at most `max_turns` recent user turns (R-05).
    Slices only at 'user' message boundaries so assistant.tool_calls + tool pairs are never orphaned.
    """
    if not history:
        return
    user_indices = [i for i, m in enumerate(history) if i > 0 and m.get("role") == "user"]
    if len(user_indices) > max_turns:
        cut_at = user_indices[-max_turns]
        del history[1:cut_at]


async def stream_llm_and_speak(
    http_session: aiohttp.ClientSession,
    user_message: str | None = None,
) -> str:
    """
    3-tier Streaming Pipeline with:
    - Input & Output Guardrails (DLP secret redaction & prompt injection filter)
    - Human-in-the-Loop (HITL) voice/text confirmation ("OK" / "Đồng ý") for laptop data operations
    - Transactional chat_history, async tool execution with timeouts, and direct TTS speaking.
    """
    _abort_speaking.clear()
    t_turn = time.perf_counter()
    fp_before = compute_prompt_cache_fingerprint(
        chat_history[0]["content"] if chat_history else SYSTEM_PROMPT, TOOLS_SCHEMA
    )
    state_machine.clear_turn_transitions()
    state_machine.set_state("THINKING", detail="turn_start")

    sentence_queue: asyncio.Queue[SpeakItem | None] = asyncio.Queue()
    audio_queue: asyncio.Queue[tuple[int, SpeakItem, bytes, float, str] | None] = asyncio.Queue()
    full_reply_parts: list[str] = []
    spoken_sentences_log: list[str] = []
    tool_calls_log: list[dict] = []
    ttft_recorded_ms: float = 0.0
    ttfa_recorded_ms: float = 0.0

    raw_user_utterance = ""
    if user_message is not None:
        raw_user_utterance = _SYS_TIME_PREFIX_RE.sub("", user_message).strip()
        allowed_in, cleaned_or_reason = check_input_guardrail(raw_user_utterance)
        if not allowed_in:
            # Speak guardrail rejection directly without calling LLM (0 tokens used)
            async def _speak_rejection():
                await sentence_queue.put(SpeakItem(text=cleaned_or_reason))
                await sentence_queue.put(None)

            # Reuse tts_worker and player_worker below
            user_message = None
            raw_user_utterance = f"__GUARDRAIL_REJECT__:{cleaned_or_reason}"

    working_history: list[dict] = list(chat_history)
    if user_message is not None:
        working_history.append({"role": "user", "content": user_message})

    ctx = TurnContext(require_hitl=True)
    turn_succeeded = False

    async def _enqueue_safe_sentence(
        text: str,
        on_done: Callable[[], None] | None = None,
        priority: int = PRIO_SPEECH,
    ) -> None:
        safe_text = sanitize_output_guardrail(text)
        if safe_text:
            spoken_sentences_log.append(safe_text)
            await sentence_queue.put(SpeakItem(text=safe_text, on_done=on_done, priority=priority))

    async def _emit_sentences_from_buf(buf: str, first_emitted: bool, label: str) -> tuple[str, bool]:
        """Extract all completed sentences from buffer and enqueue for TTS (R-06)."""
        nonlocal ttft_recorded_ms
        search_pos = 0
        while True:
            m = SENT_RE.search(buf, search_pos)
            if not m:
                break
            if m.group(1) == "." and _ABBREV_TAIL_RE.search(buf[: m.start() + 1].strip()):
                search_pos = m.end()
                continue
            if len(buf[: m.end()].strip()) < 6:
                break
            sent = buf[: m.end()].strip()
            buf = buf[m.end() :]
            search_pos = 0
            if not first_emitted:
                first_emitted = True
                llm_first_ms = (time.perf_counter() - t_turn) * 1000
                if ttft_recorded_ms == 0.0:
                    ttft_recorded_ms = round(llm_first_ms, 1)
                print(f"🧠 [{label} ({llm_first_ms:.0f} ms)]: \"{sanitize_output_guardrail(sent)}\"")
            await _enqueue_safe_sentence(sent)
        return buf, first_emitted

    async def llm_producer():
        nonlocal turn_succeeded, ttft_recorded_ms
        client = get_llm_client()
        try:
            # 1. Handle Input Guardrail rejection fast-path
            if raw_user_utterance.startswith("__GUARDRAIL_REJECT__:"):
                reason = raw_user_utterance.split(":", 1)[1]
                full_reply_parts.append(reason)
                await _enqueue_safe_sentence(reason)
                return

            # 2. Check if user is responding ("OK" / "Đồng ý" / "Hủy") to a pending HITL action
            pending = get_pending_action()
            if pending is not None and raw_user_utterance:
                intent = detect_hitl_intent(raw_user_utterance)
                if intent == "reject":
                    clear_pending_action()
                    cancel_msg = f"Dạ vâng, em đã hủy thao tác {pending.description_vi} theo ý sếp."
                    full_reply_parts.append(cancel_msg)
                    await _enqueue_safe_sentence(cancel_msg)
                    turn_succeeded = True
                    return
                elif intent == "confirm":
                    clear_pending_action()
                    ctx.confirmed = True
                    timeout_sec = TOOL_TIMEOUT.get(pending.func_name, DEFAULT_TOOL_TIMEOUT)
                    try:
                        res: ToolResult = await asyncio.wait_for(
                            asyncio.to_thread(run_tool, pending.func_name, pending.args_json, ctx),
                            timeout=timeout_sec,
                        )
                    except asyncio.TimeoutError:
                        res = ToolResult(
                            text=f"ERROR tool_timeout: {pending.func_name} timed out after {timeout_sec}s.",
                            ok=False,
                        )

                    if res.speak and not _abort_speaking.is_set():
                        raw_sents = _split_into_sentences(res.speak) or [res.speak]
                        speak_chunks = [p for s in raw_sents for p in _wrap_long(s, limit=180)] or [res.speak]
                        for i, piece in enumerate(speak_chunks):
                            cb = res.commit if (i == len(speak_chunks) - 1) else None
                            await _enqueue_safe_sentence(piece, on_done=cb, priority=PRIO_DOC_READER)
                        confirm_msg = f"Em đang đọc tài liệu cho sếp ngay đây ạ."
                        full_reply_parts.append(confirm_msg)
                        turn_succeeded = True
                        return
                    else:
                        if res.commit:
                            try:
                                res.commit()
                            except Exception:
                                log.exception("Commit callback error")
                        confirm_ctx_msg = (
                            f"[Sếp đã xác nhận ĐỒNG Ý cho phép {pending.description_vi}. "
                            f"Kết quả thực thi công cụ {pending.func_name}]: {res.text}"
                        )
                        if working_history and working_history[-1].get("role") == "user":
                            working_history[-1]["content"] = (
                                f"{working_history[-1]['content']}\n{confirm_ctx_msg}"
                            )
                        else:
                            working_history.append({"role": "user", "content": confirm_ctx_msg})
                else:
                    clear_pending_action()

            # 3. Normal LLM streaming + multi-round tool loop
            for round_idx in range(MAX_TOOL_ROUNDS + 1):
                if _abort_speaking.is_set():
                    break

                stream = await client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=working_history,
                    tools=TOOLS_SCHEMA,
                    tool_choice="auto" if round_idx < MAX_TOOL_ROUNDS else "none",
                    stream=True,
                    temperature=0.6,
                    max_tokens=180,
                )

                buf = ""
                first_sent_emitted = False
                tool_calls_acc: dict[int, dict] = {}
                round_text_parts: list[str] = []

                async for chunk in stream:
                    if _abort_speaking.is_set():
                        break
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta

                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_acc:
                                tool_calls_acc[idx] = {"id": tc.id or "", "name": "", "args": ""}
                            if tc.id:
                                tool_calls_acc[idx]["id"] = tc.id
                            if tc.function and tc.function.name:
                                tool_calls_acc[idx]["name"] += tc.function.name
                            if tc.function and tc.function.arguments:
                                tool_calls_acc[idx]["args"] += tc.function.arguments

                    content = delta.content or ""
                    if content:
                        round_text_parts.append(content)
                        full_reply_parts.append(content)
                        buf += content
                        label = "DeepSeek Stream Câu 1" if round_idx == 0 else "DeepSeek Sau Tool Câu 1"
                        buf, first_sent_emitted = await _emit_sentences_from_buf(buf, first_sent_emitted, label)

                if buf.strip() and not _abort_speaking.is_set():
                    sent = buf.strip()
                    if not first_sent_emitted:
                        llm_first_ms = (time.perf_counter() - t_turn) * 1000
                        if ttft_recorded_ms == 0.0:
                            ttft_recorded_ms = round(llm_first_ms, 1)
                        print(f"🧠 [DeepSeek Stream Câu 1 ({llm_first_ms:.0f} ms)]: \"{sanitize_output_guardrail(sent)}\"")
                    await _enqueue_safe_sentence(sent)
                    buf = ""

                if not tool_calls_acc:
                    break

                assistant_tc_msg = {
                    "role": "assistant",
                    "content": "".join(round_text_parts) or None,
                    "tool_calls": [
                        {
                            "id": v["id"],
                            "type": "function",
                            "function": {"name": v["name"], "arguments": v["args"]},
                        }
                        for v in tool_calls_acc.values()
                    ],
                }
                working_history.append(assistant_tc_msg)
                full_reply_parts.clear()

                async def _exec_one_tc(v: dict) -> tuple[dict, ToolResult]:
                    t_name = v["name"]
                    t_args = v["args"]
                    timeout_sec = TOOL_TIMEOUT.get(t_name, DEFAULT_TOOL_TIMEOUT)

                    if t_name == "doc_va_tom_tat_tai_lieu" and '"dung"' in t_args:
                        stop_speaking()

                    try:
                        res = await asyncio.wait_for(
                            asyncio.to_thread(run_tool, t_name, t_args, ctx),
                            timeout=timeout_sec,
                        )
                    except asyncio.TimeoutError:
                        log.warning("Tool %s timed out after %ss", t_name, timeout_sec)
                        res = ToolResult(
                            text=f"ERROR tool_timeout: {t_name} timed out after {timeout_sec}s.",
                            ok=False,
                        )
                    return v, res

                tc_list = list(tool_calls_acc.values())
                can_parallel = False
                if len(tc_list) > 1:
                    has_untrusted = any(
                        (spec := TOOL_SPECS.get(tc["name"])) is not None and spec.untrusted_output
                        for tc in tc_list
                    )
                    has_side_effect = False
                    for tc in tc_list:
                        try:
                            parsed = json.loads(tc["args"]) if tc["args"] else {}
                            if not isinstance(parsed, dict):
                                parsed = {}
                        except Exception:
                            parsed = {}
                        if risk_of(tc["name"], parsed) in ("write", "destructive", "physical"):
                            has_side_effect = True
                            break
                    can_parallel = not (has_untrusted and has_side_effect)

                if can_parallel:
                    executed_pairs = await asyncio.gather(*(_exec_one_tc(v) for v in tc_list))
                else:
                    executed_pairs = []
                    for v in tc_list:
                        executed_pairs.append(await _exec_one_tc(v))

                for v, res in executed_pairs:
                    t_name = v["name"]
                    tool_calls_log.append(
                        {
                            "name": t_name,
                            "ok": res.ok,
                            "tainted": res.tainted,
                            "hitl_pending": res.text.startswith("PENDING_HITL_CONFIRMATION"),
                        }
                    )
                    if res.text.startswith("PENDING_HITL_CONFIRMATION"):
                        state_machine.set_state("HITL_CONFIRM", detail=t_name)

                    if res.speak and not _abort_speaking.is_set():
                        raw_sents = _split_into_sentences(res.speak) or [res.speak]
                        speak_chunks = [p for s in raw_sents for p in _wrap_long(s, limit=180)] or [res.speak]
                        for i, piece in enumerate(speak_chunks):
                            cb = res.commit if (i == len(speak_chunks) - 1) else None
                            await _enqueue_safe_sentence(piece, on_done=cb, priority=PRIO_DOC_READER)
                        llm_tool_text = (
                            "Direct TTS is already reading the requested document sentences aloud to the user. "
                            "Reply with at most one short confirmation sentence."
                        )
                    else:
                        if res.commit:
                            try:
                                res.commit()
                            except Exception:
                                log.exception("Commit callback error")
                        llm_tool_text = res.text

                    working_history.append(
                        {"role": "tool", "tool_call_id": v["id"], "content": llm_tool_text}
                    )

            turn_succeeded = True
        finally:
            await sentence_queue.put(None)

    async def tts_worker():
        idx = 0
        turn_prefer_fast = False
        while True:
            item = await sentence_queue.get()
            if item is None:
                await audio_queue.put(None)
                break
            if _abort_speaking.is_set():
                continue
            audio_bytes, tts_ms, voice_used, turn_prefer_fast = await fetch_tts_bytes_smart(
                http_session, item.text, is_first_sentence=(idx == 0), prefer_fast=turn_prefer_fast
            )
            if audio_bytes and not _abort_speaking.is_set():
                idx += 1
                await audio_queue.put((idx, item, audio_bytes, tts_ms, voice_used))

    async def player_worker():
        nonlocal ttfa_recorded_ms
        while True:
            q_item = await audio_queue.get()
            if q_item is None:
                break
            idx, speak_item, audio_bytes, tts_ms, voice_used = q_item
            if _abort_speaking.is_set():
                continue
            if idx == 1:
                ttfa = (time.perf_counter() - t_turn) * 1000
                ttfa_recorded_ms = round(ttfa, 1)
                state_machine.set_state("SPEAKING", detail="tts_playing")
                print(
                    f"⚡ [Tèo TTS Câu 1 ({tts_ms:.0f} ms | Tổng phản hồi: {ttfa:.0f} ms | {voice_used})]: Phát âm thanh ngay!"
                )
            print(f"   🤖 [Tèo nói câu {idx} ({tts_ms:.0f} ms | {voice_used})]: {speak_item.text}")

            if speak_item.priority != PRIO_SPEECH:
                await asyncio.to_thread(
                    play_audio_bytes_sync,
                    audio_bytes,
                    _abort_speaking,
                    speak_item.priority,
                    "doc_reader",
                )
            else:
                await asyncio.to_thread(play_audio_bytes_sync, audio_bytes, _abort_speaking)

            if speak_item.on_done and not _abort_speaking.is_set():
                try:
                    speak_item.on_done()
                except Exception:
                    log.exception("on_done callback error")

        set_background_music_volume(duck=False)

    await asyncio.gather(llm_producer(), tts_worker(), player_worker())

    final_reply = sanitize_output_guardrail("".join(full_reply_parts).strip())
    if turn_succeeded:
        if final_reply:
            working_history.append({"role": "assistant", "content": final_reply})
        chat_history[:] = working_history
        trim_chat_history(chat_history)

    if get_pending_action() is not None:
        state_machine.set_state("HITL_CONFIRM", detail="awaiting_user_confirm")
    else:
        state_machine.set_state("IDLE", detail="turn_complete")

    fp_after = compute_prompt_cache_fingerprint(
        chat_history[0]["content"] if chat_history else SYSTEM_PROMPT, TOOLS_SCHEMA
    )
    total_ms = round((time.perf_counter() - t_turn) * 1000, 1)
    record_turn_trace(
        TurnTrace(
            turn_id=f"turn_{int(time.time() * 1000)}",
            timestamp=round(time.time(), 3),
            raw_user_text=raw_user_utterance,
            cache_fingerprint_before=fp_before,
            cache_fingerprint_after=fp_after,
            cache_invariant_ok=(fp_before == fp_after),
            state_transitions=[t["state"] for t in state_machine.get_turn_transitions()],
            tool_calls=tool_calls_log,
            hitl_triggered=(get_pending_action() is not None or ctx.confirmed),
            tainted_turn=ctx.tainted,
            spoken_sentences=spoken_sentences_log,
            final_reply=final_reply,
            ttft_ms=ttft_recorded_ms,
            ttfa_ms=ttfa_recorded_ms,
            total_ms=total_ms,
        )
    )

    return final_reply
