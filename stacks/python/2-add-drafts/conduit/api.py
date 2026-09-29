from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from django.conf import settings
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction
from ninja import NinjaAPI, Router, Schema
from ninja.errors import ValidationError
from pydantic import Field

from .models import Article, Comment, User

api = NinjaAPI(docs_url=None, openapi_url=None)
router = Router()


class APIError(Exception):
    def __init__(self, status, field, message, **data):
        self.status = status
        self.field = field
        self.message = message
        self.data = data


@api.exception_handler(APIError)
def api_error(request, exc):
    return api.create_response(
        request, {"errors": {exc.field: [exc.message]}, **exc.data}, status=exc.status
    )


@api.exception_handler(ValidationError)
def validation_error(request, exc):
    errors = {}
    for item in exc.errors:
        field = str(item["loc"][-1])
        errors.setdefault(field, []).append(
            "can't be blank" if item["type"] == "missing" else "is invalid"
        )
    return api.create_response(request, {"errors": errors}, status=422)


def require_value(field, value):
    if not isinstance(value, str) or not value.strip():
        raise APIError(422, field, "can't be blank")
    return value


def password(value):
    require_value("password", value)
    if len(value) < 8:
        raise APIError(422, "password", "is too short")
    return value


def validate_identity(data):
    for field, validator in (("username", UnicodeUsernameValidator()), ("email", validate_email)):
        if field in data:
            require_value(field, data[field])
            try:
                validator(data[field])
            except DjangoValidationError:
                raise APIError(422, field, "is invalid") from None
            if field == "email":
                data[field] = User.objects.normalize_email(data[field])


def unique_user(data, exclude=None):
    for field in ("username", "email"):
        if field in data:
            users = User.objects.filter(**{field: data[field]})
            if exclude:
                users = users.exclude(pk=exclude.pk)
            if users.exists():
                raise APIError(409, field, "has already been taken")


def token_for(user):
    claims = {"sub": str(user.pk), "exp": datetime.now(UTC) + timedelta(days=30)}
    return jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")


def viewer(request):
    header = request.headers.get("Authorization", "")
    if not header:
        return None
    try:
        scheme, token = header.split(" ", 1)
        if scheme != "Token":
            raise ValueError
        claims = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return User.objects.get(pk=claims["sub"])
    except ValueError, jwt.InvalidTokenError, User.DoesNotExist, KeyError:
        raise APIError(401, "token", "is invalid") from None


def required_user(request):
    user = viewer(request)
    if user is None:
        raise APIError(401, "token", "is missing")
    return user


def user_data(user):
    return {
        "email": user.email,
        "token": token_for(user),
        "username": user.username,
        "bio": user.bio,
        "image": user.image,
    }


def profile_data(user, current=None):
    return {
        "username": user.username,
        "bio": user.bio,
        "image": user.image,
        "following": bool(current and current.following.filter(pk=user.pk).exists()),
    }


def article_data(article, current=None, *, summary=False):
    data = {
        "slug": article.slug,
        "title": article.title,
        "description": article.description,
        "tagList": article.tags,
        "createdAt": article.created_at,
        "updatedAt": article.updated_at,
        "status": article.status,
        "publishedAt": article.published_at,
        "revision": article.revision,
        "favorited": bool(current and article.favorites.filter(pk=current.pk).exists()),
        "favoritesCount": article.favorites.count(),
        "author": profile_data(article.author, current),
    }
    if not summary:
        data["body"] = article.body
    return data


def comment_data(comment, current=None):
    return {
        "id": comment.pk,
        "createdAt": comment.created_at,
        "updatedAt": comment.updated_at,
        "body": comment.body,
        "author": profile_data(comment.author, current),
    }


def article_or_404(slug, current=None, *, lock=False):
    articles = Article.objects.select_related("author")
    if lock:
        articles = articles.select_for_update(of=("self",))
    article = articles.filter(slug=slug).first()
    if article is None or (
        article.status == Article.Status.DRAFT and article.author_id != getattr(current, "pk", None)
    ):
        raise APIError(404, "article", "not found")
    return article


def require_published(article):
    if article.status == Article.Status.DRAFT:
        raise APIError(422, "article", "is a draft")


def profile_or_404(username):
    user = User.objects.filter(username=username).first()
    if user is None:
        raise APIError(404, "profile", "not found")
    return user


