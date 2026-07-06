# 实习投递记录器

一个自用的实习投递管理小项目：单密码登录、SQLite 存储、表格看板、15 天复看提醒。

## 本地运行

```bash
python3 -m pip install -r requirements.txt
APP_PASSWORD=dev SECRET_KEY=dev python3 app.py
```

访问 `http://127.0.0.1:8020`。

## Docker

```bash
cp .env.example .env
# 修改 .env 中的 APP_PASSWORD 和 SECRET_KEY
docker compose up -d --build
```

## 后续修改标准

1. 本地修改代码。
2. 运行 `python3 -m unittest`、`docker compose config`、`docker build -t internship-tracker:local .`。
3. commit 到 `main`。
4. push 到 GitHub `main`。
5. 询问是否上线。
6. 确认后到 82 服务器拉取并 `docker compose up -d --build`。
   - 如果 82 服务器无法访问 GitHub，就在确认代码已 push 后用 `git archive HEAD | ssh ... tar -x` 上传当前提交再部署。

## 数据

生产数据在服务器 `data/app.sqlite3`，不提交到 Git。
