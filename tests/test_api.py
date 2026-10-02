import os
import tempfile
import unittest

from app import create_app


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        app = create_app(self.db_path)
        app.config["TESTING"] = True
        self.client = app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.remove(self.db_path)

    def _create(self, **overrides):
        payload = {"company": "Zenithbyte", "role": "Python Development Intern"}
        payload.update(overrides)
        return self.client.post("/api/applications", json=payload)

    def test_health(self):
        self.assertEqual(self.client.get("/api/health").get_json(), {"status": "ok"})

    def test_create_and_get(self):
        res = self._create()
        self.assertEqual(res.status_code, 201)
        body = res.get_json()
        self.assertEqual(body["status"], "applied")
        got = self.client.get(f"/api/applications/{body['id']}")
        self.assertEqual(got.get_json()["company"], "Zenithbyte")

    def test_create_validation_errors(self):
        res = self.client.post("/api/applications", json={"company": ""})
        self.assertEqual(res.status_code, 400)
        self.assertIn("'role' is required", res.get_json()["errors"])

    def test_invalid_status_rejected(self):
        self.assertEqual(self._create(status="ghosted").status_code, 400)

    def test_invalid_date_rejected(self):
        self.assertEqual(self._create(applied_on="02-10-2026").status_code, 400)

    def test_filter_by_status(self):
        self._create()
        self._create(company="Acme", status="interview")
        res = self.client.get("/api/applications?status=interview")
        data = res.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["company"], "Acme")

    def test_update(self):
        app_id = self._create().get_json()["id"]
        res = self.client.put(f"/api/applications/{app_id}", json={"status": "offer"})
        self.assertEqual(res.get_json()["status"], "offer")

    def test_update_missing_returns_404(self):
        res = self.client.put("/api/applications/999", json={"status": "offer"})
        self.assertEqual(res.status_code, 404)

    def test_delete(self):
        app_id = self._create().get_json()["id"]
        self.assertEqual(self.client.delete(f"/api/applications/{app_id}").status_code, 204)
        self.assertEqual(self.client.get(f"/api/applications/{app_id}").status_code, 404)

    def test_stats(self):
        self._create()
        self._create(status="rejected")
        stats = self.client.get("/api/stats").get_json()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["by_status"]["rejected"], 1)


if __name__ == "__main__":
    unittest.main()
