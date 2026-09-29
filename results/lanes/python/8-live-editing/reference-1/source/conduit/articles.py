import json
from typing import Any

from django.db import transaction
from ninja import Router, Schema
from pydantic import Field

from .accounts import profile_data, required_user, viewer
from .http import APIError, PageOffset, PageSize, require_value
from .models import Article, Comment, EditingLink, followed_author
from .sharing import article_changed, revoke_after_commit

router = Router()


def article_data(article, current=None, *, summary=False):
    favorited = getattr(article, "is_favorited", None)
    if favorited is None:
        favorited = bool(current and article.favorites.filter(pk=current.pk).exists())
    favorites_count = getattr(article, "favorites_count", None)
    if favorites_count is None:
        favorites_count = article.favorites.count()
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
        "favorited": favorited,
        "favoritesCount": favorites_count,
        "author": profile_data(
            article.author, current, following=getattr(article, "author_followed", None)
        ),
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
        "author": profile_data(
            comment.author, current, following=getattr(comment, "author_followed", None)
        ),
    }


def article_or_404(slug, current=None, *, lock=False, with_viewer=False):
    articles = Article.objects.select_related("author")
    if lock:
        articles = articles.select_for_update(of=("self",))
    if with_viewer:
        articles = articles.with_viewer(current)
    article = articles.filter(slug=slug).first()
    if article is None or (
        article.status == Article.Status.DRAFT and article.author_id != getattr(current, "pk", None)
    ):
        raise APIError(404, "article", "not found")
    return article


def require_published(article):
    if article.status == Article.Status.DRAFT:
        raise APIError(422, "article", "is a draft")


def owned(resource, user, name):
    if resource.author_id != user.pk:
        raise APIError(403, name, "forbidden")


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


class CommentInput(Schema):
    body: str


class CommentInputBody(Schema):
    comment: CommentInput


@router.get("/articles")
def list_articles(
    request,
    tag: str = None,
    author: str = None,
    favorited: str = None,
    limit: PageSize = 20,
    offset: PageOffset = 0,
):
    articles = Article.objects.published().select_related("author")
    if tag:
        articles = articles.filter(tags__contains=[tag])
    if author:
        articles = articles.filter(author__username=author)
    if favorited:
        articles = articles.filter(
            pk__in=Article.favorites.through.objects.filter(user__username=favorited).values(
                "article_id"
            )
        )
    return article_page(articles, viewer(request), limit, offset)


@router.get("/articles/feed", auth=required_user)
def feed(
    request,
    limit: PageSize = 20,
    offset: PageOffset = 0,
):
    articles = (
        Article.objects.published().select_related("author").filter(author__followers=request.auth)
    )
    return article_page(articles, request.auth, limit, offset)


@router.get("/user/drafts", auth=required_user)
def user_drafts(
    request,
    limit: PageSize = 20,
    offset: PageOffset = 0,
):
    articles = Article.objects.select_related("author").filter(
        author=request.auth, status=Article.Status.DRAFT
    )
    return article_page(articles, request.auth, limit, offset)


def article_page(articles, current, limit, offset):
    count = articles.count()
    page = articles.with_viewer(current).defer("body")[offset : offset + limit]
    return {
        "articles": [article_data(article, current, summary=True) for article in page],
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
    return {"article": article_data(article_or_404(slug, current, with_viewer=True), current)}


@router.put("/articles/{slug}", auth=required_user)
def update_article(request, slug: str):
    with transaction.atomic():
        article = article_or_404(slug, request.auth, lock=True)
        owned(article, request.auth, "article")
        try:
            payload = json.loads(request.body)
        except ValueError, UnicodeDecodeError:
            raise APIError(422, "article", "is invalid") from None
        if not isinstance(payload, dict) or not isinstance(payload.get("article"), dict):
            raise APIError(422, "article", "is invalid")
        data = ArticleChanges.model_validate(payload["article"]).model_dump(exclude_unset=True)
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
        article_changed(article)
    return {"article": article_data(article, request.auth)}


@router.delete("/articles/{slug}", auth=required_user, response={204: None})
def delete_article(request, slug: str):
    article = article_or_404(slug, request.auth)
    owned(article, request.auth, "article")
    with transaction.atomic():
        share_id = EditingLink.objects.filter(article=article).values_list("pk", flat=True).first()
        article.delete()
        revoke_after_commit(share_id)
    return 204, None


@router.post("/articles/{slug}/publish", auth=required_user)
def publish_article(request, slug: str):
    with transaction.atomic():
        article = article_or_404(slug, request.auth, lock=True)
        owned(article, request.auth, "article")
        revision = article.revision
        article.publish()
        if article.revision != revision:
            article_changed(article)
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
    comments = article.comments.select_related("author").order_by("id")
    if current:
        comments = comments.annotate(author_followed=followed_author(current))
    return {"comments": [comment_data(comment, current) for comment in comments]}


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
