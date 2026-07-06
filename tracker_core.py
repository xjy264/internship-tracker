import sqlite3
from datetime import date, timedelta

STATUSES = ["已投递", "待跟进", "面试中", "通过", "拒绝", "放弃"]
TRUTHY = ["unknown", "yes", "no"]
REVIEW_DONE_STATUSES = {"通过", "拒绝", "放弃"}
APPLICATION_FIELDS = [
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
DEFAULTS = {
    "job_url": "",
    "channel": "",
    "status": "已投递",
    "location": "",
    "resume_version": "",
    "has_interview": "unknown",
    "interview_at": "",
    "interview_passed": "unknown",
    "next_action": "",
    "notes": "",
}


def init_db(db):
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
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed_at TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()


def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    init_db(db)
    return db


def normalize_application(data, existing=None):
    existing = existing or {}
    row = {}
    for field in APPLICATION_FIELDS:
        value = data.get(field, existing.get(field, DEFAULTS.get(field, "")))
        row[field] = "" if value is None else str(value).strip()
    row["status"] = row["status"] if row["status"] in STATUSES else "已投递"
    row["has_interview"] = row["has_interview"] if row["has_interview"] in TRUTHY else "unknown"
    row["interview_passed"] = row["interview_passed"] if row["interview_passed"] in TRUTHY else "unknown"
    validate_application(row)
    return row


def validate_application(row):
    for field in ("applied_at", "company", "role"):
        if not row.get(field):
            raise ValueError(f"{field} is required")
    try:
        date.fromisoformat(row["applied_at"])
    except ValueError as exc:
        raise ValueError("applied_at must be YYYY-MM-DD") from exc


def row_to_dict(row):
    if row is None:
        return None
    item = dict(row)
    item["is_due"] = is_due(item)
    return item


def is_due(row):
    try:
        applied = date.fromisoformat(row["applied_at"])
    except ValueError:
        return False
    return applied <= date.today() - timedelta(days=15) and not row.get("reviewed_at") and row.get("status") not in REVIEW_DONE_STATUSES


def get_application(db, app_id):
    return row_to_dict(db.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone())


def add_application(db, data):
    row = normalize_application(data)
    cur = db.execute(
        """
        INSERT INTO applications (
            applied_at, company, role, job_url, channel, status, location, resume_version,
            has_interview, interview_at, interview_passed, next_action, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [row[field] for field in APPLICATION_FIELDS],
    )
    db.commit()
    return get_application(db, cur.lastrowid)


def update_application(db, app_id, data):
    current = get_application(db, app_id)
    if current is None:
        raise KeyError(app_id)
    row = normalize_application(data, current)
    db.execute(
        """
        UPDATE applications SET
            applied_at=?, company=?, role=?, job_url=?, channel=?, status=?, location=?, resume_version=?,
            has_interview=?, interview_at=?, interview_passed=?, next_action=?, notes=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        """,
        [row[field] for field in APPLICATION_FIELDS] + [app_id],
    )
    db.commit()
    return get_application(db, app_id)


def review_application(db, app_id):
    if get_application(db, app_id) is None:
        raise KeyError(app_id)
    db.execute("UPDATE applications SET reviewed_at=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (date.today().isoformat(), app_id))
    db.commit()
    return get_application(db, app_id)


def delete_application(db, app_id):
    cur = db.execute("DELETE FROM applications WHERE id=?", (app_id,))
    db.commit()
    return cur.rowcount


def list_applications(db, q="", status="", due_only=False):
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
    rows = [row_to_dict(row) for row in db.execute(sql, params).fetchall()]
    return [row for row in rows if row["is_due"]] if due_only else rows


def stats(db):
    rows = list_applications(db)
    return {
        "total": len(rows),
        "due": sum(1 for row in rows if row["is_due"]),
        "interviewing": sum(1 for row in rows if row["status"] == "面试中"),
        "passed": sum(1 for row in rows if row["status"] == "通过"),
    }


def task_to_dict(row):
    return dict(row) if row else None


def add_task(db, title):
    title = title.strip()
    if not title:
        raise ValueError("title is required")
    cur = db.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
    db.commit()
    return task_to_dict(db.execute("SELECT * FROM tasks WHERE id=?", (cur.lastrowid,)).fetchone())


def list_tasks(db, include_completed=False):
    where = "" if include_completed else "WHERE completed_at = ''"
    return [task_to_dict(row) for row in db.execute(f"SELECT * FROM tasks {where} ORDER BY id").fetchall()]


def clear_tasks(db):
    cur = db.execute("DELETE FROM tasks")
    db.commit()
    return cur.rowcount


def complete_task(db, task_id):
    db.execute("UPDATE tasks SET completed_at=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (date.today().isoformat(), task_id))
    db.commit()
    task = task_to_dict(db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())
    if task is None:
        raise KeyError(task_id)
    return task
