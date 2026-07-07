# 实习投递记录器

Agent-first 的实习投递管理小项目：Codex / Claude Code 通过 CLI 写入 SQLite，网页只读展示投递表格和投递备忘录。

## Agent CLI

所有写入都走：

```bash
python3 scripts/internship_cli.py --json applications add --applied-at 2026-07-06 --company 字节 --role 前端实习
python3 scripts/internship_cli.py --json applications list --due
python3 scripts/internship_cli.py --json applications update --id 1 --status 面试中 --has-interview yes
python3 scripts/internship_cli.py --json applications review --id 1
python3 scripts/internship_cli.py --json tasks clear
python3 scripts/internship_cli.py --json tasks add --title "美团"
python3 scripts/internship_cli.py --json tasks list
```

默认数据库是 `data/app.sqlite3`。测试或一次性操作可用 `DATABASE=/path/to/app.sqlite3` 指定。

## 网页

```bash
python3 -m pip install -r requirements.txt
APP_PASSWORD=dev SECRET_KEY=dev python3 app.py
```

访问 `http://127.0.0.1:8020`。网页只展示，不提供新增/编辑/删除入口。

## Docker

```bash
cp .env.example .env
# 修改 .env 中的 APP_PASSWORD 和 SECRET_KEY
docker compose up -d --build
```

## 后续修改标准

1. 本地修改代码。
2. 运行 `python3 -m unittest discover -s tests -v`、`docker compose config`、`docker build -t internship-tracker:local .`。
3. commit 到 `main`。
4. push 到 GitHub `main`。
5. 询问是否上线。
6. 确认后到 82 服务器部署；如果 82 服务器无法访问 GitHub，就在确认代码已 push 后用 `git archive HEAD | ssh ... tar -x` 上传当前提交再部署。

## 数据

生产数据在服务器 `data/app.sqlite3`，不提交到 Git。
