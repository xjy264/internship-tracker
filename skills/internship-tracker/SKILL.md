---
name: internship-tracker
description: Drive the internship-tracker project, an agent-first Flask and SQLite internship application tracker. Use when Codex or Claude Code needs to write internship applications through the repository CLI, maintain the read-only web dashboard, manage the application memo, update the SQLite schema, or follow the test, commit, push, then ask-before-deploy workflow.
---

# Internship Tracker

Use this skill in the `internship-tracker` repository.

## Agent-first rule

- Write data only through `python3 scripts/internship_cli.py --json ...`.
- Do not edit SQLite directly.
- Do not re-add manual write forms to the web UI unless the user explicitly asks.
- Prefer `--json` for every Codex/Claude Code operation.

## Common commands

Add an application:

```bash
python3 scripts/internship_cli.py --json applications add --applied-at YYYY-MM-DD --company 公司 --role 岗位
```

Update an application:

```bash
python3 scripts/internship_cli.py --json applications update --id ID --status 面试中 --has-interview yes --interview-passed unknown
```

List applications:

```bash
python3 scripts/internship_cli.py --json applications list
python3 scripts/internship_cli.py --json applications list --due
```

Review or delete:

```bash
python3 scripts/internship_cli.py --json applications review --id ID
python3 scripts/internship_cli.py --json applications delete --id ID
```

Maintain the application memo. Use each task title as a company or target the user still wants to apply to:

```bash
python3 scripts/internship_cli.py --json tasks clear
python3 scripts/internship_cli.py --json tasks add --title "美团"
python3 scripts/internship_cli.py --json tasks list
```

## Project rules

- Required application fields: `applied_at`, `company`, `role`.
- Optional fields: `job_url`, `channel`, `status`, `location`, `resume_version`, `has_interview`, `interview_at`, `interview_passed`, `next_action`, `notes`, `reviewed_at`.
- Keep production data in `data/app.sqlite3`; do not commit it.

## Workflow

1. Modify locally.
2. Run tests and Docker checks.
3. Commit to `main`.
4. Push to `origin/main`.
5. Ask before deploying future changes to the 82 server.
