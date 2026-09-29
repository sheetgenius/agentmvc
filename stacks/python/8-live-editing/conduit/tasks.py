from django.db import transaction
from procrastinate.contrib.django import app

from .models import Export


@app.task
def build_export(export_id):
    with transaction.atomic():
        export = Export.objects.select_for_update().filter(pk=export_id).first()
        if export:
            export.complete()
