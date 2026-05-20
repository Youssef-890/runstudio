"""Dispatch code execution by language (Python sandbox, Node, C++)."""

from __future__ import annotations

MAX_CODE_LENGTH = 64_000

_LANG_ALIASES: dict[str, str] = {
    "python": "python",
    "py": "python",
    "javascript": "javascript",
    "js": "javascript",
    "nodejs": "javascript",
    "node": "javascript",
    "cpp": "cpp",
    "c++": "cpp",
    "cxx": "cpp",
}


def normalize_language(language: object) -> str:
    if language is None:
        return "python"
    if not isinstance(language, str):
        raise TypeError("'language' must be a string.")
    key = language.strip().lower()
    if key not in _LANG_ALIASES:
        raise ValueError("Unsupported language. Use: python, javascript, cpp.")
    return _LANG_ALIASES[key]


def execute_payload(code: object, language: object = "python") -> tuple[str, str]:
    if not isinstance(code, str):
        raise TypeError("Code must be a string.")
    if len(code) > MAX_CODE_LENGTH:
        raise ValueError(f"Code exceeds maximum length ({MAX_CODE_LENGTH} characters).")
    lang = normalize_language(language)

    if lang == "python":
        from services.sandbox import run_restricted

        return run_restricted(code)
    if lang == "javascript":
        from services.nodejs_runner import run_javascript

        return run_javascript(code)
    if lang == "cpp":
        from services.cpp_runner import run_cpp

        return run_cpp(code)
    raise ValueError("Unknown internal language.")
