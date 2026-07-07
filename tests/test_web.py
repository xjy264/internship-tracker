import os
import tempfile
import unittest
from datetime import date, timedelta

from app import create_app, get_db, init_db
from tracker_core import add_application, add_task


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

    def test_home_is_read_only_one_row_per_application_and_shows_task(self):
        with self.app.app_context():
            db = get_db()
            add_task(db, "务必开始投递")
            add_application(db, {
                "applied_at": "2026-07-06",
                "company": "字节",
                "role": "前端实习",
                "status": "已投递",
            })
        page = self.login().data.decode()
        self.assertIn("务必开始投递", page)
        self.assertIn("字节", page)
        self.assertEqual(page.count('data-app-id="1"'), 1)
        for text in ("新增投递", "保存投递", "编辑", "删除", "标记复看"):
            self.assertNotIn(text, page)
        self.assertEqual(self.client.post("/applications", data={}).status_code, 404)

    def test_company_links_to_job_url_in_new_tab(self):
        with self.app.app_context():
            add_application(get_db(), {
                "applied_at": "2026-07-07",
                "company": "美团",
                "role": "后台产品实习生",
                "job_url": "https://zhaopin.example/jobs/1",
            })
        page = self.login().data.decode()
        self.assertIn('<a href="https://zhaopin.example/jobs/1" target="_blank" rel="noopener noreferrer">美团</a>', page)

    def test_due_filter_still_works_in_read_only_table(self):
        self.login()
        with self.app.app_context():
            old_day = (date.today() - timedelta(days=16)).isoformat()
            add_application(get_db(), {"applied_at": old_day, "company": "老公司", "role": "后端实习", "status": "已投递"})
        page = self.client.get("/?due=1").data.decode()
        self.assertIn("老公司", page)
        self.assertIn("待复看", page)


if __name__ == "__main__":
    unittest.main()
