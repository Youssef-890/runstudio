"""POST /execute — run user code, return stdout/stderr JSON."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.executor import execute_payload, normalize_language

bp = Blueprint("execute", __name__)


@bp.post("/execute")
def execute():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code")
    language = payload.get("language", "python")
    lang_norm = "python"
    try:
        lang_norm = normalize_language(language)
        stdout, stderr = execute_payload(code, lang_norm)
    except TypeError as e:
        return jsonify({"error": str(e), "stdout": "", "stderr": ""}), 400
    except ValueError as e:
        return jsonify({"error": str(e), "stdout": "", "stderr": ""}), 400
    return jsonify({"stdout": stdout, "stderr": stderr, "language": lang_norm})
