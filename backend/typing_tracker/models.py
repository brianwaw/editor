import uuid
from django.db import models
from django.contrib.auth.models import User


class TypingSession(models.Model):
    """
    Represents one editor session for a student.
    Detailed edit ops are stored in a Redis Stream (key: track:<session_id>)
    during the live session. On submit / session-end the full op list is
    snapshotted here in op_snapshot so instructors have a permanent record.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="typing_sessions",
    )
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    language = models.CharField(max_length=50)
    started_at = models.DateTimeField(auto_now_add=True)
    last_event_at = models.DateTimeField(auto_now=True)

    # Set to True when a suspicious paste burst is detected.
    is_flagged = models.BooleanField(default=False)

    # Count of distinct bursts (>= 600 chars in < 3s) during this session
    burst_count = models.IntegerField(default=0)

    # If this session has a high similarity score from JPlag (computed separately)
    # and burst_count >= 2, we can set this to True.
    requires_human_review = models.BooleanField(default=False)

    # Final op snapshot persisted on session-end / submit (null during live session).
    op_snapshot = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        flagged = " [FLAGGED]" if self.is_flagged else ""
        return f"Session {self.session_id} — {self.user.username} ({self.language}){flagged}"
