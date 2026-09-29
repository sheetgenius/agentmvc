import json
import secrets
from hashlib import sha256

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.http import HttpResponse
from django.utils import timezone
from ninja import NinjaAPI

from .domain import (
    RuleError,
    article_json,
    article_visible,
    commit_edit,
    create_article,
    edit_user,
    export_json,
    login_limited,
    nonblank,
    own_article,
    page,
    parse,
    profile_json,
    published_for_interaction,
    register,
    require,
    share_for,
    shared_json,
    user_from_header,
    user_json,
)
from .models import Article, ArticleTag, Comment, Export, Favorite, Follow, Share, User
from .tasks import build_export

api = NinjaAPI(docs_url=None, openapi_url=None)


@api.exception_handler(RuleError)
def rule_error(request, exc):
    result = {"errors": {exc.field: [exc.message]}}
    if exc.article:
        result["article"] = (
            shared_json(exc.article)
            if request.path.startswith("/api/shares/")
            else article_json(exc.article, user_from_header(request.headers.get("Authorization")))
        )
    return api.create_response(request, result, status=exc.status)


def viewer(request, required=False):
    user = user_from_header(request.headers.get("Authorization"))
    return require(user) if required else user


def payload(request, wrapper, *, strict=False):
    try:
        value = json.loads(request.body)
    except ValueError, UnicodeDecodeError:
        raise RuleError(400, wrapper, "is invalid") from None
    if not isinstance(value, dict) or not isinstance(value.get(wrapper), dict):
        raise RuleError(422, wrapper, "is invalid")
    if strict and set(value) != {wrapper}:
        raise RuleError(422, wrapper, "is invalid")
    return value[wrapper]


def pagination(request):
    try:
        limit = int(request.GET.get("limit", 20))
        offset = int(request.GET.get("offset", 0))
        if limit < 0 or offset < 0 or limit > 1000 or offset > 1_000_000_000:
            raise ValueError
    except ValueError:
        raise RuleError(422, "pagination", "is invalid") from None
    return limit, offset


def article_result(article, user=None):
    article = Article.objects.select_related("author").prefetch_related("tags").get(pk=article.pk)
    return {"article": article_json(article, user)}


@api.get("/health")
def health(request):
    return {"status": "ok"}


@api.post("/api/users", response={201: dict})
def users(request):
    user = register(payload(request, "user"))
    return 201, {"user": user_json(user)}


@api.post("/api/users/login")
def login(request):
    from .domain import Login

    form = parse(Login, payload(request, "user"))
    nonblank(form.email, "email")
    nonblank(form.password, "password")
    user = User.objects.filter(email=form.email).first()
    # A valid Argon2 hash is checked even for an unknown account.
    valid = check_password(form.password, user.password_hash if user else DUMMY_HASH)
    rejected = not user or not valid
    if login_limited(form.email, rejected):
        raise RuleError(429, "credentials", "rate limited")
    if rejected:
        raise RuleError(401, "credentials", "invalid")
    return {"user": user_json(user)}


DUMMY_HASH = make_password("a dummy password used for constant work")


@api.get("/api/user")
def current_user(request):
    return {"user": user_json(viewer(request, True))}


@api.put("/api/user")
def update_user(request):
    user = viewer(request, True)
    return {"user": user_json(edit_user(user, payload(request, "user")))}


@api.get("/api/profiles/{username}")
def profile(request, username: str):
    user = viewer(request)
    target = User.objects.filter(username=username).first()
    if not target:
        raise RuleError(404, "profile", "not found")
    return {"profile": profile_json(target, user)}


@api.post("/api/profiles/{username}/follow")
@api.delete("/api/profiles/{username}/follow")
def follow(request, username: str):
    user = viewer(request, True)
    target = User.objects.filter(username=username).first()
    if not target:
        raise RuleError(404, "profile", "not found")
    if target.pk != user.pk:
        if request.method == "POST":
            Follow.objects.get_or_create(follower=user, followed=target)
        else:
            Follow.objects.filter(follower=user, followed=target).delete()
    return {"profile": profile_json(target, user)}


@api.get("/api/articles/feed")
def feed(request):
    user = viewer(request, True)
    limit, offset = pagination(request)
    qs = Article.objects.public().filter(author__follower_links__follower=user)
    return page(qs, user, limit, offset)


@api.get("/api/user/drafts")
def drafts(request):
    user = viewer(request, True)
    limit, offset = pagination(request)
    return page(Article.objects.filter(author=user, status="draft"), user, limit, offset)


@api.get("/api/articles")
def articles(request):
    user = viewer(request)
    limit, offset = pagination(request)
    qs = Article.objects.public()
    if tag := request.GET.get("tag"):
        qs = qs.filter(tags__name=tag)
    if author := request.GET.get("author"):
        qs = qs.filter(author__username=author)
    if favorited := request.GET.get("favorited"):
        qs = qs.filter(
            pk__in=Favorite.objects.filter(user__username=favorited).values("article_id")
        )
    return page(qs, user, limit, offset)


@api.post("/api/articles", response={201: dict})
def new_article(request):
    user = viewer(request, True)
    return 201, article_result(create_article(user, payload(request, "article")), user)


@api.get("/api/articles/{slug}")
def get_article(request, slug: str):
    user = viewer(request)
    return article_result(article_visible(slug, user), user)


@api.put("/api/articles/{slug}")
def put_article(request, slug: str):
    user = viewer(request, True)
    article = article_visible(slug, user)
    own_article(article, user)
    return article_result(commit_edit(article, payload(request, "article"), viewer=user), user)


