import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import jwt
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils import timezone as django_timezone
from django.utils.text import slugify
from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr, ValidationError

from .models import Article, ArticleTag, Favorite, Follow, LoginAttempt, Share, User


class RuleError(Exception):
    def __init__(self, status, field, message, article=None):
        self.status = status
        self.field = field
        self.message = message
        self.article = article


class Input(BaseModel):
    model_config = ConfigDict(extra="ignore")


class Registration(Input):
    username: StrictStr
    email: StrictStr
    password: StrictStr


class Login(Input):
    email: StrictStr
    password: StrictStr


class UserEdit(Input):
    username: StrictStr | None = None
    email: StrictStr | None = None
    password: StrictStr | None = None
    bio: StrictStr | None = None
    image: StrictStr | None = None


class ArticleCreate(Input):
    title: StrictStr
    description: StrictStr
    body: StrictStr
    tagList: list[StrictStr] = []
    status: StrictStr = "published"


class ArticleEdit(Input):
    title: StrictStr | None = None
    description: StrictStr | None = None
    body: StrictStr | None = None
    tagList: list[StrictStr] | None = None
    revision: StrictInt | None = None


class ShareEdit(Input):
    model_config = ConfigDict(extra="forbid")
    title: StrictStr
    body: StrictStr
    revision: StrictInt


def parse(model, value):
    try:
        return model.model_validate(value)
    except ValidationError as exc:
        first = exc.errors()[0]
        field = str(first["loc"][0]) if first["loc"] else "article"
        raise RuleError(422, field, "is invalid") from exc


def nonblank(value, field):
    if not value or not value.strip():
        raise RuleError(422, field, "can't be blank")


def password_valid(value):
    nonblank(value, "password")
    if len(value) < 8:
        raise RuleError(422, "password", "is too short")


def login_limited(email, rejected):
    now = django_timezone.now()
    with transaction.atomic():
        attempt, _ = LoginAttempt.objects.select_for_update().get_or_create(
            email=email, defaults={"expires_at": now + timedelta(minutes=15)}
        )
        if attempt.expires_at <= now:
            attempt.count = 0
            attempt.expires_at = now + timedelta(minutes=15)
        limited = attempt.count >= 20
        if not limited:
            attempt.count = attempt.count + 1 if rejected else 0
            attempt.save(update_fields=["count", "expires_at"])
    return limited


