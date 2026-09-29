from django.db import transaction
from ninja import Router

from .accounts import required_user
from .http import APIError
from .models import Export
from .tasks import build_export

router = Router()


def export_data(export):
    return {
        "id": export.pk,
        "status": export.status,
        "createdAt": export.created_at,
        "completedAt": export.completed_at,
        "articles": export.articles,
    }


@router.post("/user/exports", auth=required_user, response={202: dict})
def create_export(request):
    with transaction.atomic():
        export = Export.objects.create(user=request.auth)
        build_export.defer(export_id=export.pk)
        response = {"export": export_data(export)}
    return 202, response


@router.get("/user/exports/{export_id}", auth=required_user)
def get_export(request, export_id: str):
    try:
        export = Export.objects.get(pk=int(export_id), user=request.auth)
    except ValueError, OverflowError, Export.DoesNotExist:
        raise APIError(404, "export", "not found") from None
    return {"export": export_data(export)}
