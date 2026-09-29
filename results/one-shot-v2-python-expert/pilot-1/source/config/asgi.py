import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import re_path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django_application = get_asgi_application()
from conduit.live import ShareConsumer  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_application,
        "websocket": URLRouter(
            [re_path(r"^api/shares/(?P<share_id>[A-Za-z0-9_-]+)/live$", ShareConsumer.as_asgi())]
        ),
    }
)
