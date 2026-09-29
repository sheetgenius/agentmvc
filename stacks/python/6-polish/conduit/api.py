from .accounts import router as accounts
from .articles import router as articles
from .http import api


@api.get("/health")
def health(request):
    return {"status": "ok"}


api.add_router("/api/", accounts)
api.add_router("/api/", articles)
