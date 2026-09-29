"""Editing capabilities and their revision-checked HTTP surface."""

import json
import secrets
from hashlib import sha256
from hmac import compare_digest
from uuid import uuid4

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from ninja import Router

from .accounts import required_user
from .http import APIError, require_value
from .models import Article, EditingLink

router = Router()


def shared_article(article):
    return {
        "slug": article.slug,
        "title": article.title,
        "body": article.body,
        "revision": article.revision,
    }


def room_name(share_id):
    return f"share.{sha256(share_id.encode()).hexdigest()}"


def notify(share_id, message):
    async_to_sync(get_channel_layer().group_send)(room_name(share_id), message)


def article_changed(article):
    share_id = EditingLink.objects.filter(article=article).values_list("pk", flat=True).first()
    if share_id:
        snapshot = shared_article(article)
        transaction.on_commit(
            lambda: notify(share_id, {"type": "article_updated", "article": snapshot})
        )


def revoke_after_commit(share_id):
    if share_id:
        transaction.on_commit(lambda: notify(share_id, {"type": "link_revoked"}))


def revoke_link(article):
    link = EditingLink.objects.filter(article=article).first()
    if link:
        share_id = link.pk
        link.delete()
        revoke_after_commit(share_id)


def key_hash(key):
    return sha256(key.encode()).hexdigest()


def accepts_key(link, key):
    return (
        link is not None and isinstance(key, str) and compare_digest(link.key_hash, key_hash(key))
    )


def valid_link(share_id, key):
    link = EditingLink.objects.select_related("article").filter(pk=share_id).first()
    return link if accepts_key(link, key) else None


def require_link(share_id, key):
    link = valid_link(share_id, key)
    if link is None:
        raise APIError(404, "share", "not found")
    return link


def locked_link(share_id, key):
    article_id = (
        EditingLink.objects.filter(pk=share_id).values_list("article_id", flat=True).first()
    )
    if article_id is None:
        raise APIError(404, "share", "not found")
    article = Article.objects.select_for_update().filter(pk=article_id).first()
    if article is None:
        raise APIError(404, "share", "not found")
    link = EditingLink.objects.filter(pk=share_id, article=article).first()
    if not accepts_key(link, key):
        raise APIError(404, "share", "not found")
    return article


def edit_fields(request):
    try:
        payload = json.loads(request.body)
    except ValueError, UnicodeDecodeError:
        raise APIError(422, "article", "is invalid") from None
    if not isinstance(payload, dict) or set(payload) != {"article"}:
        raise APIError(422, "article", "is invalid")
    data = payload["article"]
    if not isinstance(data, dict) or set(data) != {"title", "body", "revision"}:
        raise APIError(422, "article", "is invalid")
    title = require_value("title", data["title"])
    body = require_value("body", data["body"])
    if len(title) > 255:
        raise APIError(422, "title", "is invalid")
    if type(data["revision"]) is not int:
        raise APIError(422, "revision", "is invalid")
    return title, body, data["revision"]


@router.post("/articles/{slug}/share", auth=required_user, response={201: dict})
def create_share(request, slug: str):
    from .articles import article_or_404, owned

    with transaction.atomic():
        article = article_or_404(slug, request.auth, lock=True)
        owned(article, request.auth, "article")
        revoke_link(article)
        key = secrets.token_urlsafe(32)
        link = EditingLink.objects.create(id=uuid4().hex, article=article, key_hash=key_hash(key))
    return 201, {"share": {"id": link.pk, "key": key}}


@router.delete("/articles/{slug}/share", auth=required_user, response={204: None})
def delete_share(request, slug: str):
    from .articles import article_or_404, owned

    with transaction.atomic():
        article = article_or_404(slug, request.auth, lock=True)
        owned(article, request.auth, "article")
        revoke_link(article)
    return 204, None


@router.get("/shares/{share_id}/article")
def get_shared_article(request, share_id: str):
    link = require_link(share_id, request.headers.get("X-Share-Key"))
    return {"article": shared_article(link.article)}


@router.put("/shares/{share_id}/article")
def update_shared_article(request, share_id: str):
    with transaction.atomic():
        article = locked_link(share_id, request.headers.get("X-Share-Key"))
        title, body, revision = edit_fields(request)
        if revision != article.revision:
            raise APIError(409, "revision", "is stale", article=shared_article(article))
        article.set_title(title)
        article.body = body
        article.revision += 1
        article.save()
        article_changed(article)
        snapshot = shared_article(article)
    return {"article": snapshot}
