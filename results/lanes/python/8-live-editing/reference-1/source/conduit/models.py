from datetime import timedelta
from hashlib import sha256
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import Count, Exists, OuterRef
from django.utils import timezone
from django.utils.text import slugify


class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(null=True, blank=True)
    image = models.URLField(null=True, blank=True)
    following = models.ManyToManyField(
        "self", symmetrical=False, related_name="followers", blank=True
    )


class LoginAttempt(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    failures = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()

    @classmethod
    def failed(cls, email):
        now = timezone.now()
        with transaction.atomic():
            attempt, _ = cls.objects.select_for_update().get_or_create(
                key=sha256(email.encode()).hexdigest(),
                defaults={"expires_at": now + timedelta(minutes=15)},
            )
            if attempt.expires_at <= now:
                attempt.failures = 0
                attempt.expires_at = now + timedelta(minutes=15)
            attempt.failures = min(attempt.failures + 1, 6)
            attempt.save(update_fields=["failures", "expires_at"])
            return attempt.failures > 5


def followed_author(viewer):
    return Exists(
        User.following.through.objects.filter(
            from_user_id=viewer.pk, to_user_id=OuterRef("author_id")
        )
    )


class ArticleQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Article.Status.PUBLISHED)

    def with_viewer(self, viewer):
        articles = self.annotate(favorites_count=Count("favorites"))
        if viewer:
            articles = articles.annotate(
                is_favorited=Exists(
                    Article.favorites.through.objects.filter(
                        article_id=OuterRef("pk"), user_id=viewer.pk
                    )
                ),
                author_followed=followed_author(viewer),
            )
        return articles


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft"
        PUBLISHED = "published"

    objects = ArticleQuerySet.as_manager()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="articles")
    slug = models.SlugField(unique=True, max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField()
    body = models.TextField()
    tags = ArrayField(models.CharField(max_length=255), default=list, blank=True)
    favorites = models.ManyToManyField(User, related_name="favorite_articles", blank=True)
    status = models.CharField(max_length=9, choices=Status, default=Status.PUBLISHED)
    published_at = models.DateTimeField(default=timezone.now, null=True)
    revision = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def set_title(self, title):
        self.title = title
        self.slug = f"{slugify(title)[:220] or 'article'}-{uuid4().hex[:12]}"

    def publish(self):
        if self.status == self.Status.DRAFT:
            self.status = self.Status.PUBLISHED
            self.published_at = timezone.now()
            self.revision += 1
            self.save()


class EditingLink(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    article = models.OneToOneField(Article, on_delete=models.CASCADE, related_name="editing_link")
    key_hash = models.CharField(max_length=64)


class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Export(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="exports")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    articles = models.JSONField(null=True)

    @property
    def status(self):
        return "done" if self.completed_at else "pending"

    def complete(self):
        if self.completed_at:
            return
        articles = (
            Article.objects.filter(author_id=self.user_id)
            .annotate(comments_count=Count("comments"))
            .order_by("created_at", "pk")
        )
        self.articles = [
            {
                "slug": article.slug,
                "title": article.title,
                "description": article.description,
                "body": article.body,
                "tagList": article.tags,
                "status": article.status,
                "commentsCount": article.comments_count,
            }
            for article in articles
        ]
        self.completed_at = timezone.now()
        self.save(update_fields=["articles", "completed_at"])
