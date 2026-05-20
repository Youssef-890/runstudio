"""Compile and run C++ (g++ or clang++) in a temporary directory."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

COMPILE_TIMEOUT = 20
RUN_TIMEOUT = 15


def _no_compiler_help() -> str:
    if platform.system() == "Windows":
        return (
            "No C++ compiler found (g++ or clang++) on PATH.\n\n"
            "Install one of these, then restart RunStudio from a new terminal:\n"
            "  • winget install LLVM.LLVM\n"
            "    (clang++ — ensure LLVM\\bin is on your PATH)\n"
            "  • Or install MSYS2 (https://www.msys2.org/) and run:\n"
            "      pacman -S mingw-w64-ucrt-x86_64-gcc\n"
            "    then add the MinGW bin folder to PATH.\n"
        )
    return (
        "No C++ compiler found (g++ or clang++) on PATH.\n\n"
        "Install a compiler, e.g.:\n"
        "  Debian/Ubuntu: sudo apt install g++\n"
        "  macOS: xcode-select --install   (clang++)\n"
        "Then restart the server and try again.\n"
    )


def _clang_candidates() -> list[str]:
    out: list[str] = []
    w = shutil.which("clang++")
    if w:
        out.append(w)
    if platform.system() == "Windows":
        for c in (
            r"C:\Program Files\LLVM\bin\clang++.exe",
            r"C:\Program Files (x86)\LLVM\bin\clang++.exe",
        ):
            if os.path.isfile(c) and c not in out:
                out.append(c)
    return out


def _gpp_candidates() -> list[str]:
    out: list[str] = []
    w = shutil.which("g++")
    if w:
        out.append(w)
    if platform.system() == "Windows":
        for root in (r"C:\msys64", r"C:\msys32"):
            for env in ("ucrt64", "mingw64", "clang64"):
                p = os.path.join(root, env, "bin", "g++.exe")
                if os.path.isfile(p) and p not in out:
                    out.append(p)
    return out


def _subprocess_env(cxx: str) -> dict[str, str]:
    """Windows: g++/clang spawn cc1plus/as from the same tree; PATH must include that bin."""
    env = os.environ.copy()
    if platform.system() == "Windows":
        bin_dir = os.path.dirname(os.path.abspath(cxx))
        if bin_dir:
            env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
    return env


def _pick_compiler() -> str | None:
    for c in _gpp_candidates():
        return c
    for c in _clang_candidates():
        return c
    return None


def _windows_msvc_stl_hint(cxx: str, cerr: str) -> str:
    """LLVM clang++ targets MSVC by default; without VS C++ headers, <iostream> etc. fail."""
    if platform.system() != "Windows":
        return ""
    cxx_l = cxx.replace("\\", "/").lower()
    if "program files/llvm" not in cxx_l:
        return ""
    low = cerr.lower()
    if "file not found" not in low and "no such file" not in low:
        return ""
    if not any(x in low for x in ("iostream", "cstdio", "vector", "string", "stddef", "cstdlib")):
        return ""
    return (
        "\n---\n"
        "This clang++ build targets the MSVC C++ standard library, but no MSVC "
        "toolchain was found. Install one of the following, then try again:\n"
        "  * MSYS2 (https://www.msys2.org/) - run: pacman -S mingw-w64-ucrt-x86_64-gcc "
        "- then add C:\\msys64\\ucrt64\\bin to PATH (RunStudio prefers g++ when found).\n"
        "  * Or Visual Studio / Build Tools with the \"Desktop development with C++\" workload.\n"
    )


def run_cpp(code: str) -> tuple[str, str]:
    cxx = _pick_compiler()
    if not cxx:
        return "", _no_compiler_help()

    exe_name = "prog.exe" if os.name == "nt" else "prog"

    env = _subprocess_env(cxx)

    with tempfile.TemporaryDirectory(prefix="repl_cpp_") as td:
        td_path = Path(td)
        src = td_path / "snippet.cpp"
        src.write_text(code, encoding="utf-8")
        out_exe = td_path / exe_name
        try:
            comp = subprocess.run(
                [cxx, str(src), "-std=c++17", "-O2", "-o", str(out_exe)],
                capture_output=True,
                text=True,
                timeout=COMPILE_TIMEOUT,
                cwd=td,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return "", "C++ compilation timed out.\n"
        except OSError as e:
            return "", f"Compilation error: {e}\n"

        cerr = comp.stderr or ""
        cout = comp.stdout or ""
        if comp.returncode != 0:
            err = cerr or f"Compilation failed (exit {comp.returncode}).\n"
            err += _windows_msvc_stl_hint(cxx, cerr)
            return cout, err

        if not out_exe.is_file():
            return "", cerr + "Executable missing after compilation.\n"

        try:
            run = subprocess.run(
                [str(out_exe)],
                capture_output=True,
                text=True,
                timeout=RUN_TIMEOUT,
                cwd=td,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return "", cerr + "C++ program execution timed out.\n"
        except OSError as e:
            return "", cerr + f"Run error: {e}\n"

        out = (cout or "") + (run.stdout or "")
        err = cerr + (run.stderr or "")
        if run.returncode != 0 and not err.strip():
            err += f"Program exited with code {run.returncode}.\n"
        return out, err
