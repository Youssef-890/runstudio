"""Authentication: register, login, logout."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from models.user import authenticate, create_user, get_user_by_username
from utils.helpers import safe_next_url

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = authenticate(username, password)
        if user is not None:
            login_user(user)
            return redirect(safe_next_url(request.args.get("next")))
        flash("Identifiant ou mot de passe incorrect.", "error")
    return render_template("login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        if not username or len(username) < 2:
            flash("Username must be at least 2 characters.", "error")
            return render_template("register.html")
        if len(password) < 4:
            flash("Password must be at least 4 characters.", "error")
            return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")
        if get_user_by_username(username) is not None:
            flash("That username is already taken.", "error")
            return render_template("register.html")
        create_user(username, password)
        user = authenticate(username, password)
        if user is not None:
            login_user(user)
            return redirect(url_for("index"))
        flash("Could not create the account.", "error")
    return render_template("register.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
