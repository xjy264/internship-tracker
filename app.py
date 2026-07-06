import os
import secrets
from functools import wraps
from pathlib import Path

from flask import Flask, abort, current_app, g, redirect, render_template, request, session, url_for

from tracker_core import STATUSES, connect, init_db as core_init_db, list_applications, list_tasks, stats


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", secrets.token_hex(24)),
        APP_PASSWORD=os.environ.get("APP_PASSWORD", ""),
        DATABASE=os.environ.get("DATABASE", str(Path(__file__).resolve().parent / "data" / "app.sqlite3")),
    )
    if config:
        app.config.update(config)

    @app.before_request
    def _ensure_db():
        init_db()

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            expected = app.config["APP_PASSWORD"]
            if expected and request.form.get("password") == expected:
                session["ok"] = True
                return redirect(url_for("index"))
            abort(401)
        return render_template("login.html")

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def index():
        q = request.args.get("q", "").strip()
        status = request.args.get("status", "").strip()
        due_only = request.args.get("due") == "1"
        db = get_db()
        return render_template(
            "index.html",
            rows=list_applications(db, q=q, status=status, due_only=due_only),
            tasks=list_tasks(db),
            stats=stats(db),
            statuses=STATUSES,
            q=q,
            selected_status=status,
            due_only=due_only,
        )

    return app


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("ok"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def get_db():
    if "db" not in g:
        path = Path(current_app.config["DATABASE"])
        path.parent.mkdir(parents=True, exist_ok=True)
        g.db = connect(path)
    return g.db


def init_db():
    core_init_db(get_db())


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8020")))
