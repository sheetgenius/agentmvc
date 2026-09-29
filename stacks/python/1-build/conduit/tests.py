from django.test import SimpleTestCase


class AuthenticationTests(SimpleTestCase):
    def test_invalid_token_is_rejected(self):
        response = self.client.get("/api/user", headers={"Authorization": "Token invalid"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"errors": {"token": ["is invalid"]}})
