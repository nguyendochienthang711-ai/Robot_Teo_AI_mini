---
name: teo-eval-benchmark
description: >-
  Runs the Dual-Mode Evaluation & Replay Harness for Robot AI Assistant "Tèo" (teo_harness.py),
  executes the full regression test suite (test_tools.py, test_sim_integration.py, test_agent_harness.py),
  and inspects agent traces and audit logs. Use this skill whenever verifying brain.py changes,
  benchmarking tool-call accuracy, testing HITL/guardrails, or diagnosing runtime issues.
---

# Teo Evaluation & Benchmark Skill

Use this skill to run deterministic offline replay tests, live DeepSeek API benchmarks, and audit/trace inspections for Robot **"Tèo"**.

## 1. Evaluation Modes

1. **Mode 1 — Offline Deterministic Replay (Default, 0 API Tokens, `< 2s`):**
   - Simulates DeepSeek SSE streaming chunks, multi-round tool calls, 2-turn HITL confirmation (both voice `"OK em"` and physical `TTP223` head touch packet), `LISTENING` Omni wheel lock, direct TTS document reading, and input/output DLP guardrails.
   - Command:
     ```powershell
     C:\Users\nguye\miniconda3\envs\teo\python.exe .agents/skills/teo-eval-benchmark/scripts/run_eval.py
     ```

2. **Mode 2 — Live DeepSeek API Benchmark (`--live`):**
   - Calls the live DeepSeek API configured in `.env`, measures `TTFT`/`TTFA` latency, grades spoken Vietnamese persona compliance (`<= 3 sentences`, no Markdown/URLs), and verifies 100% Prompt Cache Prefix Invariance.
   - Command:
     ```powershell
     C:\Users\nguye\miniconda3\envs\teo\python.exe .agents/skills/teo-eval-benchmark/scripts/run_eval.py --live
     ```

3. **Mode 3 — Full Regression Suite + Trace Audit Summary (`--full`):**
   - Runs `test_tools.py`, `test_sim_integration.py`, `test_agent_harness.py`, the deterministic eval suite, and prints a summary of recent `logs/agent_traces.jsonl` and `logs/tool_audit.jsonl` entries.
   - Command:
     ```powershell
     C:\Users\nguye\miniconda3\envs\teo\python.exe .agents/skills/teo-eval-benchmark/scripts/run_eval.py --full
     ```