def owned(resource, user, name):
    if resource.author_id != user.pk:
        raise APIError(403, name, "forbidden")


class Registration(Schema):
    username: str
    email: str
    password: str


class RegistrationBody(Schema):
    user: Registration


class Login(Schema):
    email: str
    password: str


class LoginBody(Schema):
    user: Login


class UserChanges(Schema):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    bio: str | None = None
    image: str | None = None


class UserChangesBody(Schema):
    user: UserChanges


class ArticleInput(Schema):
    title: str
    description: str
    body: str
    tagList: list[str] = Field(default_factory=list)
    status: str = Article.Status.PUBLISHED


class ArticleInputBody(Schema):
    article: ArticleInput


class ArticleChanges(Schema):
    title: Any = None
    description: Any = None
    body: Any = None
    tagList: Any = None
    revision: Any = None


class ArticleChangesBody(Schema):
    article: ArticleChanges


class CommentInput(Schema):
    body: str


class CommentInputBody(Schema):
    comment: CommentInput


@api.get("/health")
def health(request):
    return {"status": "ok"}


@router.post("/users", response={201: dict})
def register(request, payload: RegistrationBody):
    data = payload.user.model_dump()
    validate_identity(data)
    password(data["password"])
    unique_user(data)
    user = User.objects.create_user(**data)
    return 201, {"user": user_data(user)}


@router.post("/users/login")
def login(request, payload: LoginBody):
    data = payload.user
    require_value("email", data.email)
    require_value("password", data.password)
    user = User.objects.filter(email=User.objects.normalize_email(data.email)).first()
    if user is None or not user.check_password(data.password):
        raise APIError(401, "credentials", "invalid")
    return {"user": user_data(user)}


@router.get("/user", auth=required_user)
def current_user(request):
    return {"user": user_data(request.auth)}


@router.put("/user", auth=required_user)
def update_user(request, payload: UserChangesBody):
    user = request.auth
    data = payload.user.model_dump(exclude_unset=True)
    validate_identity(data)
    new_password = None
    if "password" in data:
        new_password = data.pop("password")
        password(new_password)
    unique_user(data, user)
    for field, value in data.items():
        if field in ("bio", "image") and not value:
            value = None
        setattr(user, field, value)
    if new_password is not None:
        user.set_password(new_password)
    user.save()
    return {"user": user_data(user)}


@router.get("/profiles/{username}")
def get_profile(request, username: str):
    return {"profile": profile_data(profile_or_404(username), viewer(request))}


@router.post("/profiles/{username}/follow", auth=required_user)
def follow(request, username: str):
    target = profile_or_404(username)
    request.auth.following.add(target)
    return {"profile": profile_data(target, request.auth)}


@router.delete("/profiles/{username}/follow", auth=required_user)
def unfollow(request, username: str):
    target = profile_or_404(username)
    request.auth.following.remove(target)
    return {"profile": profile_data(target, request.auth)}


@router.get("/articles")
def list_articles(
    request,
    tag: str = None,
    author: str = None,
    favorited: str = None,
    limit: int = 20,
    offset: int = 0,
):
    articles = Article.objects.published().select_related("author")
    if tag:
        articles = articles.filter(tags__contains=[tag])
    if author:
        articles = articles.filter(author__username=author)
    if favorited:
        articles = articles.filter(favorites__username=favorited)
    return article_page(articles, viewer(request), limit, offset)


@router.get("/articles/feed", auth=required_user)
def feed(request, limit: int = 20, offset: int = 0):
    articles = (
        Article.objects.published().select_related("author").filter(author__followers=request.auth)
    )
    return article_page(articles, request.auth, limit, offset)


@router.get("/user/drafts", auth=required_user)
def user_drafts(request, limit: int = 20, offset: int = 0):
    articles = Article.objects.select_related("author").filter(
        author=request.auth, status=Article.Status.DRAFT
    )
    return article_page(articles, request.auth, limit, offset)


def article_page(articles, current, limit, offset):
    count = articles.count()
    start = max(offset, 0)
    return {
        "articles": [
            article_data(article, current, summary=True)
            for article in articles[start : start + max(limit, 0)]
        ],
        "articlesCount": count,
    }


