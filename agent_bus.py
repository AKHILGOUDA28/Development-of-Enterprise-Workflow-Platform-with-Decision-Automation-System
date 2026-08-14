"""
agent_bus.py
------------
Agent Communication Event Bus.

Implements a simple publish-subscribe system for inter-agent messaging.
Agents publish events when they complete work; other agents (or the API)
can subscribe to event types or retrieve all events for a session.

Usage:
    from agent_bus import bus

    bus.publish("planner", "plan_ready", {"plan": "..."}, session_id="abc")
    events = bus.get_events(session_id="abc")
"""

import uuid
import json
from datetime import datetime, timezone
from threading import Lock
from typing import Callable, Dict, List, Optional


class AgentEvent:
    """Represents a single inter-agent communication event."""

    def __init__(
        self,
        publisher: str,
        event_type: str,
        payload: dict,
        session_id: str = "global"
    ):
        self.event_id   = str(uuid.uuid4())[:8].upper()
        self.publisher  = publisher
        self.event_type = event_type
        self.payload    = payload
        self.session_id = session_id
        self.timestamp  = datetime.now(timezone.utc).isoformat() + "Z"

    def to_dict(self) -> dict:
        return {
            "event_id":   self.event_id,
            "publisher":  self.publisher,
            "event_type": self.event_type,
            "payload":    self.payload,
            "session_id": self.session_id,
            "timestamp":  self.timestamp,
        }


class AgentEventBus:
    """
    Thread-safe publish-subscribe event bus for agent coordination.

    Maintains an in-memory event log (capped at MAX_EVENTS per session)
    and supports subscription callbacks for real-time event handling.
    """

    MAX_EVENTS_PER_SESSION = 200

    def __init__(self):
        self._lock        = Lock()
        self._events: Dict[str, List[AgentEvent]] = {}   # session_id → events
        self._subscribers: Dict[str, List[Callable]]     = {}  # event_type → handlers
        self._global_events: List[AgentEvent]            = []

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------
    def publish(
        self,
        publisher: str,
        event_type: str,
        payload: dict,
        session_id: str = "global"
    ) -> AgentEvent:
        """
        Publishes an event from an agent.

        Args:
            publisher:  Name of the publishing agent (e.g. 'planner', 'researcher')
            event_type: Semantic type of the event (e.g. 'plan_ready', 'tool_called')
            payload:    Dict of event data
            session_id: Current request/session identifier

        Returns:
            The created AgentEvent instance.
        """
        event = AgentEvent(publisher, event_type, payload, session_id)

        # Persist event in DB for production auditing
        try:
            from database.connection import db_manager
            db_manager.execute("""
                INSERT INTO agent_events (session_id, publisher, event_type, payload, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, publisher, event_type, json.dumps(payload), event.timestamp))
        except Exception as db_err:
            pass

        with self._lock:
            # Per-session log
            if session_id not in self._events:
                self._events[session_id] = []
            session_log = self._events[session_id]
            session_log.append(event)
            # Cap per session
            if len(session_log) > self.MAX_EVENTS_PER_SESSION:
                self._events[session_id] = session_log[-self.MAX_EVENTS_PER_SESSION:]

            # Global log (across all sessions, capped at 1000)
            self._global_events.append(event)
            if len(self._global_events) > 1000:
                self._global_events = self._global_events[-1000:]

        # Notify subscribers (outside lock to avoid deadlocks)
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass  # Subscriber errors must not crash the bus

        return event

    # ------------------------------------------------------------------
    # Subscribing
    # ------------------------------------------------------------------
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Registers a callback for a specific event type.

        Args:
            event_type: The event type to listen for (e.g., 'plan_ready')
            handler:    Callable that receives an AgentEvent
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Removes a previously registered handler."""
        with self._lock:
            if event_type in self._subscribers:
                self._subscribers[event_type] = [
                    h for h in self._subscribers[event_type] if h is not handler
                ]

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def get_events(
        self,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50
    ) -> List[dict]:
        """
        Returns events as a list of dicts.

        Args:
            session_id: Filter to a specific session (None = all sessions)
            event_type: Filter to a specific event type (None = all types)
            limit:      Maximum number of events to return (most recent first)
        """
        with self._lock:
            if session_id:
                source = self._events.get(session_id, [])
            else:
                source = self._global_events

            if event_type:
                source = [e for e in source if e.event_type == event_type]

            return [e.to_dict() for e in reversed(source[-limit:])]

    def get_all_sessions(self) -> List[str]:
        """Returns all session IDs that have events."""
        with self._lock:
            return list(self._events.keys())

    def clear_session(self, session_id: str) -> None:
        """Removes all events for a given session."""
        with self._lock:
            self._events.pop(session_id, None)

    def get_stats(self) -> dict:
        """Returns summary statistics about the event bus."""
        with self._lock:
            total = len(self._global_events)
            sessions = len(self._events)
            type_counts: Dict[str, int] = {}
            for ev in self._global_events:
                type_counts[ev.event_type] = type_counts.get(ev.event_type, 0) + 1
            return {
                "total_events": total,
                "active_sessions": sessions,
                "event_type_breakdown": type_counts,
            }


# ---------------------------------------------------------------------------
# Global singleton — import and use across the app
# ---------------------------------------------------------------------------
bus = AgentEventBus()
