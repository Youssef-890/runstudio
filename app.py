"""Flask application: multi-language REPL, auth, per-user script storage."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, render_template
from flask_login import LoginManager

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id: str):
    from models.user import get_user_by_id

    return get_user_by_id(int(user_id))


def create_app(test_config: dict | None = None) -> Flask:
    root = Path(__file__).resolve().parent
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        DATABASE=str(root / "database" / "app.db"),
    )
    if test_config:
        app.config.update(test_config)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from utils.helpers import close_db, init_db

    app.teardown_appcontext(close_db)
    init_db(app)

    from routes.auth import bp as auth_bp
    from routes.execute import bp as execute_bp
    from routes.scripts import bp as scripts_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(execute_bp)
    app.register_blueprint(scripts_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    create_app().run(debug=debug, host="127.0.0.1", port=5000)
