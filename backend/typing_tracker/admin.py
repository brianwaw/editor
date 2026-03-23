from django.contrib import admin
from .models import TypingSession


@admin.register(TypingSession)
class TypingSessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "user", "language", "is_flagged", "burst_count", "requires_human_review", "started_at")
    list_filter = ("is_flagged", "requires_human_review", "language")
    search_fields = ("user__username", "session_id")
    readonly_fields = ("session_id", "started_at", "last_event_at")
