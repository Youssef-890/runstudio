"""JSON API for the signed-in user's scripts only (scoped by user_id)."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from services import storage_service
from services.executor import normalize_language

bp = Blueprint("scripts", __name__, url_prefix="/api/scripts")


@bp.get("")
@login_required
def list_scripts():
    items = storage_service.list_scripts_for_user(current_user.id)
    return jsonify({"scripts": items})


@bp.get("/<int:script_id>")
@login_required
def get_script(script_id: int):
    row = storage_service.get_script(current_user.id, script_id)
    if row is None:
        return jsonify({"error": "Script not found."}), 404
    return jsonify(row)


@bp.post("")
@login_required
def create_script():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "Untitled")
    code = data.get("code", "")
    language = data.get("language", "python")
    if not isinstance(title, str):
        return jsonify({"error": "title must be a string."}), 400
    if not isinstance(code, str):
        return jsonify({"error": "code must be a string."}), 400
    if not isinstance(language, str):
        return jsonify({"error": "language must be a string."}), 400
    try:
        lang_norm = normalize_language(language)
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    sid = storage_service.save_script(current_user.id, title, code, lang_norm)
    return (
        jsonify({"id": sid, "title": title.strip() or "Untitled", "language": lang_norm}),
        201,
    )


@bp.route("/<int:script_id>", methods=["PUT"])
@login_required
def put_script(script_id: int):
    data = request.get_json(silent=True) or {}
    title = data.get("title") if "title" in data else None
    code = data.get("code") if "code" in data else None
    language = data.get("language") if "language" in data else None
    if title is not None and not isinstance(title, str):
        return jsonify({"error": "title must be a string."}), 400
    if code is not None and not isinstance(code, str):
        return jsonify({"error": "code must be a string."}), 400
    if language is not None and not isinstance(language, str):
        return jsonify({"error": "language must be a string."}), 400
    try:
        ok = storage_service.update_script(
            current_user.id, script_id, title, code, language
        )
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    if not ok:
        return jsonify({"error": "Script not found."}), 404
    return jsonify({"ok": True})


@bp.route("/<int:script_id>", methods=["DELETE"])
@login_required
def delete_script_route(script_id: int):
    if not storage_service.delete_script(current_user.id, script_id):
        return jsonify({"error": "Script not found."}), 404
    return jsonify({"ok": True})
