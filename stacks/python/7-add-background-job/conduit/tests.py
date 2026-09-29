from django.test import SimpleTestCase, TestCase

from .models import User


class AuthenticationTests(SimpleTestCase):
    def test_invalid_token_is_rejected(self):
        response = self.client.get("/api/user", headers={"Authorization": "Token invalid"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"errors": {"token": ["is invalid"]}})


class SecurityTests(TestCase):
    def test_login_throttles_failed_attempts_per_email(self):
        User.objects.create_user("alice", "alice@example.com", "password123")
        credentials = {"user": {"email": "alice@example.com", "password": "wrongpassword"}}
        for _ in range(5):
            self.assertEqual(
                self.client.post(
                    "/api/users/login", credentials, content_type="application/json"
                ).status_code,
                401,
            )
        self.assertEqual(
            self.client.post(
                "/api/users/login", credentials, content_type="application/json"
            ).status_code,
            429,
        )

    def test_absurd_page_size_is_rejected(self):
        response = self.client.get("/api/articles?limit=99999999999999999999")
        self.assertEqual(response.status_code, 422)
