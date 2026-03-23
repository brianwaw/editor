from django.urls import re_path
from .consumers import TypingConsumer

websocket_urlpatterns = [
    re_path(r"^ws/track/(?P<session_id>[^/]+)/$", TypingConsumer.as_asgi()),
]
