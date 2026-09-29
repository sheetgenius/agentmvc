from django.db import models
from django.db.models import Q


class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    bio = models.TextField(null=True)
    image = models.TextField(null=True)
    token_version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~Q(username=""), name="username_not_empty"),
            models.CheckConstraint(condition=~Q(email=""), name="email_not_empty"),
        ]


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following_links")
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name="follower_links")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "followed"], name="one_follow"),
            models.CheckConstraint(
                condition=~Q(follower=models.F("followed")), name="no_self_follow"
            ),
        ]


class ArticleQuerySet(models.QuerySet):
    def public(self):
        return self.filter(status=Article.Status.PUBLISHED)

    def visible_to(self, viewer):
        return (
            self.filter(Q(status=Article.Status.PUBLISHED) | Q(author=viewer))
            if viewer
            else self.public()
        )


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft"
        PUBLISHED = "published"

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=255, unique=True)
    title = models.TextField()
    description = models.TextField()
    body = models.TextField()
    status = models.CharField(max_length=10, choices=Status, default=Status.PUBLISHED)
    published_at = models.DateTimeField(null=True)
    revision = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = ArticleQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(status="draft", published_at__isnull=True)
                | Q(status="published", published_at__isnull=False),
                name="publication_state",
            ),
            models.CheckConstraint(condition=Q(revision__gte=1), name="positive_revision"),
            models.CheckConstraint(condition=~Q(title=""), name="title_not_empty"),
            models.CheckConstraint(condition=~Q(description=""), name="description_not_empty"),
            models.CheckConstraint(condition=~Q(body=""), name="article_body_not_empty"),
        ]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["author", "status", "-created_at"]),
        ]


class ArticleTag(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=255)
    position = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["article", "name"], name="one_article_tag"),
            models.UniqueConstraint(fields=["article", "position"], name="one_tag_position"),
        ]
        ordering = ["position"]


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="favorites")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "article"], name="one_favorite")]


class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=~Q(body=""), name="comment_body_not_empty")]


class Share(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    article = models.OneToOneField(Article, on_delete=models.CASCADE)
    key_hash = models.CharField(max_length=255)


class Export(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=7, default="pending", choices=[("pending", "pending"), ("done", "done")]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    articles = models.JSONField(null=True)


class LoginAttempt(models.Model):
    email = models.EmailField(unique=True)
    count = models.PositiveIntegerField(default=0)
