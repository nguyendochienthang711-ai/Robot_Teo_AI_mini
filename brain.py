import asyncio
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
from tools import TOOLS_SCHEMA, ToolResult, TurnContext, run_tool
from tools.documents import _split_into_sentences, _wrap_long

log = logging.getLogger("teo.brain")

SENT_RE = re.compile(r"(?<![.\d])([.!?])(?![.\d])\s+")

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
    3-tier Streaming Pipeline with transactional history, TurnContext policy,
    async tool execution with timeouts, and direct TTS speaking (R-01..R-07).
    """
    _abort_speaking.clear()
    t_turn = time.perf_counter()
    sentence_queue: asyncio.Queue[SpeakItem | None] = asyncio.Queue()
    audio_queue: asyncio.Queue[tuple[int, SpeakItem, bytes, float, str] | None] = asyncio.Queue()
    full_reply_parts: list[str] = []

    # Transactional working copy of chat_history so mid-turn errors never corrupt history (R-04)
    working_history: list[dict] = list(chat_history)
    if user_message is not None:
        working_history.append({"role": "user", "content": user_message})

    ctx = TurnContext()
    turn_succeeded = False

    async def _emit_sentences_from_buf(buf: str, first_emitted: bool, label: str) -> tuple[str, bool]:
        """Extract all completed sentences from buffer and enqueue for TTS (R-06)."""
        while True:
            m = SENT_RE.search(buf)
            if not m or len(buf[: m.end()].strip()) < 6:
                break
            sent = buf[: m.end()].strip()
            buf = buf[m.end() :]
            if not first_emitted:
                first_emitted = True
                llm_first_ms = (time.perf_counter() - t_turn) * 1000
                print(f"🧠 [{label} ({llm_first_ms:.0f} ms)]: \"{sent}\"")
            await sentence_queue.put(SpeakItem(text=sent))
        return buf, first_emitted

    async def llm_producer():
        nonlocal turn_succeeded
        client = get_llm_client()
        try:
            for round_idx in range(MAX_TOOL_ROUNDS + 1):
                if _abort_speaking.is_set():
                    break

                # Always send tools=TOOLS_SCHEMA to preserve prompt cache prefix across rounds (R-07)
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
                        print(f"🧠 [DeepSeek Stream Câu 1 ({llm_first_ms:.0f} ms)]: \"{sent}\"")
                    await sentence_queue.put(SpeakItem(text=sent))
                    buf = ""

                if not tool_calls_acc:
                    break

                # Record assistant tool_calls in working history
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

                # Execute each tool call off the event loop with per-tool timeout & shared TurnContext (R-01, R-02)
                for v in tool_calls_acc.values():
                    t_name = v["name"]
                    t_args = v["args"]
                    timeout_sec = TOOL_TIMEOUT.get(t_name, DEFAULT_TOOL_TIMEOUT)

                    if t_name == "doc_va_tom_tat_tai_lieu" and '"dung"' in t_args:
                        stop_speaking()

                    try:
                        res: ToolResult = await asyncio.wait_for(
                            asyncio.to_thread(run_tool, t_name, t_args, ctx),
                            timeout=timeout_sec,
                        )
                    except asyncio.TimeoutError:
                        log.warning("Tool %s timed out after %ss", t_name, timeout_sec)
                        res = ToolResult(
                            text=f"ERROR tool_timeout: {t_name} timed out after {timeout_sec}s.",
                            ok=False,
                        )

                    # Direct TTS path (R-03, R-16): stream sentences straight to TTS and commit bookmark after speech
                    if res.speak and not _abort_speaking.is_set():
                        raw_sents = _split_into_sentences(res.speak) or [res.speak]
                        speak_chunks = [p for s in raw_sents for p in _wrap_long(s, limit=180)] or [res.speak]
                        for i, piece in enumerate(speak_chunks):
                            cb = res.commit if (i == len(speak_chunks) - 1) else None
                            await sentence_queue.put(SpeakItem(text=piece, on_done=cb))
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
        while True:
            q_item = await audio_queue.get()
            if q_item is None:
                break
            idx, speak_item, audio_bytes, tts_ms, voice_used = q_item
            if _abort_speaking.is_set():
                continue
            if idx == 1:
                ttfa = (time.perf_counter() - t_turn) * 1000
                print(
                    f"⚡ [Tèo TTS Câu 1 ({tts_ms:.0f} ms | Tổng phản hồi: {ttfa:.0f} ms | {voice_used})]: Phát âm thanh ngay!"
                )
            print(f"   🤖 [Tèo nói câu {idx} ({tts_ms:.0f} ms | {voice_used})]: {speak_item.text}")

            await asyncio.to_thread(play_audio_bytes_sync, audio_bytes, _abort_speaking)

            # Only commit bookmark if sentence finished without being aborted (R-03, R-16)
            if speak_item.on_done and not _abort_speaking.is_set():
                try:
                    speak_item.on_done()
                except Exception:
                    log.exception("on_done callback error")

        set_background_music_volume(duck=False)

    await asyncio.gather(llm_producer(), tts_worker(), player_worker())

    final_reply = "".join(full_reply_parts).strip()
    if turn_succeeded:
        if final_reply:
            working_history.append({"role": "assistant", "content": final_reply})
        chat_history[:] = working_history
        trim_chat_history(chat_history)

    return final_reply