def token_for(user):
    return jwt.encode(
        {
            "sub": str(user.pk),
            "v": user.token_version,
            "exp": datetime.now(UTC) + timedelta(days=30),
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def user_from_header(header):
    if not header:
        return None
    if not header.startswith("Token "):
        raise RuleError(401, "token", "is invalid")
    try:
        data = jwt.decode(header[6:], settings.SECRET_KEY, algorithms=["HS256"])
        user = User.objects.get(pk=int(data["sub"]))
        if data.get("v") != user.token_version:
            raise ValueError("revoked")
        return user
    except (jwt.PyJWTError, User.DoesNotExist, ValueError, KeyError, TypeError) as exc:
        raise RuleError(401, "token", "is invalid") from exc


def require(user):
    if not user:
        raise RuleError(401, "token", "is missing")
    return user


def user_json(user):
    return {
        "email": user.email,
        "token": token_for(user),
        "username": user.username,
        "bio": user.bio,
        "image": user.image,
    }


def register(data):
    form = parse(Registration, data)
    for field in ("username", "email"):
        nonblank(getattr(form, field), field)
    password_valid(form.password)
    for field in ("username", "email"):
        if User.objects.filter(**{field: getattr(form, field)}).exists():
            raise RuleError(409, field, "has already been taken")
    try:
        return User.objects.create(
            username=form.username, email=form.email, password_hash=make_password(form.password)
        )
    except IntegrityError as exc:
        raise RuleError(409, "email", "has already been taken") from exc


def edit_user(user, data):
    form = parse(UserEdit, data)
    fields = form.model_fields_set
    for field in ("username", "email", "password"):
        if field in fields:
            value = getattr(form, field)
            if value is None:
                raise RuleError(422, field, "is invalid")
            nonblank(value, field)
            if field == "password":
                password_valid(value)
            elif User.objects.filter(**{field: value}).exclude(pk=user.pk).exists():
                raise RuleError(409, field, "has already been taken")
    for field in ("username", "email", "bio", "image"):
        if field in fields:
            value = getattr(form, field)
            setattr(user, field, value or None if field in ("bio", "image") else value)
    if "password" in fields:
        user.password_hash = make_password(form.password)
    try:
        user.save()
    except IntegrityError as exc:
        raise RuleError(409, "email", "has already been taken") from exc
    return user


def profile_json(target, viewer, following=None):
    if following is None:
        following = bool(
            viewer and Follow.objects.filter(follower=viewer, followed=target).exists()
        )
    return {
        "username": target.username,
        "bio": target.bio,
        "image": target.image,
        "following": following,
    }


def article_visible(slug, viewer, lock=False):
    qs = Article.objects.visible_to(viewer).select_related("author")
    if lock:
        qs = qs.select_for_update()
    article = qs.filter(slug=slug).first()
    if article is None:
        raise RuleError(404, "article", "not found")
    return article


def own_article(article, viewer):
    if article.author_id != viewer.id:
        raise RuleError(403, "article", "forbidden")


def published_for_interaction(article):
    if article.status == Article.Status.DRAFT:
        raise RuleError(422, "article", "is a draft")


def slug_for(title):
    return f"{slugify(title)[:190] or 'article'}-{secrets.token_hex(5)}"


def set_tags(article, tags):
    unique = list(dict.fromkeys(tags))
    ArticleTag.objects.filter(article=article).delete()
    ArticleTag.objects.bulk_create(
        [ArticleTag(article=article, name=name, position=i) for i, name in enumerate(unique)]
    )


def create_article(user, data):
    form = parse(ArticleCreate, data)
    for field in ("title", "description", "body"):
        nonblank(getattr(form, field), field)
    if form.status not in Article.Status.values:
        raise RuleError(422, "status", "is invalid")
    with transaction.atomic():
        article = Article.objects.create(
            author=user,
            slug=slug_for(form.title),
            title=form.title,
            description=form.description,
            body=form.body,
            status=form.status,
            published_at=django_timezone.now() if form.status == "published" else None,
        )
        set_tags(article, form.tagList)
    return article


def shared_json(article):
    return {
        "slug": article.slug,
        "title": article.title,
        "body": article.body,
        "revision": article.revision,
    }


def commit_edit(article, data, viewer=None, share=None):
    """One locked content transition for author and capability edits."""
    with transaction.atomic():
        article = Article.objects.select_for_update().select_related("author").get(pk=article.pk)
        if share is not None:
            active = Share.objects.select_for_update().filter(pk=share.pk).first()
            if not active or active.key_hash != share.key_hash:
                raise RuleError(404, "share", "not found")
        else:
            if not (article.status == "published" or article.author_id == viewer.pk):
                raise RuleError(404, "article", "not found")
            own_article(article, viewer)
        if "revision" in data:
            revision = data["revision"]
            if type(revision) is not int:
                raise RuleError(422, "revision", "is invalid")
            if revision != article.revision:
                raise RuleError(409, "revision", "is stale", article)
        form = parse(ShareEdit if share is not None else ArticleEdit, data)
        fields = form.model_fields_set
        prior_title = article.title
        for field in ("title", "description", "body"):
            if field in fields:
                value = getattr(form, field)
                if value is None:
                    raise RuleError(422, field, "is invalid")
                nonblank(value, field)
                setattr(article, field, value)
        if "tagList" in fields and form.tagList is None:
            raise RuleError(422, "tagList", "is invalid")
        if "title" in fields and article.title != prior_title:
            article.slug = slug_for(article.title)
        article.revision += 1
        article.save()
        if "tagList" in fields:
            set_tags(article, form.tagList)
        from .live import broadcast_after_commit

        transaction.on_commit(lambda: broadcast_after_commit(article.pk, shared_json(article)))
    return article


def share_for(id, key, lock=False):
    qs = Share.objects.select_related("article")
    if lock:
        qs = qs.select_for_update()
    share = qs.filter(pk=id).first()
    if (
        not share
        or not isinstance(key, str)
        or not secrets.compare_digest(share.key_hash, sha256(key.encode()).hexdigest())
    ):
        raise RuleError(404, "share", "not found")
    return share


def export_json(export):
    return {
        "id": export.pk,
        "status": export.status,
        "createdAt": export.created_at.isoformat(),
        "completedAt": export.completed_at.isoformat() if export.completed_at else None,
        "articles": export.articles,
    }


def page(qs, viewer, limit, offset):
    count = qs.count()
    rows = list(
        qs.select_related("author")
        .defer("body")
        .prefetch_related("tags")
        .annotate(favorites_count=Count("favorites", distinct=True))
        .order_by("-created_at", "-id")[offset : offset + limit]
    )
    ids = [row.pk for row in rows]
    authors = {row.author_id for row in rows}
    favorites = (
        set(
            Favorite.objects.filter(user=viewer, article_id__in=ids).values_list(
                "article_id", flat=True
            )
        )
        if viewer
        else set()
    )
    follows = (
        set(
            Follow.objects.filter(follower=viewer, followed_id__in=authors).values_list(
                "followed_id", flat=True
            )
        )
        if viewer
        else set()
    )
    return {
        "articles": [
            article_json(row, viewer, False, row.pk in favorites, row.author_id in follows)
            for row in rows
        ],
        "articlesCount": count,
    }


def article_json(article, viewer=None, body=True, favorited=None, following=None):
    if favorited is None:
        favorited = bool(viewer and Favorite.objects.filter(user=viewer, article=article).exists())
    count = getattr(article, "favorites_count", None)
    if count is None:
        count = Favorite.objects.filter(article=article).count()
    data = {
        "slug": article.slug,
        "title": article.title,
        "description": article.description,
        "tagList": [tag.name for tag in article.tags.all()],
        "createdAt": article.created_at.isoformat(),
        "updatedAt": article.updated_at.isoformat(),
        "favorited": favorited,
        "favoritesCount": count,
        "author": profile_json(article.author, viewer, following),
        "status": article.status,
        "publishedAt": article.published_at.isoformat() if article.published_at else None,
        "revision": article.revision,
    }
    if body:
        data["body"] = article.body
    return data
