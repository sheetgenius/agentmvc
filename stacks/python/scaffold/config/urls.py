from django.urls import path
from ninja import NinjaAPI

api = NinjaAPI(docs_url=None, openapi_url=None)


@api.get("/health")
def health(request):
    return {"status": "ok"}


urlpatterns = [path("", api.urls)]
