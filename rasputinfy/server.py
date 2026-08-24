"""Flask application serving the now-playing UI and API."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from rasputinfy.mpris import merge_with_mpris
from rasputinfy.state import DEFAULT_STATE_PATH, read_state

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def create_app(
    *,
    demo: bool = False,
    use_mpris: bool = True,
    state_path: Path | None = None,
) -> Flask:
    resolved_state_path = state_path or DEFAULT_STATE_PATH
    app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")
    app.config["RASPUTINFY_DEMO"] = demo
    app.config["RASPUTINFY_USE_MPRIS"] = use_mpris
    app.config["RASPUTINFY_STATE_PATH"] = resolved_state_path

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/api/now-playing")
    def now_playing():
        state = read_state(app.config["RASPUTINFY_STATE_PATH"])
        if app.config["RASPUTINFY_USE_MPRIS"] and not app.config["RASPUTINFY_DEMO"]:
            state = merge_with_mpris(state)
        return jsonify(state.to_dict())

    return app
