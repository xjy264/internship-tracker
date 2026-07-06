#!/usr/bin/env python3
import argparse
import csv
import os
import sys
from datetime import date, timedelta
from pathlib import Path

FIELDS = ["id", "applied_at", "company", "role", "has_interview", "interview_passed", "reviewed_at"]
DATA_FILE = Path(os.environ.get("INTERNSHIP_TRACKER_CSV", Path(__file__).resolve().parents[1] / "applications.csv"))


def die(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def parse_date(value):
    try:
        return date.fromisoformat(value)
    except ValueError:
        die(f"invalid date: {value}; use YYYY-MM-DD")


def ensure_file(path=DATA_FILE):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        write_rows([], path)


def read_rows(path=DATA_FILE):
    ensure_file(path)
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_rows(rows, path=DATA_FILE):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in FIELDS} for row in rows])


def next_id(rows):
    ids = [int(row["id"]) for row in rows if row.get("id", "").isdigit()]
    return str(max(ids, default=0) + 1)


def print_rows(rows):
    if not rows:
        print("No records.")
        return
    print("\t".join(FIELDS))
    for row in rows:
        print("\t".join(row.get(field, "") for field in FIELDS))


def find_row(rows, row_id):
    for row in rows:
        if row.get("id") == row_id:
            return row
    die(f"id not found: {row_id}")


def cmd_add(args):
    parse_date(args.applied_at)
    rows = read_rows()
    row = {
        "id": next_id(rows),
        "applied_at": args.applied_at,
        "company": args.company.strip(),
        "role": args.role.strip(),
        "has_interview": "",
        "interview_passed": "unknown",
        "reviewed_at": "",
    }
    if not row["company"] or not row["role"]:
        die("company and role are required")
    rows.append(row)
    write_rows(rows)
    print(f"Added #{row['id']}: {row['company']} - {row['role']}")


def cmd_update(args):
    rows = read_rows()
    row = find_row(rows, args.id)
    if args.has_interview is not None:
        row["has_interview"] = args.has_interview
    if args.interview_passed is not None:
        row["interview_passed"] = args.interview_passed
    write_rows(rows)
    print(f"Updated #{args.id}")


def cmd_list(_args):
    print_rows(read_rows())


def reminder_rows(rows, today=None):
    today = today or date.today()
    cutoff = today - timedelta(days=15)
    due = []
    for row in rows:
        applied_at = parse_date(row.get("applied_at", ""))
        if applied_at <= cutoff and not row.get("reviewed_at") and row.get("interview_passed", "unknown") in ("", "unknown"):
            due.append(row)
    return due


def cmd_reminders(_args):
    print_rows(reminder_rows(read_rows()))


def cmd_review(args):
    rows = read_rows()
    row = find_row(rows, args.id)
    row["reviewed_at"] = date.today().isoformat()
    write_rows(rows)
    print(f"Reviewed #{args.id}")


def build_parser():
    parser = argparse.ArgumentParser(description="Track internship applications in applications.csv")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add an application")
    add.add_argument("--applied-at", required=True)
    add.add_argument("--company", required=True)
    add.add_argument("--role", required=True)
    add.set_defaults(func=cmd_add)

    update = sub.add_parser("update", help="update interview fields")
    update.add_argument("--id", required=True)
    update.add_argument("--has-interview", choices=["yes", "no"])
    update.add_argument("--interview-passed", choices=["yes", "no", "unknown"])
    update.set_defaults(func=cmd_update)

    sub.add_parser("list", help="list all applications").set_defaults(func=cmd_list)
    sub.add_parser("reminders", help="show applications needing 15-day review").set_defaults(func=cmd_reminders)

    review = sub.add_parser("review", help="mark an application as reviewed")
    review.add_argument("--id", required=True)
    review.set_defaults(func=cmd_review)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
