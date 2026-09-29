import asyncio
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.db import connection, transaction
from django.test import SimpleTestCase, TestCase, TransactionTestCase

from conduit.domain import (
    RuleError,
    article_visible,
    commit_edit,
    create_article,
    edit_user,
    password_valid,
    published_for_interaction,
)
from conduit.live import Rooms
from conduit.models import Article, Export, Share, User
from conduit.tasks import build_export


def user(name):
    return User.objects.create(
        username=name,
        email=f"{name}@example.test",
        password_hash=make_password("password123"),
    )


class DomainRules(TestCase):
    def test_draft_visibility_and_interaction(self):
        author, other = user("author"), user("other")
        draft = create_article(
            author, {"title": "Private", "description": "d", "body": "b", "status": "draft"}
        )
        self.assertEqual(article_visible(draft.slug, author).pk, draft.pk)
        self.assertFalse(Article.objects.public().filter(pk=draft.pk).exists())
        for viewer in (None, other):
            with self.assertRaises(RuleError) as caught:
                article_visible(draft.slug, viewer)
            self.assertEqual(caught.exception.status, 404)
        with self.assertRaises(RuleError) as caught:
            published_for_interaction(draft)
        self.assertEqual((caught.exception.status, caught.exception.message), (422, "is a draft"))

    def test_author_and_share_use_one_revision_rule(self):
        author = user("writer")
        article = create_article(author, {"title": "First", "description": "d", "body": "b"})
        share = Share.objects.create(
            id="link", article=article, key_hash=sha256(b"secret").hexdigest()
        )
        changed = commit_edit(
            article, {"title": "Second", "body": "new", "revision": 1}, share=share
        )
        self.assertEqual((changed.revision, changed.slug != article.slug), (2, True))
        with self.assertRaises(RuleError) as caught:
            commit_edit(article, {"body": "stale", "revision": 1}, viewer=author)
        self.assertEqual((caught.exception.status, caught.exception.article.revision), (409, 2))
        self.assertEqual(Article.objects.get(pk=article.pk).body, "new")
        self.assertEqual(
            commit_edit(article, {"body": "author", "revision": 2}, viewer=author).revision, 3
        )
        share.delete()
        with self.assertRaises(RuleError) as caught:
            commit_edit(article, {"title": "revoked", "body": "x", "revision": 3}, share=share)
        self.assertEqual(caught.exception.status, 404)

    def test_password_policy_is_shared_by_registration_and_update(self):
        account = user("passwords")
        for value in ("", "short7c"):
            with self.assertRaises(RuleError):
                password_valid(value)
            with self.assertRaises(RuleError):
                edit_user(account, {"password": value})
        self.assertNotEqual(edit_user(account, {"password": "a" * 64}).password_hash, "a" * 64)


class ExportAtomicity(TransactionTestCase):
    def test_export_and_job_roll_back_together(self):
        author = user("exporter")
        with connection.cursor() as cursor:
            cursor.execute("select count(*) from procrastinate_jobs")
            before = cursor.fetchone()[0]
        with self.assertRaises(RuntimeError), transaction.atomic():
            export = Export.objects.create(user=author)
            build_export.defer(export_id=export.pk)
            raise RuntimeError("rollback")
        self.assertEqual(Export.objects.count(), 0)
        with connection.cursor() as cursor:
            cursor.execute("select count(*) from procrastinate_jobs")
            self.assertEqual(cursor.fetchone()[0], before)


class RoomAdmission(SimpleTestCase):
    def test_cap_counts_authorized_sockets(self):
        fake_article = SimpleNamespace(pk=1, slug="slug", title="title", body="body", revision=1)

        async def exercise():
            rooms = Rooms()
            clients = [object() for _ in range(101)]
            results = [await rooms.join(client, "link", "secret") for client in clients]
            self.assertEqual([result[0] for result in results[:100]], ["ready"] * 100)
            self.assertEqual(results[100][0], "room_full")
            self.assertEqual(results[99][2], 100)

        with patch(
            "conduit.live.share_for",
            return_value=SimpleNamespace(article=fake_article, article_id=1),
        ):
            asyncio.run(exercise())
