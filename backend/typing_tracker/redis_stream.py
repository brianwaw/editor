"""
Redis Stream helpers for typing_tracker.

Stream key:  track:<session_id>
Each entry:  a JSON-encoded op stored in the 'data' field.
TTL:         30 days (refreshed on every append).

These functions use aioredis (bundled with channels-redis / redis-py ≥ 4.2).
"""

import json
import logging

from channels.layers import get_channel_layer
from django.conf import settings
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_REDIS_URL = getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0")
_STREAM_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days
_MAX_STREAM_LEN = 50_000                  # safety cap per session


def _stream_key(session_id: str) -> str:
    return f"track:{session_id}"


async def _get_redis() -> aioredis.Redis:
    """Return an async Redis client (no connection pooling needed for ASGI)."""
    return await aioredis.from_url(_REDIS_URL, decode_responses=True)


async def append_ops_to_stream(session_id: str, ops: list[dict]) -> None:
    """
    Append a list of op dicts to the Redis Stream for this session.
    Each op is stored as a single 'data' field containing JSON.
    Also refreshes the 30-day TTL on the stream key.
    """
    key = _stream_key(session_id)
    try:
        r = await _get_redis()
        pipe = r.pipeline(transaction=False)
        for op in ops:
            pipe.xadd(key, {"data": json.dumps(op)}, maxlen=_MAX_STREAM_LEN, approximate=True)
        pipe.expire(key, _STREAM_TTL_SECONDS)
        await pipe.execute()
        await r.aclose()
    except Exception:
        logger.exception("Failed to append ops to Redis stream %s", key)


async def read_all_ops_from_stream(session_id: str) -> list[dict]:
    """
    Read the entire op history for a session from the Redis Stream.
    Returns a list of op dicts in chronological order.
    """
    key = _stream_key(session_id)
    try:
        r = await _get_redis()
        entries = await r.xrange(key, "-", "+")
        await r.aclose()
        ops = []
        for _entry_id, fields in entries:
            try:
                ops.append(json.loads(fields["data"]))
            except (KeyError, json.JSONDecodeError):
                pass
        return ops
    except Exception:
        logger.exception("Failed to read ops from Redis stream %s", key)
        return []


async def delete_stream(session_id: str) -> None:
    """Delete the Redis Stream after the session has been persisted to Postgres."""
    key = _stream_key(session_id)
    try:
        r = await _get_redis()
        await r.delete(key)
        await r.aclose()
    except Exception:
        logger.exception("Failed to delete Redis stream %s", key)
