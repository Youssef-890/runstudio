"""Run JavaScript on the server with Node.js (subprocess, bounded runtime)."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

TIMEOUT_SEC = 15


def run_javascript(code: str) -> tuple[str, str]:
    node = shutil.which("node")
    if not node:
        return "", "Node.js is not installed or not on PATH.\n"

    with tempfile.TemporaryDirectory(prefix="repl_js_") as td:
        src = Path(td) / "snippet.mjs"
        src.write_text(code, encoding="utf-8")
        try:
            proc = subprocess.run(
                [node, str(src)],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SEC,
                cwd=td,
                env={**os.environ, "NODE_NO_WARNINGS": "1"},
            )
        except subprocess.TimeoutExpired:
            return "", "Node.js execution timed out.\n"
        except OSError as e:
            return "", f"Could not start Node.js: {e}\n"
        out = proc.stdout or ""
        err = proc.stderr or ""
        if proc.returncode != 0 and not err:
            err = f"Process exited with code {proc.returncode}.\n"
        return out, err
