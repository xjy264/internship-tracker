import csv
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "tracker.py"


class TrackerCliTest(unittest.TestCase):
    def run_cli(self, csv_path, *args):
        self.assertTrue(SCRIPT.exists(), f"missing tracker script: {SCRIPT}")
        env = os.environ.copy()
        env["INTERNSHIP_TRACKER_CSV"] = str(csv_path)
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            env=env,
            check=True,
        )

    def read_rows(self, csv_path):
        with csv_path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_add_update_remind_and_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "applications.csv"

            self.run_cli(csv_path, "add", "--applied-at", "2026-07-06", "--company", "字节", "--role", "前端实习")
            rows = self.read_rows(csv_path)
            self.assertEqual(rows[0]["id"], "1")
            self.assertEqual(rows[0]["company"], "字节")
            self.assertEqual(rows[0]["role"], "前端实习")

            self.run_cli(csv_path, "update", "--id", "1", "--has-interview", "yes", "--interview-passed", "unknown")
            rows = self.read_rows(csv_path)
            self.assertEqual(rows[0]["has_interview"], "yes")
            self.assertEqual(rows[0]["interview_passed"], "unknown")

            old_day = (date.today() - timedelta(days=16)).isoformat()
            self.run_cli(csv_path, "add", "--applied-at", old_day, "--company", "老公司", "--role", "后端实习")
            reminders = self.run_cli(csv_path, "reminders").stdout
            self.assertIn("老公司", reminders)

            self.run_cli(csv_path, "review", "--id", "2")
            reminders = self.run_cli(csv_path, "reminders").stdout
            self.assertNotIn("老公司", reminders)


if __name__ == "__main__":
    unittest.main()
