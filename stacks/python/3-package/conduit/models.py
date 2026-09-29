from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(null=True, blank=True)
    image = models.URLField(null=True, blank=True)
    following = models.ManyToManyField(
        "self", symmetrical=False, related_name="followers", blank=True
    )


class ArticleQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Article.Status.PUBLISHED)


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


class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
