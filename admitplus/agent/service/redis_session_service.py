from __future__ import annotations
import json
import logging
import time
import uuid
from typing import Any, Optional

from typing_extensions import override
from redis.asyncio import Redis

from google.adk.sessions import _session_util
from google.adk.errors.already_exists_error import AlreadyExistsError
from google.adk.sessions.base_session_service import (
    BaseSessionService,
    GetSessionConfig,
    ListSessionsResponse,
)
from google.adk.sessions.session import Session
from google.adk.sessions.state import State
from google.adk.events.event import Event

logger = logging.getLogger("google_adk." + __name__)


class RedisSessionService(BaseSessionService):
    """A Redis-based implementation of the session service.

    This implementation is suitable for production environments with support for:
    - Distributed session storage
    - High availability
    - Concurrent access
    - Optional TTL for sessions

    Args:
        redis_client: An async Redis client instance
        key_prefix: Prefix for all Redis keys (default: "adk")
        session_ttl: Optional TTL in seconds for sessions (default: None, no expiration)
    """

    # Redis key patterns
    SESSION_KEY_PATTERN = "{prefix}:sessions:{app_name}:{user_id}:{session_id}"
    USER_STATE_KEY_PATTERN = "{prefix}:user_state:{app_name}:{user_id}"
    APP_STATE_KEY_PATTERN = "{prefix}:app_state:{app_name}"
    SESSION_INDEX_PATTERN = "{prefix}:session_index:{app_name}:{user_id}"
    APP_SESSION_INDEX_PATTERN = "{prefix}:session_index:{app_name}"

    def __init__(
        self,
        redis_client: Redis,
        key_prefix: str = "adk",
        session_ttl: Optional[int] = None,
    ):
        """Initialize the Redis session service.

        Args:
            redis_client: Async Redis client instance
            key_prefix: Prefix for all Redis keys
            session_ttl: Optional TTL in seconds for sessions
        """
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.session_ttl = session_ttl

    def _get_session_key(self, app_name: str, user_id: str, session_id: str) -> str:
        """Generate Redis key for a session."""
        return self.SESSION_KEY_PATTERN.format(
            prefix=self.key_prefix,
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )

    def _get_user_state_key(self, app_name: str, user_id: str) -> str:
        """Generate Redis key for user state."""
        return self.USER_STATE_KEY_PATTERN.format(
            prefix=self.key_prefix,
            app_name=app_name,
            user_id=user_id,
        )

    def _get_app_state_key(self, app_name: str) -> str:
        """Generate Redis key for app state."""
        return self.APP_STATE_KEY_PATTERN.format(
            prefix=self.key_prefix,
            app_name=app_name,
        )

    def _get_session_index_key(self, app_name: str, user_id: str) -> str:
        """Generate Redis key for session index (set of session IDs per user)."""
        return self.SESSION_INDEX_PATTERN.format(
            prefix=self.key_prefix,
            app_name=app_name,
            user_id=user_id,
        )

    def _get_app_session_index_key(self, app_name: str) -> str:
        """Generate Redis key for app-level session index."""
        return self.APP_SESSION_INDEX_PATTERN.format(
            prefix=self.key_prefix,
            app_name=app_name,
        )

    def _serialize_session(self, session: Session) -> str:
        """Serialize a Session object to JSON string.

        Session and Event are both Pydantic BaseModels, so model_dump()
        recursively converts all nested objects (Content, EventActions, etc.)
        into plain dicts that json.dumps can handle.
        """
        return session.model_dump_json()

    def _deserialize_session(self, data: str | bytes) -> Session:
        """Deserialize a JSON string to a Session object.

        model_validate_json() reconstructs the full object graph,
        including nested Content, EventActions, etc.
        """
        return Session.model_validate_json(data)

    async def _merge_state(
        self, app_name: str, user_id: str, session: Session
    ) -> Session:
        """Merge app and user state into session state."""
        # Merge app state
        app_state_key = self._get_app_state_key(app_name)
        app_state = await self.redis.hgetall(app_state_key)
        if app_state:
            for key, value in app_state.items():
                key_str = key.decode("utf-8") if isinstance(key, bytes) else key
                value_obj = json.loads(
                    value.decode("utf-8") if isinstance(value, bytes) else value
                )
                session.state[State.APP_PREFIX + key_str] = value_obj

        # Merge user state
        user_state_key = self._get_user_state_key(app_name, user_id)
        user_state = await self.redis.hgetall(user_state_key)
        if user_state:
            for key, value in user_state.items():
                key_str = key.decode("utf-8") if isinstance(key, bytes) else key
                value_obj = json.loads(
                    value.decode("utf-8") if isinstance(value, bytes) else value
                )
                session.state[State.USER_PREFIX + key_str] = value_obj

        return session

    @override
    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        """Create a new session in Redis."""
        # Generate or validate session ID
        if session_id:
            session_id = session_id.strip()
            # Check if session already exists
            session_key = self._get_session_key(app_name, user_id, session_id)
            exists = await self.redis.exists(session_key)
            if exists:
                raise AlreadyExistsError(
                    f"Session with id {session_id} already exists."
                )
        else:
            session_id = str(uuid.uuid4())

        # Extract state deltas
        state_deltas = _session_util.extract_state_delta(state)
        app_state_delta = state_deltas["app"]
        user_state_delta = state_deltas["user"]
        session_state = state_deltas["session"]

        # Use Redis pipeline for atomic operations
        async with self.redis.pipeline(transaction=True) as pipe:
            # Update app state
            if app_state_delta:
                app_state_key = self._get_app_state_key(app_name)
                for key, value in app_state_delta.items():
                    await pipe.hset(app_state_key, key, json.dumps(value))

            # Update user state
            if user_state_delta:
                user_state_key = self._get_user_state_key(app_name, user_id)
                for key, value in user_state_delta.items():
                    await pipe.hset(user_state_key, key, json.dumps(value))

            # Create session
            session = Session(
                app_name=app_name,
                user_id=user_id,
                id=session_id,
                state=session_state or {},
                last_update_time=time.time(),
            )

            session_key = self._get_session_key(app_name, user_id, session_id)
            await pipe.set(session_key, self._serialize_session(session))

            # Set TTL if configured
            if self.session_ttl:
                await pipe.expire(session_key, self.session_ttl)

            # Add to session indexes
            session_index_key = self._get_session_index_key(app_name, user_id)
            await pipe.sadd(session_index_key, session_id)

            app_session_index_key = self._get_app_session_index_key(app_name)
            await pipe.sadd(app_session_index_key, f"{user_id}:{session_id}")

            await pipe.execute()

        # Merge state and return
        return await self._merge_state(app_name, user_id, session)

    @override
    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        """Retrieve a session from Redis."""
        session_key = self._get_session_key(app_name, user_id, session_id)
        session_data = await self.redis.get(session_key)

        if not session_data:
            return None

        session = self._deserialize_session(session_data)

        # Apply event filtering based on config
        if config:
            if config.num_recent_events:
                session.events = session.events[-config.num_recent_events :]
            if config.after_timestamp:
                i = len(session.events) - 1
                while i >= 0:
                    if session.events[i].timestamp < config.after_timestamp:
                        break
                    i -= 1
                if i >= 0:
                    session.events = session.events[i + 1 :]

        # Merge state and return
        return await self._merge_state(app_name, user_id, session)

    @override
    async def list_sessions(
        self, *, app_name: str, user_id: Optional[str] = None
    ) -> ListSessionsResponse:
        """List all sessions for an app or user."""
        sessions_without_events = []

        if user_id is None:
            # List all sessions for the app
            app_session_index_key = self._get_app_session_index_key(app_name)
            session_refs = await self.redis.smembers(app_session_index_key)

            for session_ref in session_refs:
                session_ref_str = (
                    session_ref.decode("utf-8")
                    if isinstance(session_ref, bytes)
                    else session_ref
                )
                user_id_part, session_id_part = session_ref_str.split(":", 1)

                session_key = self._get_session_key(
                    app_name, user_id_part, session_id_part
                )
                session_data = await self.redis.get(session_key)

                if session_data:
                    session = self._deserialize_session(session_data)
                    session.events = []  # Remove events for listing
                    session = await self._merge_state(app_name, user_id_part, session)
                    sessions_without_events.append(session)
        else:
            # List sessions for specific user
            session_index_key = self._get_session_index_key(app_name, user_id)
            session_ids = await self.redis.smembers(session_index_key)

            for session_id in session_ids:
                session_id_str = (
                    session_id.decode("utf-8")
                    if isinstance(session_id, bytes)
                    else session_id
                )
                session_key = self._get_session_key(app_name, user_id, session_id_str)
                session_data = await self.redis.get(session_key)

                if session_data:
                    session = self._deserialize_session(session_data)
                    session.events = []  # Remove events for listing
                    session = await self._merge_state(app_name, user_id, session)
                    sessions_without_events.append(session)

        return ListSessionsResponse(sessions=sessions_without_events)

    @override
    async def delete_session(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        """Delete a session from Redis."""
        session_key = self._get_session_key(app_name, user_id, session_id)

        # Check if session exists
        exists = await self.redis.exists(session_key)
        if not exists:
            return

        async with self.redis.pipeline(transaction=True) as pipe:
            # Delete session
            await pipe.delete(session_key)

            # Remove from indexes
            session_index_key = self._get_session_index_key(app_name, user_id)
            await pipe.srem(session_index_key, session_id)

            app_session_index_key = self._get_app_session_index_key(app_name)
            await pipe.srem(app_session_index_key, f"{user_id}:{session_id}")

            await pipe.execute()

    @override
    async def append_event(self, session: Session, event: Event) -> Event:
        """Append an event to a session in Redis."""
        if event.partial:
            return event

        app_name = session.app_name
        user_id = session.user_id
        session_id = session.id

        def _warning(message: str) -> None:
            logger.warning(f"Failed to append event to session {session_id}: {message}")

        session_key = self._get_session_key(app_name, user_id, session_id)

        # Check if session exists
        session_data = await self.redis.get(session_key)
        if not session_data:
            _warning(f"session not found in Redis")
            return event

        # Update the in-memory session (for current request)
        await super().append_event(session=session, event=event)
        session.last_update_time = event.timestamp

        # Retrieve current session from Redis
        storage_session = self._deserialize_session(session_data)
        storage_session.events.append(event)
        storage_session.last_update_time = event.timestamp

        # Handle state delta if present
        if event.actions and event.actions.state_delta:
            state_deltas = _session_util.extract_state_delta(event.actions.state_delta)
            app_state_delta = state_deltas["app"]
            user_state_delta = state_deltas["user"]
            session_state_delta = state_deltas["session"]

            async with self.redis.pipeline(transaction=True) as pipe:
                # Update app state
                if app_state_delta:
                    app_state_key = self._get_app_state_key(app_name)
                    for key, value in app_state_delta.items():
                        await pipe.hset(app_state_key, key, json.dumps(value))

                # Update user state
                if user_state_delta:
                    user_state_key = self._get_user_state_key(app_name, user_id)
                    for key, value in user_state_delta.items():
                        await pipe.hset(user_state_key, key, json.dumps(value))

                # Update session state
                if session_state_delta:
                    storage_session.state.update(session_state_delta)

                # Save updated session
                await pipe.set(session_key, self._serialize_session(storage_session))

                # Refresh TTL if configured
                if self.session_ttl:
                    await pipe.expire(session_key, self.session_ttl)

                await pipe.execute()

        else:
            # Just update the session without state changes
            await self.redis.set(session_key, self._serialize_session(storage_session))
            if self.session_ttl:
                await self.redis.expire(session_key, self.session_ttl)

        return event

    async def close(self) -> None:
        """Close the Redis connection."""
        await self.redis.close()

    async def ping(self) -> bool:
        """Check if Redis connection is alive."""
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    async def clear_all_sessions(self, app_name: str) -> int:
        """Clear all sessions for an app. Useful for testing/cleanup.

        Args:
            app_name: The application name

        Returns:
            Number of sessions deleted
        """
        pattern = f"{self.key_prefix}:sessions:{app_name}:*"
        cursor = 0
        deleted_count = 0

        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                deleted_count += await self.redis.delete(*keys)
            if cursor == 0:
                break

        # Clear indexes
        app_session_index_key = self._get_app_session_index_key(app_name)
        await self.redis.delete(app_session_index_key)

        # Clear user session indexes
        user_index_pattern = f"{self.key_prefix}:session_index:{app_name}:*"
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor, match=user_index_pattern, count=100
            )
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break

        return deleted_count
