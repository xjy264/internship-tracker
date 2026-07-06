import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "internship_cli.py"


class AgentCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "agent.sqlite3"

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        env = os.environ.copy()
        env["DATABASE"] = str(self.db_path)
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--json", *args],
            text=True,
            capture_output=True,
            env=env,
            check=True,
        )
        return json.loads(result.stdout)

    def test_applications_json_crud_and_due_review(self):
        created = self.run_cli("applications", "add", "--applied-at", "2026-07-06", "--company", "字节", "--role", "前端实习")
        self.assertEqual(created["application"]["id"], 1)
        self.assertEqual(created["application"]["company"], "字节")

        listed = self.run_cli("applications", "list")
        self.assertEqual(len(listed["applications"]), 1)

        updated = self.run_cli("applications", "update", "--id", "1", "--status", "面试中", "--has-interview", "yes")
        self.assertEqual(updated["application"]["status"], "面试中")
        self.assertEqual(updated["application"]["has_interview"], "yes")

        old_day = (date.today() - timedelta(days=16)).isoformat()
        old = self.run_cli("applications", "add", "--applied-at", old_day, "--company", "老公司", "--role", "后端实习")
        due = self.run_cli("applications", "list", "--due")
        self.assertEqual([row["id"] for row in due["applications"]], [old["application"]["id"]])

        self.run_cli("applications", "review", "--id", str(old["application"]["id"]))
        due = self.run_cli("applications", "list", "--due")
        self.assertEqual(due["applications"], [])

    def test_tasks_clear_add_list_complete(self):
        self.run_cli("tasks", "add", "--title", "旧任务")
        cleared = self.run_cli("tasks", "clear")
        self.assertEqual(cleared["deleted"], 1)

        added = self.run_cli("tasks", "add", "--title", "务必开始投递")
        tasks = self.run_cli("tasks", "list")
        self.assertEqual(tasks["tasks"], [added["task"]])
        self.assertEqual(tasks["tasks"][0]["title"], "务必开始投递")
        self.assertEqual(tasks["tasks"][0]["completed_at"], "")

        done = self.run_cli("tasks", "complete", "--id", str(added["task"]["id"]))
        self.assertNotEqual(done["task"]["completed_at"], "")


if __name__ == "__main__":
    unittest.main()