@router.post("/articles", auth=required_user, response={201: dict})
def create_article(request, payload: ArticleInputBody):
    data = payload.article.model_dump()
    for field in ("title", "description", "body"):
        require_value(field, data[field])
    if data["status"] not in Article.Status.values:
        raise APIError(422, "status", "is invalid")
    tags = data.pop("tagList")
    article = Article(author=request.auth, tags=tags, **data)
    if article.status == Article.Status.DRAFT:
        article.published_at = None
    article.set_title(data["title"])
    article.save()
    return 201, {"article": article_data(article, request.auth)}


@router.get("/articles/{slug}")
def get_article(request, slug: str):
    current = viewer(request)
    return {"article": article_data(article_or_404(slug, current), current)}


@router.put("/articles/{slug}", auth=required_user)
def update_article(request, slug: str, payload: ArticleChangesBody):
    with transaction.atomic():
        article = article_or_404(slug, request.auth, lock=True)
        owned(article, request.auth, "article")
        data = payload.article.model_dump(exclude_unset=True)
        if "revision" in data:
            revision = data.pop("revision")
            if type(revision) is not int:
                raise APIError(422, "revision", "is invalid")
            if revision != article.revision:
                raise APIError(
                    409, "revision", "is stale", article=article_data(article, request.auth)
                )
        for field in ("title", "description", "body"):
            if field in data:
                if data[field] is not None and not isinstance(data[field], str):
                    raise APIError(422, field, "is invalid")
                require_value(field, data[field])
        if "tagList" in data:
            if not isinstance(data["tagList"], list) or not all(
                isinstance(tag, str) for tag in data["tagList"]
            ):
                raise APIError(422, "tagList", "is invalid")
            article.tags = data.pop("tagList")
        if "title" in data:
            article.set_title(data.pop("title"))
        for field, value in data.items():
            setattr(article, field, value)
        article.revision += 1
        article.save()
    return {"article": article_data(article, request.auth)}


@router.delete("/articles/{slug}", auth=required_user, response={204: None})
def delete_article(request, slug: str):
    article = article_or_404(slug, request.auth)
    owned(article, request.auth, "article")
    article.delete()
    return 204, None


@router.post("/articles/{slug}/publish", auth=required_user)
def publish_article(request, slug: str):
    with transaction.atomic():
        article = article_or_404(slug, request.auth, lock=True)
        owned(article, request.auth, "article")
        article.publish()
    return {"article": article_data(article, request.auth)}


@router.post("/articles/{slug}/favorite", auth=required_user)
def favorite(request, slug: str):
    article = article_or_404(slug, request.auth)
    require_published(article)
    article.favorites.add(request.auth)
    return {"article": article_data(article, request.auth)}


@router.delete("/articles/{slug}/favorite", auth=required_user)
def unfavorite(request, slug: str):
    article = article_or_404(slug, request.auth)
    require_published(article)
    article.favorites.remove(request.auth)
    return {"article": article_data(article, request.auth)}


@router.get("/articles/{slug}/comments")
def list_comments(request, slug: str):
    current = viewer(request)
    article = article_or_404(slug, current)
    return {
        "comments": [
            comment_data(c, current)
            for c in article.comments.select_related("author").order_by("id")
        ]
    }


@router.post("/articles/{slug}/comments", auth=required_user, response={201: dict})
def create_comment(request, slug: str, payload: CommentInputBody):
    article = article_or_404(slug, request.auth)
    require_published(article)
    body = require_value("body", payload.comment.body)
    comment = Comment.objects.create(article=article, author=request.auth, body=body)
    return 201, {"comment": comment_data(comment, request.auth)}


@router.delete("/articles/{slug}/comments/{comment_id}", auth=required_user, response={204: None})
def delete_comment(request, slug: str, comment_id: int):
    article = article_or_404(slug, request.auth)
    require_published(article)
    comment = article.comments.filter(pk=comment_id).first()
    if comment is None:
        raise APIError(404, "comment", "not found")
    owned(comment, request.auth, "comment")
    comment.delete()
    return 204, None


@router.get("/tags")
def list_tags(request):
    return {
        "tags": sorted(
            {
                tag
                for tags in Article.objects.published().values_list("tags", flat=True)
                for tag in tags
            }
        )
    }


api.add_router("/api/", router)
