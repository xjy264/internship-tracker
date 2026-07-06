# internship-tracker 工作规则

- 这是 agent-first 项目：Codex / Claude Code 写入数据只能用 `python3 scripts/internship_cli.py --json ...`。
- 网页是只读展示，不要给网页加手工新增/编辑/删除入口，除非用户明确要求。
- 必填投递字段只有：投递时间、公司、岗位。
- 其它投递渠道、岗位链接、状态、城市、简历版本、面试信息、下一步、备注都是可选字段。
- 修改后先在本地跑测试/构建，提交并推送到远程仓库，再询问用户是否上线。
- 未经用户确认，不要把后续改动部署到 82 服务器。
- 若 82 服务器无法从 GitHub 拉取，确认本地 commit 已推送后，可用 `git archive HEAD` 打包当前提交上传部署。
- 不提交 `.env`、`data/`、SQLite 数据库或真实投递数据。
