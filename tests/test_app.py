import io
import tempfile
import unittest
from pathlib import Path

import app as webapp


class WebAppTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        webapp.DATABASE_PATH = Path(self.temp_dir.name) / "test.db"
        webapp.UPLOAD_FOLDER = Path(self.temp_dir.name) / "uploads"
        webapp.app.config["TESTING"] = True
        webapp.app.config["WTF_CSRF_ENABLED"] = False
        webapp.init_db()
        self.client = webapp.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def register_and_login(self):
        self.client.post("/register", data={"username": "tester", "password": "secret1"})
        return self.client.post(
            "/login",
            data={"username": "tester", "password": "secret1"},
            follow_redirects=True,
        )

    def test_auth_flow(self):
        response = self.register_and_login()
        self.assertIn("Xin chào".encode(), response.data)

    def test_upload_and_download(self):
        self.register_and_login()

        upload_response = self.client.post(
            "/dashboard",
            data={"file": (io.BytesIO(b"hello"), "demo.txt")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertEqual(upload_response.status_code, 200)
        self.assertIn(b"demo.txt", upload_response.data)

        download_response = self.client.get("/download/demo.txt")
        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(download_response.data, b"hello")


if __name__ == "__main__":
    unittest.main()
