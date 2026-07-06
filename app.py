import os
import secrets
import sqlite3
from datetime import date, timedelta
from functools import wraps
from pathlib import Path

from flask import Flask, abort, current_app, flash, g, redirect, render_template, request, session, url_for

STATUSES = ["已投递", "待跟进", "面试中", "通过", "拒绝", "放弃"]
TRUTHY = ["unknown", "yes", "no"]
REVIEW_DONE_STATUSES = {"通过", "拒绝", "放弃"}
FIELDS = [
    "applied_at",
    "company",
    "role",
    "job_url",
    "channel",
    "status",
    "location",
    "resume_version",
    "has_interview",
    "interview_at",
    "interview_passed",
    "next_action",
    "notes",
]


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
        rows = list_applications(q=q, status=status, due_only=due_only)
        return render_template(
            "index.html",
            rows=rows,
            stats=stats(),
            statuses=STATUSES,
            q=q,
            selected_status=status,
            due_only=due_only,
        )

    @app.post("/applications")
    @login_required
    def add_application():
        data = form_data()
        validate_required(data)
        db = get_db()
        db.execute(
            """
            INSERT INTO applications (
                applied_at, company, role, job_url, channel, status, location, resume_version,
                has_interview, interview_at, interview_passed, next_action, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [data[field] for field in FIELDS],
        )
        db.commit()
        flash("已新增投递")
        return redirect(url_for("index"))

    @app.post("/applications/<int:app_id>/update")
    @login_required
    def update_application(app_id):
        row = get_application(app_id)
        if row is None:
            abort(404)
        data = {field: request.form.get(field, row[field] if field in row.keys() else "").strip() for field in FIELDS}
        validate_required(data)
        get_db().execute(
            """
            UPDATE applications SET
                applied_at=?, company=?, role=?, job_url=?, channel=?, status=?, location=?, resume_version=?,
                has_interview=?, interview_at=?, interview_passed=?, next_action=?, notes=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            [data[field] for field in FIELDS] + [app_id],
        )
        get_db().commit()
        flash("已更新投递")
        return redirect(url_for("index"))

    @app.post("/applications/<int:app_id>/review")
    @login_required
    def review_application(app_id):
        if get_application(app_id) is None:
            abort(404)
        get_db().execute("UPDATE applications SET reviewed_at=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (date.today().isoformat(), app_id))
        get_db().commit()
        flash("已标记复看")
        return redirect(url_for("index"))

    @app.post("/applications/<int:app_id>/delete")
    @login_required
    def delete_application(app_id):
        get_db().execute("DELETE FROM applications WHERE id=?", (app_id,))
        get_db().commit()
        flash("已删除投递")
        return redirect(url_for("index"))

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
        g.db = sqlite3.connect(path)
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            applied_at TEXT NOT NULL,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            job_url TEXT NOT NULL DEFAULT '',
            channel TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT '已投递',
            location TEXT NOT NULL DEFAULT '',
            resume_version TEXT NOT NULL DEFAULT '',
            has_interview TEXT NOT NULL DEFAULT 'unknown',
            interview_at TEXT NOT NULL DEFAULT '',
            interview_passed TEXT NOT NULL DEFAULT 'unknown',
            next_action TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            reviewed_at TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()


def form_data():
    data = {field: request.form.get(field, "").strip() for field in FIELDS}
    data["status"] = data["status"] if data["status"] in STATUSES else "已投递"
    data["has_interview"] = data["has_interview"] if data["has_interview"] in TRUTHY else "unknown"
    data["interview_passed"] = data["interview_passed"] if data["interview_passed"] in TRUTHY else "unknown"
    return data


def validate_required(data):
    for field in ("applied_at", "company", "role"):
        if not data.get(field):
            abort(400)
    try:
        date.fromisoformat(data["applied_at"])
    except ValueError:
        abort(400)


def get_application(app_id):
    return get_db().execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()


def is_due(row):
    try:
        applied = date.fromisoformat(row["applied_at"])
    except ValueError:
        return False
    return applied <= date.today() - timedelta(days=15) and not row["reviewed_at"] and row["status"] not in REVIEW_DONE_STATUSES


def row_dict(row):
    item = dict(row)
    item["is_due"] = is_due(row)
    return item


def list_applications(q="", status="", due_only=False):
    sql = "SELECT * FROM applications"
    params = []
    clauses = []
    if q:
        clauses.append("(company LIKE ? OR role LIKE ? OR notes LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like])
    if status:
        clauses.append("status = ?")
        params.append(status)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY applied_at DESC, id DESC"
    rows = [row_dict(row) for row in get_db().execute(sql, params).fetchall()]
    return [row for row in rows if row["is_due"]] if due_only else rows


def stats():
    rows = [row_dict(row) for row in get_db().execute("SELECT * FROM applications").fetchall()]
    return {
        "total": len(rows),
        "due": sum(1 for row in rows if row["is_due"]),
        "interviewing": sum(1 for row in rows if row["status"] == "面试中"),
        "passed": sum(1 for row in rows if row["status"] == "通过"),
    }


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8020")))
