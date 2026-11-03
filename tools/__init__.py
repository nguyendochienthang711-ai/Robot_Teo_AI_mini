"""
Teo AI Robot Secretary - Modular Tools Package.
Optimized with lazy module loading and strict schema validation (TL-14).
"""

from tools.dispatcher import execute_tool_call
from tools.schemas import TOOLS_SCHEMA

__all__ = ["TOOLS_SCHEMA", "execute_tool_call"]
