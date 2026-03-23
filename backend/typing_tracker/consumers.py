"""
TypingConsumer — WebSocket consumer for real-time edit-op tracking.

Connection URL: ws/track/<session_id>/?token=<jwt>

Message protocol (client → server):
    {type: "ops_flush",    ops: [{t, op, pos, text, len}, ...]}
    {type: "paste_event",  t, pos, text, len}
    {type: "session_end"}

Message protocol (server → client):
    {type: "ack",           accepted: <int>}
    {type: "paste_warning", message: "..."}
    {type: "error",         message: "..."}
"""

import json
import logging
import time
import uuid

import jwt
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth.models import User

from .models import TypingSession
from .redis_stream import (
    append_ops_to_stream,
    read_all_ops_from_stream,
    delete_stream,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Burst-detection constants
# ---------------------------------------------------------------------------
BURST_CHAR_THRESHOLD = 600   # characters inserted …
BURST_WINDOW_SECONDS = 3     # … within this many seconds


class TypingConsumer(AsyncWebsocketConsumer):
    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self):
        """Authenticate via JWT query param, then accept the connection."""
        query_string = self.scope.get("query_string", b"").decode()
        token = self._parse_token(query_string)

        if not token:
            await self.close(code=4001)
            return

        user = await self._authenticate(token)
        if user is None:
            await self.close(code=4001)
            return

        self.session_id = self.scope["url_route"]["kwargs"].get(
            "session_id", str(uuid.uuid4())
        )
        self.user = user

        # Create or resume the Postgres session row
        self.db_session = await self._get_or_create_session()

        # Sliding-window state for burst detection: list of (ts_seconds, char_count)
        self._recent_inserts: list[tuple[float, int]] = []
        self._last_burst_time = 0.0

        await self.accept()
        logger.info("WS connected: user=%s session=%s", user.username, self.session_id)

    async def disconnect(self, close_code):
        if hasattr(self, "db_session"):
            await self._finalise_session()
        logger.info(
            "WS disconnected: session=%s code=%s",
            getattr(self, "session_id", "?"),
            close_code,
        )

    async def receive(self, text_data):
        try:
            payload = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            await self._send_error("Invalid JSON")
            return

        msg_type = payload.get("type")
        logger.info("WS received msg_type: %s", msg_type)

        if msg_type == "ops_flush":
            await self._handle_ops_flush(payload)
        elif msg_type == "paste_event":
            await self._handle_paste_event(payload)
        elif msg_type == "session_end":
            await self._finalise_session()
            await self._send({"type": "ack", "accepted": 0})
        else:
            await self._send_error(f"Unknown message type: {msg_type!r}")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    async def _handle_ops_flush(self, payload: dict):
        """Validate and store a batch of edit ops in the Redis Stream."""
        ops = payload.get("ops")
        if not isinstance(ops, list) or len(ops) == 0:
            await self._send_error("ops_flush requires a non-empty ops list")
            return

        valid_ops = []
        for op in ops:
            if not isinstance(op, dict):
                continue
            if op.get("op") not in ("insert", "delete", "replace"):
                continue
            entry = {
                "t":    int(op.get("t",   int(time.time() * 1000))),
                "op":   op["op"],
                "pos":  int(op.get("pos",  0)),
                "text": str(op.get("text", "")),
                "len":  int(op.get("len",  0)),
            }
            valid_ops.append(entry)

            inserted_len = len(entry["text"])
            if entry["op"] in ("insert", "replace") and inserted_len > 0:
                self._record_insert(inserted_len)
                
        logger.info("Extracted %d valid ops. Appending to stream.", len(valid_ops))

        if valid_ops:
            await append_ops_to_stream(self.session_id, valid_ops)

        burst_detected = self._check_burst()
        logger.info("Burst check: %s, burst_count: %d", burst_detected, self.db_session.burst_count)
        
        if burst_detected:
            now = time.time()
            if now - self._last_burst_time > BURST_WINDOW_SECONDS:
                self._last_burst_time = now
                self.db_session.burst_count += 1
                self.db_session.is_flagged = True
                
                if self.db_session.burst_count >= 2:
                    self.db_session.requires_human_review = True
                    
                await self._save_session()
                await self._send({
                    "type": "paste_warning",
                    "message": (
                        f"Unusual typing pattern detected ({self.db_session.burst_count} time(s)). "
                        "Please ensure you are writing your own code."
                    ),
                })
            else:
                # Already warned recently, just ack
                await self._send({"type": "ack", "accepted": len(valid_ops)})
        else:
            await self._send({"type": "ack", "accepted": len(valid_ops)})

    async def _handle_paste_event(self, payload: dict):
        """Handle a dedicated paste_event (large single insert from client)."""
        op = {
            "t":    int(payload.get("t",   int(time.time() * 1000))),
            "op":   "insert",
            "pos":  int(payload.get("pos",  0)),
            "text": str(payload.get("text", "")),
            "len":  0,
        }
        
        attempted_len = payload.get("attempted_len", len(op["text"]))
        
        await append_ops_to_stream(self.session_id, [op])

        self._record_insert(attempted_len)
        
        if self._check_burst():
            now = time.time()
            if now - self._last_burst_time > BURST_WINDOW_SECONDS:
                self._last_burst_time = now
                self.db_session.burst_count += 1
                self.db_session.is_flagged = True
                
                if self.db_session.burst_count >= 2:
                    self.db_session.requires_human_review = True

                await self._save_session()
                await self._send({
                    "type": "paste_warning",
                    "message": (
                        f"Unusual typing pattern detected ({self.db_session.burst_count} time(s)). "
                        "Please ensure you are writing your own code."
                    ),
                })
            else:
                await self._send({"type": "ack", "accepted": 1})
        else:
            await self._send({"type": "ack", "accepted": 1})

    # ------------------------------------------------------------------
    # Burst detection (sliding window)
    # ------------------------------------------------------------------

    def _record_insert(self, char_count: int):
        self._recent_inserts.append((time.time(), char_count))

    def _check_burst(self) -> bool:
        """
        Returns True if ≥ BURST_CHAR_THRESHOLD chars were inserted
        within any BURST_WINDOW_SECONDS window.
        """
        now = time.time()
        cutoff = now - BURST_WINDOW_SECONDS
        self._recent_inserts = [
            (t, c) for (t, c) in self._recent_inserts if t >= cutoff
        ]
        return sum(c for (_, c) in self._recent_inserts) >= BURST_CHAR_THRESHOLD

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------

    async def _finalise_session(self):
        """Pull full op history from Redis, persist to Postgres, clean stream."""
        ops = await read_all_ops_from_stream(self.session_id)
        if ops:
            existing = self.db_session.op_snapshot or []
            existing.extend(ops)
            self.db_session.op_snapshot = existing
            await self._save_session()
        await delete_stream(self.session_id)
        logger.info(
            "Session finalised: session=%s ops=%d flagged=%s",
            self.session_id,
            len(ops),
            self.db_session.is_flagged,
        )

    # ------------------------------------------------------------------
    # DB helpers (sync → async wrappers)
    # ------------------------------------------------------------------

    @database_sync_to_async
    def _get_or_create_session(self):
        session, _ = TypingSession.objects.get_or_create(
            session_id=self.session_id,
            defaults={"user": self.user, "language": "unknown"},
        )
        if session.user_id != self.user.id:
            raise PermissionError("Session belongs to a different user.")
        return session

    @database_sync_to_async
    def _save_session(self):
        self.db_session.save()

    # ------------------------------------------------------------------
    # Auth helper
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_token(query_string: str) -> str | None:
        for part in query_string.split("&"):
            if part.startswith("token="):
                return part[len("token="):]
        return None

    @staticmethod
    @database_sync_to_async
    def _authenticate(token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return User.objects.get(id=payload["user_id"])
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Send helpers
    # ------------------------------------------------------------------

    async def _send(self, data: dict):
        await self.send(text_data=json.dumps(data))

    async def _send_error(self, message: str):
        await self._send({"type": "error", "message": message})
