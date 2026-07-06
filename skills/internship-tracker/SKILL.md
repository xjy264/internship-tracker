---
name: internship-tracker
description: Drive the internship-tracker project, a Flask and SQLite web app for managing internship applications. Use when Codex needs to add or modify internship application tracking features, update the web dashboard, maintain the SQLite schema, deploy to the 82 server, or follow the project workflow of test, commit, push, then ask before future deployments.
---

# Internship Tracker

Use this skill in the `internship-tracker` repository.

## Project rules

- Keep required application fields limited to `applied_at`, `company`, and `role` unless the user asks to change them.
- Treat `job_url`, `channel`, `status`, `location`, `resume_version`, `has_interview`, `interview_at`, `interview_passed`, `next_action`, `notes`, and `reviewed_at` as optional.
- Do not commit `.env`, `data/`, SQLite databases, or real application records.
- Prefer the existing Flask + SQLite + server-rendered HTML stack; do not add a SPA/build chain unless the user explicitly asks.

## Workflow

1. Modify locally.
2. Run `python3 -m unittest` with project dependencies available.
3. Run `docker compose config` and `docker build -t internship-tracker:local .` for deployment-affecting changes.
4. Commit to `main`.
5. Push to `origin/main`.
6. Ask the user before deploying future changes to the 82 server.

## Runtime

- Local app entrypoint: `app.py`.
- Production database: `data/app.sqlite3` mounted by Docker Compose.
- Production server path: `/home/ubuntu/apps/internship-tracker`.
- Production URL: `http://82.156.194.174:8020`.
- SSH key for deployment: `~/.ssh/id_ed25519_remote_20260630`.

## Reminder rule

Show an application as needing review when:

- `applied_at` is at least 15 days old,
- `reviewed_at` is empty,
- `status` is not `通过`, `拒绝`, or `放弃`.
