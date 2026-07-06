#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracker_core import (  # noqa: E402
    APPLICATION_FIELDS,
    STATUSES,
    add_application,
    add_task,
    clear_tasks,
    complete_task,
    connect,
    delete_application,
    list_applications,
    list_tasks,
    review_application,
    update_application,
)


def db_path():
    return os.environ.get("DATABASE", str(ROOT / "data" / "app.sqlite3"))


def output(args, payload, human):
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(human)


def application_data(args):
    return {field: getattr(args, field) for field in APPLICATION_FIELDS if hasattr(args, field) and getattr(args, field) is not None}


def cmd_app_add(args):
    with connect(db_path()) as db:
        app = add_application(db, application_data(args))
    output(args, {"application": app}, f"added application #{app['id']}")


def cmd_app_list(args):
    with connect(db_path()) as db:
        rows = list_applications(db, q=args.q, status=args.status, due_only=args.due)
    output(args, {"applications": rows}, f"{len(rows)} application(s)")


def cmd_app_update(args):
    with connect(db_path()) as db:
        app = update_application(db, args.id, application_data(args))
    output(args, {"application": app}, f"updated application #{app['id']}")


def cmd_app_review(args):
    with connect(db_path()) as db:
        app = review_application(db, args.id)
    output(args, {"application": app}, f"reviewed application #{app['id']}")


def cmd_app_delete(args):
    with connect(db_path()) as db:
        deleted = delete_application(db, args.id)
    output(args, {"deleted": deleted}, f"deleted {deleted} application(s)")


def cmd_tasks_clear(args):
    with connect(db_path()) as db:
        deleted = clear_tasks(db)
    output(args, {"deleted": deleted}, f"deleted {deleted} task(s)")


def cmd_tasks_add(args):
    with connect(db_path()) as db:
        task = add_task(db, args.title)
    output(args, {"task": task}, f"added task #{task['id']}")


def cmd_tasks_list(args):
    with connect(db_path()) as db:
        tasks = list_tasks(db, include_completed=args.all)
    output(args, {"tasks": tasks}, f"{len(tasks)} task(s)")


def cmd_tasks_complete(args):
    with connect(db_path()) as db:
        task = complete_task(db, args.id)
    output(args, {"task": task}, f"completed task #{task['id']}")


def add_application_args(parser, required=False):
    parser.add_argument("--applied-at", dest="applied_at", required=required)
    parser.add_argument("--company", required=required)
    parser.add_argument("--role", required=required)
    parser.add_argument("--job-url", dest="job_url")
    parser.add_argument("--channel")
    parser.add_argument("--status", choices=STATUSES)
    parser.add_argument("--location")
    parser.add_argument("--resume-version", dest="resume_version")
    parser.add_argument("--has-interview", dest="has_interview", choices=["unknown", "yes", "no"])
    parser.add_argument("--interview-at", dest="interview_at")
    parser.add_argument("--interview-passed", dest="interview_passed", choices=["unknown", "yes", "no"])
    parser.add_argument("--next-action", dest="next_action")
    parser.add_argument("--notes")


def build_parser():
    parser = argparse.ArgumentParser(description="Agent-first internship tracker CLI")
    parser.add_argument("--json", action="store_true", help="emit JSON for Codex/Claude Code")
    sub = parser.add_subparsers(dest="resource", required=True)

    apps = sub.add_parser("applications")
    app_sub = apps.add_subparsers(dest="action", required=True)
    add = app_sub.add_parser("add")
    add_application_args(add, required=True)
    add.set_defaults(func=cmd_app_add)

    list_p = app_sub.add_parser("list")
    list_p.add_argument("--status", default="")
    list_p.add_argument("--q", default="")
    list_p.add_argument("--due", action="store_true")
    list_p.set_defaults(func=cmd_app_list)

    update = app_sub.add_parser("update")
    update.add_argument("--id", type=int, required=True)
    add_application_args(update)
    update.set_defaults(func=cmd_app_update)

    review = app_sub.add_parser("review")
    review.add_argument("--id", type=int, required=True)
    review.set_defaults(func=cmd_app_review)

    delete = app_sub.add_parser("delete")
    delete.add_argument("--id", type=int, required=True)
    delete.set_defaults(func=cmd_app_delete)

    tasks = sub.add_parser("tasks")
    task_sub = tasks.add_subparsers(dest="action", required=True)
    task_sub.add_parser("clear").set_defaults(func=cmd_tasks_clear)
    task_add = task_sub.add_parser("add")
    task_add.add_argument("--title", required=True)
    task_add.set_defaults(func=cmd_tasks_add)
    task_list = task_sub.add_parser("list")
    task_list.add_argument("--all", action="store_true")
    task_list.set_defaults(func=cmd_tasks_list)
    task_done = task_sub.add_parser("complete")
    task_done.add_argument("--id", type=int, required=True)
    task_done.set_defaults(func=cmd_tasks_complete)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
