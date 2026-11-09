# AGENTS.md — Workspace Rules & Agent Harness Guide for Robot "Tèo" AI

@[ANTIGRAVITY.md](ANTIGRAVITY.md)

---

## 🛠️ Project Harness Architecture (Quick Reference)

1. **Runtime & Evaluation Harness ([`teo_harness.py`](teo_harness.py)):**
   - **State Machine (`state_machine`):** Synchronizes `IDLE`, `LISTENING`, `THINKING`, `HITL_CONFIRM`, `SPEAKING`, and `ALERT` across [`brain.py`](brain.py), [`audio_io.py`](audio_io.py), and [`teo_sim_runner.py`](teo_sim_runner.py) via HMAC-SHA256 signed UDP `state_sync` packets.
   - **No WS2812 LED Ring:** AI state is expressed via **ST7789 240×240 LCD eye expressions** (`eye_mood`, `eye_rgba`) + **upper-body arm micro-postures** (`arm_pose`).
   - **Listening Motor Lock:** While `state == "LISTENING"`, all 3 Omni wheels and servos are hard-locked (`wheel_locked = True`) so servo noise never enters the INMP441 microphone.
   - **Physical TTP223 Head Touch Confirmation:** Signed `robot_node` `touch_confirm` packets (or key `[T]` in the 3D simulator) confirm pending HITL operations or trigger barge-in (`stop_speaking`).
   - **Priority AudioBus (`audio_bus`):** Coordinates playback priorities (`0: ALERT/ALARM` > `1: SPEECH` > `2: DOC_READER`) so Pomodoro alarms preempt document reading cleanly.
   - **Dynamic Context Builder (`build_dynamic_user_message`):** Injects `[Giờ hệ thống: ... | Hẹn giờ đang chạy: ... | Ghi nhớ sếp: ...]` into the user message while keeping `SYSTEM_PROMPT` and `TOOLS_SCHEMA` at `chat_history[0]` 100% byte-identical.

2. **Workspace Skills (`.agents/skills/`):**
   - `teo-tool-builder`: Spec-Kit workflow and validator for adding/modifying consolidated tools ($\le 14$ schemas, Draft 2020-12, `additionalProperties: False`, Policy & Guardrails).
   - `teo-eval-benchmark`: Dual-mode evaluation & replay runner (offline deterministic SSE replay in `<1s` + `--live` DeepSeek benchmark + trace analysis).

3. **Lifecycle Hooks (`.agents/hooks.json`):**
   - Protects `.env` secrets on `PreToolUse`.
   - Runs automated Quality & Invariant Gates (`<= 14` schemas, `SYSTEM_PROMPT` cache invariance, `py_compile`) **once every 10 turns** (`PostInvocation`).

4. **Python Environment & Quality Gates:**
   - Always use the `teo` Conda environment: `C:\Users\nguye\miniconda3\envs\teo\python.exe`
   - Run full test & harness verification before completing code changes:
     ```powershell
     C:\Users\nguye\miniconda3\envs\teo\python.exe -m unittest test_tools.py test_sim_integration.py test_agent_harness.py
     C:\Users\nguye\miniconda3\envs\teo\python.exe teo_harness.py
     ```
