"""
Restricted Python execution: exec() with a whitelisted __builtins__ set.
Not a full sandbox; suitable for controlled / local deployments only.
"""

from __future__ import annotations

import io
import sys
import traceback
from typing import Any

_SAFE_BUILTIN_NAMES = (
    "abs",
    "all",
    "any",
    "bin",
    "bool",
    "bytearray",
    "bytes",
    "chr",
    "dict",
    "divmod",
    "enumerate",
    "filter",
    "float",
    "format",
    "frozenset",
    "hash",
    "hex",
    "int",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "list",
    "map",
    "max",
    "memoryview",
    "min",
    "next",
    "oct",
    "ord",
    "pow",
    "print",
    "range",
    "repr",
    "reversed",
    "round",
    "set",
    "slice",
    "sorted",
    "str",
    "sum",
    "tuple",
    "zip",
)


def safe_builtins() -> dict[str, Any]:
    import builtins as bi

    out: dict[str, Any] = {}
    for name in _SAFE_BUILTIN_NAMES:
        if hasattr(bi, name):
            out[name] = getattr(bi, name)
    return out


def run_restricted(code: str) -> tuple[str, str]:
    """Returns (captured stdout/stderr text, traceback string or empty)."""
    buf = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    err_text = ""
    try:
        sys.stdout = sys.stderr = buf
        glo: dict[str, Any] = {"__builtins__": safe_builtins()}
        loc: dict[str, Any] = {}
        exec(code, glo, loc)
    except Exception:
        err_text = traceback.format_exc()
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return buf.getvalue(), err_text
