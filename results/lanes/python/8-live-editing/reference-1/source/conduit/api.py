from .accounts import router as accounts
from .articles import router as articles
from .exports import router as exports
from .http import api
from .sharing import router as sharing


@api.get("/health")
def health(request):
    return {"status": "ok"}


api.add_router("/api/", accounts)
api.add_router("/api/", articles)
api.add_router("/api/", exports)
api.add_router("/api/", sharing)
