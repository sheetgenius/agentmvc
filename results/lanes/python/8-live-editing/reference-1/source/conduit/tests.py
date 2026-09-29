from django.db import connection
from django.test import SimpleTestCase, TestCase
from django.test.utils import CaptureQueriesContext

from .accounts import token_for
from .models import Article, Comment, User


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


class ReferenceRegressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user("owner", "owner@example.com")
        cls.reader = User.objects.create_user("reader", "reader@example.com")
        cls.other = User.objects.create_user("other", "other@example.com")
        cls.article = Article.objects.create(
            author=cls.owner,
            slug="reference",
            title="Reference",
            description="Regression",
            body="Original",
        )

    def headers(self, user):
        return {"Authorization": f"Token {token_for(user)}"} if user else {}

    def test_malformed_edit_checks_authority_before_shape_and_never_mutates(self):
        before = Article.objects.values().get(pk=self.article.pk)
        for user, slug, status in (
            (None, "reference", 401),
            (self.reader, "reference", 403),
            (self.owner, "missing", 404),
            (self.owner, "reference", 422),
        ):
            with self.subTest(status=status):
                response = self.client.put(
                    f"/api/articles/{slug}",
                    {"article": []},
                    content_type="application/json",
                    headers=self.headers(user),
                )
                self.assertEqual(response.status_code, status)
        self.assertEqual(Article.objects.values().get(pk=self.article.pk), before)
        response = self.client.put(
            "/api/articles/reference",
            {"article": {"revision": 0, "body": []}},
            content_type="application/json",
            headers=self.headers(self.owner),
        )
        self.assertEqual(response.status_code, 409)

    def test_favorite_filter_preserves_global_count_and_viewer_flag(self):
        self.article.favorites.add(self.reader, self.other)
        for favoriter in (self.reader, self.other):
            for viewer in (None, self.owner, self.reader, self.other):
                with self.subTest(filter=favoriter.username, viewer=viewer):
                    response = self.client.get(
                        f"/api/articles?favorited={favoriter.username}",
                        headers=self.headers(viewer),
                    )
                    article = response.json()["articles"][0]
                    self.assertEqual(article["favoritesCount"], 2)
                    self.assertEqual(article["favorited"], viewer in (self.reader, self.other))

    def test_comment_queries_do_not_grow_with_page_length(self):
        self.reader.following.add(self.owner)
        Comment.objects.create(article=self.article, author=self.owner, body="One")
        url = "/api/articles/reference/comments"
        headers = self.headers(self.reader)
        with CaptureQueriesContext(connection) as one:
            self.assertEqual(self.client.get(url, headers=headers).status_code, 200)
        Comment.objects.bulk_create(
            [Comment(article=self.article, author=self.owner, body=str(n)) for n in range(19)]
        )
        with CaptureQueriesContext(connection) as twenty:
            response = self.client.get(url, headers=headers)
        self.assertEqual(len(one), len(twenty))
        comments = response.json()["comments"]
        self.assertEqual(len(comments), 20)
        self.assertTrue(all(comment["author"]["following"] for comment in comments))
