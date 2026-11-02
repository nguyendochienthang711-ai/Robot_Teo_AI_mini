import asyncio
import io
import re
import sys
import time
import aiohttp
import pygame
from openai import AsyncOpenAI

from audio_io import fetch_tts_bytes_smart, set_background_music_volume
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, MODEL_NAME, SYSTEM_PROMPT
from tools import TOOLS_SCHEMA, execute_tool_call

if not DEEPSEEK_API_KEY:
    print("❌ Lỗi: Chưa tìm thấy DEEPSEEK_API_KEY trong file .env!")
    sys.exit(1)

llm_client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
    timeout=30.0,
)

chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]


async def stream_llm_and_speak(http_session: aiohttp.ClientSession) -> str:
    """
    Pipeline Streaming 3 tầng:
    [Tầng 1: DeepSeek stream=True + Tool Calls] -> [Tầng 2: TTS Worker] -> [Tầng 3: Loa Pygame]
    """
    t_turn = time.perf_counter()
    sentence_queue: asyncio.Queue[str | None] = asyncio.Queue()
    audio_queue: asyncio.Queue[tuple[int, str, bytes, float, str] | None] = asyncio.Queue()
    full_reply_parts: list[str] = []

    async def llm_producer():
        try:
            stream = await llm_client.chat.completions.create(
                model=MODEL_NAME,
                messages=chat_history,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                stream=True,
                temperature=0.6,
                max_tokens=180,
            )
            buf = ""
            first_sent_emitted = False
            tool_calls_acc = {}

            async for chunk in stream:
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
                    full_reply_parts.append(content)
                    buf += content
                    if not first_sent_emitted:
                        m = re.search(r"(?<![.])([.!?])(?![.])\s+", buf)
                        if m and len(buf[: m.end()].strip()) >= 6:
                            sent = buf[: m.end()].strip()
                            buf = buf[m.end() :]
                            first_sent_emitted = True
                            llm_first_ms = (time.perf_counter() - t_turn) * 1000
                            print(f"🧠 [DeepSeek Stream Câu 1 ({llm_first_ms:.0f} ms)]: \"{sent}\"")
                            await sentence_queue.put(sent)

            if tool_calls_acc:
                if buf.strip():
                    await sentence_queue.put(buf.strip())
                    buf = ""

                assistant_tc_msg = {
                    "role": "assistant",
                    "content": "".join(full_reply_parts) or None,
                    "tool_calls": [
                        {
                            "id": v["id"],
                            "type": "function",
                            "function": {"name": v["name"], "arguments": v["args"]},
                        }
                        for v in tool_calls_acc.values()
                    ],
                }
                chat_history.append(assistant_tc_msg)
                full_reply_parts.clear()
                first_sent_emitted = False

                for v in tool_calls_acc.values():
                    tool_result = execute_tool_call(v["name"], v["args"])
                    chat_history.append(
                        {"role": "tool", "tool_call_id": v["id"], "content": tool_result}
                    )

                follow_stream = await llm_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=chat_history,
                    stream=True,
                    temperature=0.6,
                    max_tokens=150,
                )
                async for chunk in follow_stream:
                    c = chunk.choices[0].delta.content or ""
                    if c:
                        full_reply_parts.append(c)
                        buf += c
                        if not first_sent_emitted:
                            m = re.search(r"(?<![.])([.!?])(?![.])\s+", buf)
                            if m and len(buf[: m.end()].strip()) >= 6:
                                sent = buf[: m.end()].strip()
                                buf = buf[m.end() :]
                                first_sent_emitted = True
                                print(f"🧠 [DeepSeek Sau Tool Câu 1]: \"{sent}\"")
                                await sentence_queue.put(sent)

            if buf.strip():
                sent = buf.strip()
                if not first_sent_emitted:
                    llm_first_ms = (time.perf_counter() - t_turn) * 1000
                    print(f"🧠 [DeepSeek Stream Câu 1 ({llm_first_ms:.0f} ms)]: \"{sent}\"")
                await sentence_queue.put(sent)
        finally:
            await sentence_queue.put(None)

    async def tts_worker():
        idx = 0
        turn_prefer_fast = False
        while True:
            sent = await sentence_queue.get()
            if sent is None:
                await audio_queue.put(None)
                break
            audio_bytes, tts_ms, voice_used, turn_prefer_fast = await fetch_tts_bytes_smart(
                http_session, sent, is_first_sentence=(idx == 0), prefer_fast=turn_prefer_fast
            )
            if audio_bytes:
                idx += 1
                await audio_queue.put((idx, sent, audio_bytes, tts_ms, voice_used))

    async def player_worker():
        while True:
            item = await audio_queue.get()
            if item is None:
                break
            idx, sent, audio_bytes, tts_ms, voice_used = item
            if idx == 1:
                ttfa = (time.perf_counter() - t_turn) * 1000
                print(
                    f"⚡ [Tèo TTS Câu 1 ({tts_ms:.0f} ms | Tổng phản hồi: {ttfa:.0f} ms | {voice_used})]: Phát âm thanh ngay!"
                )
            print(f"   🤖 [Tèo nói câu {idx} ({tts_ms:.0f} ms | {voice_used})]: {sent}")

            sound_stream = io.BytesIO(audio_bytes)
            pygame.mixer.music.load(sound_stream)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.02)
            pygame.mixer.music.unload()

        set_background_music_volume(duck=False)

    await asyncio.gather(llm_producer(), tts_worker(), player_worker())
    return "".join(full_reply_parts).strip()
