from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from procrastinate.contrib.django import app

from .models import Article, Export


@app.task
@transaction.atomic
def build_export(export_id):
    export = Export.objects.select_for_update().get(pk=export_id)
    if export.status == "done":
        return
    rows = (
        Article.objects.filter(author=export.user)
        .prefetch_related("tags")
        .annotate(comments_count=Count("comments"))
        .order_by("created_at", "pk")
    )
    export.articles = [
        {
            "slug": row.slug,
            "title": row.title,
            "description": row.description,
            "body": row.body,
            "tagList": [tag.name for tag in row.tags.all()],
            "status": row.status,
            "commentsCount": row.comments_count,
        }
        for row in rows
    ]
    export.status = "done"
    export.completed_at = timezone.now()
    export.save(update_fields=["articles", "status", "completed_at"])
