---
name: teo-tool-builder
description: >-
  Guides the creation, consolidation, and modification of tools for Robot AI Assistant "Tèo"
  following the Spec-Kit standard, Draft 2020-12 JSON Schema validation, Policy risk classification,
  DLP/HITL guardrails, and 100% Prompt Cache Invariance. Use this skill whenever adding a new tool,
  updating an existing tool schema in tools/schemas.py, or editing handlers in tools/*.py.
---

# Teo Tool Builder Skill (Spec-Kit & Guardrails Standard)

Use this skill whenever adding, consolidating, or modifying any tool in the `tools/` package of Robot **"Tèo"**.

## 1. Constitutional Constraints (Mandatory)

1. **Tool Consolidation ($\le 14$ Schemas):**
   - `TOOLS_SCHEMA` in [`tools/schemas.py`](../../../tools/schemas.py) MUST NOT exceed **14** active tool schemas.
   - Prefer consolidating related sub-actions into an existing tool via an enum parameter (`thao_tac` or `che_do`) before adding a new top-level tool.
2. **Schema Format (JSON Schema Draft 2020-12):**
   - Tool function names use Vietnamese `snake_case` without accents (e.g. `quan_ly_cong_viec`).
   - All `description` fields in `TOOLS_SCHEMA` MUST be **100% English ASCII** to minimize token usage.
   - Every tool's top-level `parameters` object MUST declare `"additionalProperties": False`.
3. **100% Prompt Cache Prefix Invariance:**
   - Never mutate `config.SYSTEM_PROMPT` or `TOOLS_SCHEMA` at runtime.
4. **Spoken Vietnamese Output Contract:**
   - Handlers must return either a concise Vietnamese string ($1\text{–}3$ spoken sentences, no Markdown, no raw URLs, addressing user as `"sếp"` and self as `"em"`) or a `ToolResult(text=..., speak=..., commit=..., tainted=...)`.
   - On error, return a fail-closed string starting with `"ERROR <error_code>: <brief English instruction for LLM>"`.

## 2. Step-by-Step Implementation Procedure

1. **Specify Contract:**
   - Define the tool schema in [`tools/schemas.py`](../../../tools/schemas.py) with strict `enum` constraints and `"additionalProperties": False`.
2. **Register Policy & Risk Level:**
   - Add or update `TOOL_SPECS` and `risk_of(func_name, args)` in [`tools/policy.py`](../../../tools/policy.py):
     - `"read"`: Read-only operations. Set `untrusted_output=True` if reading external web, documents, clipboard, or screen.
     - `"write"`: Safe state modifications.
     - `"destructive"`: Deleting data or mutating sensitive host settings.
     - `"physical"`: Actuating servos or the 3-wheel Omni base (`tools/system.py`).
3. **Configure Guardrails & HITL Gate:**
   - If the action deletes user data, reads/writes the clipboard, reads local documents, or captures the laptop screen, register its Vietnamese description in `describe_hitl_action(func_name, args)` in [`tools/guardrails.py`](../../../tools/guardrails.py).
   - If arguments can carry untrusted text, validate them in `check_tool_args_guardrail(func_name, args)`.
4. **Register Lazy Handler in Dispatcher:**
   - Map `func_name: ("tools.<module>", "tool_<func_name>")` in `_REGISTRY` inside [`tools/dispatcher.py`](../../../tools/dispatcher.py).
   - Never eagerly import heavy third-party libraries in [`tools/__init__.py`](../../../tools/__init__.py).
5. **Validate & Test:**
   - Run the schema & policy validator script:
     ```powershell
     C:\Users\nguye\miniconda3\envs\teo\python.exe .agents/skills/teo-tool-builder/scripts/validate_tools.py
     ```
   - Add unit tests in [`test_tools.py`](../../../test_tools.py) and run:
     ```powershell
     C:\Users\nguye\miniconda3\envs\teo\python.exe -m unittest test_tools.py test_agent_harness.py
     ```