@api.delete("/api/articles/{slug}")
def delete_article(request, slug: str):
    user = viewer(request, True)
    with transaction.atomic():
        article = article_visible(slug, user, lock=True)
        own_article(article, user)
        share_id = Share.objects.filter(article=article).values_list("pk", flat=True).first()
        article.delete()
        if share_id:
            from .live import revoke_after_commit

            transaction.on_commit(lambda: revoke_after_commit(share_id))
    return HttpResponse(status=204)


@api.post("/api/articles/{slug}/publish")
def publish(request, slug: str):
    user = viewer(request, True)
    with transaction.atomic():
        article = article_visible(slug, user, lock=True)
        own_article(article, user)
        if article.status == "draft":
            article.status = "published"
            article.published_at = timezone.now()
            article.revision += 1
            article.save(update_fields=["status", "published_at", "revision", "updated_at"])
    return article_result(article, user)


@api.get("/api/tags")
def tags(request):
    return {
        "tags": list(
            ArticleTag.objects.filter(article__status="published")
            .order_by("name")
            .values_list("name", flat=True)
            .distinct()
        )
    }


@api.post("/api/articles/{slug}/favorite")
@api.delete("/api/articles/{slug}/favorite")
def favorite(request, slug: str):
    user = viewer(request, True)
    article = article_visible(slug, user)
    published_for_interaction(article)
    if request.method == "POST":
        Favorite.objects.get_or_create(user=user, article=article)
    else:
        Favorite.objects.filter(user=user, article=article).delete()
    return article_result(article, user)


@api.get("/api/articles/{slug}/comments")
def comments(request, slug: str):
    user = viewer(request)
    article = article_visible(slug, user)
    rows = (
        Comment.objects.filter(article=article)
        .select_related("author")
        .order_by("created_at", "pk")
    )
    if user:
        rows = rows.annotate(
            author_followed=Exists(
                Follow.objects.filter(follower=user, followed_id=OuterRef("author_id"))
            )
        )
    return {"comments": [comment_json(row, user) for row in rows]}


def comment_json(comment, user):
    return {
        "id": comment.pk,
        "createdAt": comment.created_at.isoformat(),
        "updatedAt": comment.updated_at.isoformat(),
        "body": comment.body,
        "author": profile_json(comment.author, user, getattr(comment, "author_followed", None)),
    }


@api.post("/api/articles/{slug}/comments", response={201: dict})
def new_comment(request, slug: str):
    user = viewer(request, True)
    article = article_visible(slug, user)
    published_for_interaction(article)
    data = payload(request, "comment")
    body = data.get("body")
    if not isinstance(body, str):
        raise RuleError(422, "body", "is invalid")
    nonblank(body, "body")
    comment = Comment.objects.create(article=article, author=user, body=body)
    return 201, {"comment": comment_json(comment, user)}


@api.delete("/api/articles/{slug}/comments/{comment_id}")
def delete_comment(request, slug: str, comment_id: str):
    user = viewer(request, True)
    article = article_visible(slug, user)
    try:
        comment = Comment.objects.get(pk=int(comment_id), article=article)
    except ValueError, Comment.DoesNotExist:
        raise RuleError(404, "comment", "not found") from None
    if comment.author_id != user.pk:
        raise RuleError(403, "comment", "forbidden")
    comment.delete()
    return HttpResponse(status=204)


@api.post("/api/user/exports", response={202: dict})
def start_export(request):
    user = viewer(request, True)
    with transaction.atomic():
        export = Export.objects.create(user=user)
        build_export.defer(export_id=export.pk)
    return 202, {"export": export_json(export)}


@api.get("/api/user/exports/{export_id}")
def get_export(request, export_id: str):
    user = viewer(request, True)
    export = (
        Export.objects.filter(pk=export_id, user=user).first() if export_id.isdecimal() else None
    )
    if not export:
        raise RuleError(404, "export", "not found")
    return {"export": export_json(export)}


@api.post("/api/articles/{slug}/share", response={201: dict})
def create_share(request, slug: str):
    user = viewer(request, True)
    with transaction.atomic():
        article = article_visible(slug, user, lock=True)
        own_article(article, user)
        old = Share.objects.filter(article=article).first()
        if old:
            old_id = old.pk
            old.delete()
            from .live import revoke_after_commit

            transaction.on_commit(lambda: revoke_after_commit(old_id))
        key = secrets.token_urlsafe(32)
        share = Share.objects.create(
            id=secrets.token_urlsafe(18), article=article, key_hash=sha256(key.encode()).hexdigest()
        )
    return 201, {"share": {"id": share.pk, "key": key}}


@api.delete("/api/articles/{slug}/share")
def revoke_share(request, slug: str):
    user = viewer(request, True)
    with transaction.atomic():
        article = article_visible(slug, user, lock=True)
        own_article(article, user)
        old = Share.objects.filter(article=article).first()
        if old:
            old_id = old.pk
            old.delete()
            from .live import revoke_after_commit

            transaction.on_commit(lambda: revoke_after_commit(old_id))
    return HttpResponse(status=204)


@api.get("/api/shares/{share_id}/article")
def shared_article(request, share_id: str):
    share = share_for(share_id, request.headers.get("X-Share-Key"))
    return {"article": shared_json(share.article)}


@api.put("/api/shares/{share_id}/article")
def shared_edit(request, share_id: str):
    share = share_for(share_id, request.headers.get("X-Share-Key"))
    article = commit_edit(share.article, payload(request, "article", strict=True), share=share)
    return {"article": shared_json(article)}
