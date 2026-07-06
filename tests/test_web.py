import os
import tempfile
import unittest
from datetime import date, timedelta

from app import create_app, init_db


class WebAppTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "APP_PASSWORD": "secret",
            "SECRET_KEY": "test-secret",
        })
        with self.app.app_context():
            init_db()
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def login(self, password="secret"):
        return self.client.post("/login", data={"password": password}, follow_redirects=True)

    def test_login_requires_single_password(self):
        bad = self.client.post("/login", data={"password": "wrong"})
        self.assertEqual(bad.status_code, 401)

        good = self.login()
        self.assertEqual(good.status_code, 200)
        self.assertIn("实习投递看板".encode(), good.data)


    def test_empty_app_password_does_not_allow_login(self):
        app = create_app({
            "TESTING": True,
            "DATABASE": os.path.join(self.tmp.name, "empty-password.sqlite3"),
            "APP_PASSWORD": "",
            "SECRET_KEY": "test-secret",
        })
        client = app.test_client()
        response = client.post("/login", data={"password": ""})
        self.assertEqual(response.status_code, 401)

    def test_application_crud_and_required_fields(self):
        self.login()
        missing = self.client.post("/applications", data={"applied_at": "2026-07-06", "company": "", "role": "前端实习"})
        self.assertEqual(missing.status_code, 400)

        created = self.client.post("/applications", data={
            "applied_at": "2026-07-06",
            "company": "字节",
            "role": "前端实习",
            "status": "已投递",
            "job_url": "",
            "channel": "",
            "location": "",
            "resume_version": "",
            "has_interview": "unknown",
            "interview_at": "",
            "interview_passed": "unknown",
            "next_action": "",
            "notes": "",
        }, follow_redirects=True)
        self.assertIn("字节".encode(), created.data)

        updated = self.client.post("/applications/1/update", data={
            "applied_at": "2026-07-06",
            "company": "字节跳动",
            "role": "前端实习",
            "status": "面试中",
            "has_interview": "yes",
            "interview_passed": "unknown",
        }, follow_redirects=True)
        self.assertIn("字节跳动".encode(), updated.data)
        self.assertIn("面试中".encode(), updated.data)

        deleted = self.client.post("/applications/1/delete", follow_redirects=True)
        self.assertNotIn("字节跳动".encode(), deleted.data)

    def test_15_day_review_reminder_and_review_action(self):
        self.login()
        old_day = (date.today() - timedelta(days=16)).isoformat()
        self.client.post("/applications", data={
            "applied_at": old_day,
            "company": "老公司",
            "role": "后端实习",
            "status": "已投递",
            "has_interview": "unknown",
            "interview_passed": "unknown",
        })

        page = self.client.get("/?due=1")
        self.assertIn("老公司".encode(), page.data)
        self.assertIn("待复看".encode(), page.data)

        self.client.post("/applications/1/review", follow_redirects=True)
        reviewed = self.client.get("/?due=1")
        self.assertNotIn("老公司".encode(), reviewed.data)


if __name__ == "__main__":
    unittest.main()
