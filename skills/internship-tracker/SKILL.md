---
name: internship-tracker
description: Track internship applications in a local CSV repository. Use when Codex needs to add internship applications, update interview status, list applications, check applications that need a 15-day follow-up review, or mark an internship application as reviewed.
---

# Internship Tracker

Use this skill in the repository root that contains `applications.csv` and `scripts/tracker.py`.

## Rules

- Required fields for a new application: `applied_at`, `company`, `role`.
- Keep optional fields out of v1 unless the user asks to extend the schema.
- Represent booleans as `yes`, `no`, or `unknown` where supported.
- Use the CLI instead of editing `applications.csv` by hand.

## Commands

Add an application:

```bash
python3 scripts/tracker.py add --applied-at YYYY-MM-DD --company 公司 --role 岗位
```

Update interview status:

```bash
python3 scripts/tracker.py update --id ID --has-interview yes --interview-passed unknown
python3 scripts/tracker.py update --id ID --has-interview yes --interview-passed yes
python3 scripts/tracker.py update --id ID --has-interview no
```

List all applications:

```bash
python3 scripts/tracker.py list
```

Show applications that were submitted at least 15 days ago, have not been reviewed, and still have unknown interview result:

```bash
python3 scripts/tracker.py reminders
```

Mark a reminder as reviewed:

```bash
python3 scripts/tracker.py review --id ID
```

## Natural language mapping

- “记录/新增/我投了公司岗位” -> `add`.
- “有面试/没面试/面试通过/面试没过” -> `update`.
- “看看投递情况” -> `list`.
- “哪些该复看/提醒我复看” -> `reminders`.
- “这个岗位我复看过了” -> `review`.
