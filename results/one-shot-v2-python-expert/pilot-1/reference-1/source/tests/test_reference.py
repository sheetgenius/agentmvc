from datetime import timedelta
from hashlib import sha256
from unittest.mock import patch

from django.db import connection, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from conduit.domain import create_article, token_for
from conduit.models import Article, Comment, Favorite, Follow, LoginAttempt, Share
from tests.test_rules import user


class ReferenceRegressions(TestCase):
    def setUp(self):
        self.author = user("author")
        self.reader = user("reader")
        self.article = create_article(
            self.author, {"title": "Reference", "description": "d", "body": "large body" * 100}
        )
        self.owner_headers = {"Authorization": f"Token {token_for(self.author)}"}
        self.reader_headers = {"Authorization": f"Token {token_for(self.reader)}"}

    def test_favorite_filter_preserves_total_count_and_viewer_flag(self):
        Favorite.objects.create(user=self.author, article=self.article)
        Favorite.objects.create(user=self.reader, article=self.article)
        for headers, favorited in (({}, False), (self.reader_headers, True)):
            response = self.client.get(
                "/api/articles", {"favorited": self.author.username}, headers=headers
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["articlesCount"], 1)
            item = response.json()["articles"][0]
            self.assertEqual((item["favoritesCount"], item["favorited"]), (2, favorited))

    def test_shared_outer_fields_rejected_after_authorization_without_mutation(self):
        Share.objects.create(id="link", article=self.article, key_hash=sha256(b"key").hexdigest())
        payload = {
            "article": {"title": "Changed", "body": "changed", "revision": 1},
            "extra": True,
        }
        for key, status in (("invalid", 404), ("key", 422)):
            response = self.client.put(
                "/api/shares/link/article",
                data=payload,
                content_type="application/json",
                headers={"X-Share-Key": key},
            )
            self.assertEqual(response.status_code, status)
            self.assertIn("errors", response.json())
            unchanged = Article.objects.get(pk=self.article.pk)
            self.assertEqual(
                (unchanged.title, unchanged.body, unchanged.revision),
                (self.article.title, self.article.body, 1),
            )

    def test_locked_login_recovers_after_window_expiry(self):
        attempt = LoginAttempt.objects.create(
            email=self.author.email, count=20, expires_at=timezone.now() + timedelta(minutes=15)
        )
        credentials = {"user": {"email": self.author.email, "password": "password123"}}
        self.assertEqual(
            self.client.post(
                "/api/users/login", data=credentials, content_type="application/json"
            ).status_code,
            429,
        )
        attempt.refresh_from_db()
        self.assertEqual(attempt.count, 20)
        attempt.expires_at = timezone.now() - timedelta(seconds=1)
        attempt.save(update_fields=["expires_at"])
        response = self.client.post(
            "/api/users/login", data=credentials, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        attempt.refresh_from_db()
        self.assertEqual(attempt.count, 0)
        self.assertGreater(attempt.expires_at, timezone.now())

    def test_article_delete_revokes_only_after_commit(self):
        Share.objects.create(id="link", article=self.article, key_hash=sha256(b"key").hexdigest())
        with patch("conduit.live.revoke_after_commit") as revoke:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                response = self.client.delete(
                    f"/api/articles/{self.article.slug}", headers=self.owner_headers
                )
                self.assertEqual(response.status_code, 204)
                revoke.assert_not_called()
                self.assertFalse(Share.objects.exists())
            self.assertEqual(len(callbacks), 1)
            revoke.assert_called_once_with("link")

    def test_rolled_back_delete_does_not_revoke(self):
        Share.objects.create(id="link", article=self.article, key_hash=sha256(b"key").hexdigest())
        with patch("conduit.live.revoke_after_commit") as revoke:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                with self.assertRaises(RuntimeError), transaction.atomic():
                    self.client.delete(
                        f"/api/articles/{self.article.slug}", headers=self.owner_headers
                    )
                    raise RuntimeError("rollback")
            self.assertEqual(callbacks, [])
            revoke.assert_not_called()
        self.assertTrue(Share.objects.filter(pk="link").exists())

    def test_signed_comment_reads_have_constant_query_count(self):
        Follow.objects.create(follower=self.reader, followed=self.author)
        Comment.objects.create(article=self.article, author=self.author, body="one")

        def read_comments():
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get(
                    f"/api/articles/{self.article.slug}/comments", headers=self.reader_headers
                )
            self.assertEqual(response.status_code, 200)
            rows = response.json()["comments"]
            self.assertTrue(all(row["author"]["following"] for row in rows))
            return len(rows), len(queries)

        one_count, one_queries = read_comments()
        Comment.objects.bulk_create(
            [Comment(article=self.article, author=self.author, body=str(n)) for n in range(19)]
        )
        many_count, many_queries = read_comments()
        self.assertEqual((one_count, many_count), (1, 20))
        self.assertEqual(one_queries, many_queries)
        self.assertLessEqual(many_queries, 3)

    def test_summary_query_does_not_fetch_article_body(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get("/api/articles")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("body", response.json()["articles"][0])
        self.assertNotIn('"conduit_article"."body"', "\n".join(q["sql"] for q in queries))
