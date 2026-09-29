from typing import Annotated

from ninja import NinjaAPI, Query
from ninja.errors import ValidationError

api = NinjaAPI(docs_url=None, openapi_url=None)
PageSize = Annotated[int, Query(ge=0, le=1000)]
PageOffset = Annotated[int, Query(ge=0, le=2_147_483_647)]


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
