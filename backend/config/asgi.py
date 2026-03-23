"""
ASGI config for config project.

Handles:
  - HTTP/HTTPS  →  Django ASGI application
  - WebSocket   →  Django Channels with JWT authentication
"""

import os

import django
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Initialise Django (and the app registry) BEFORE any app-level imports.
django.setup()

# These imports must come AFTER django.setup() so the app registry is ready.
from channels.auth import AuthMiddlewareStack          # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402
from typing_tracker.routing import websocket_urlpatterns  # noqa: E402

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        ),
    }
)
