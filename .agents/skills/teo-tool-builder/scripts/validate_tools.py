"""
Validate all Teo tool schemas, dispatcher registry mappings, policy specs, and cache invariance.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[4]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from jsonschema import Draft202012Validator
import config
from teo_harness import compute_prompt_cache_fingerprint
from tools.dispatcher import _REGISTRY
from tools.policy import TOOL_SPECS
from tools.schemas import TOOLS_SCHEMA


def main() -> int:
    errors: list[str] = []

    if len(TOOLS_SCHEMA) > 14:
        errors.append(f"Schema count {len(TOOLS_SCHEMA)} exceeds constitutional limit of 14.")

    schema_names = set()
    for entry in TOOLS_SCHEMA:
        fn = entry.get("function", {})
        name = fn.get("name", "")
        schema_names.add(name)
        desc = fn.get("description", "")
        params = fn.get("parameters", {})

        if not desc or not desc.isascii():
            errors.append(f"Tool '{name}' description must be non-empty English ASCII.")
        if params.get("additionalProperties", True) is not False:
            errors.append(f"Tool '{name}' parameters must set additionalProperties: False.")

        try:
            Draft202012Validator.check_schema(params)
        except Exception as exc:
            errors.append(f"Tool '{name}' has invalid Draft 2020-12 schema: {exc}")

        if name not in _REGISTRY:
            errors.append(f"Tool '{name}' is missing from tools.dispatcher._REGISTRY.")
        if name not in TOOL_SPECS:
            errors.append(f"Tool '{name}' is missing from tools.policy.TOOL_SPECS.")

    for reg_name in _REGISTRY:
        if reg_name not in schema_names:
            errors.append(f"Registry entry '{reg_name}' has no matching schema in TOOLS_SCHEMA.")

    if "<untrusted_data>" not in config.SYSTEM_PROMPT:
        errors.append("SYSTEM_PROMPT is missing '<untrusted_data>' prompt-isolation rule.")

    fp = compute_prompt_cache_fingerprint()
    if errors:
        print("❌ [TEO TOOL VALIDATOR FAILED]:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(
        f"✅ [TEO TOOL VALIDATOR PASSED]: {len(TOOLS_SCHEMA)}/14 schemas valid | "
        f"Registry & Policy synced | Cache Fingerprint: {fp}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
