"""
Real-time Analytics Module - Live Streaming & WebSocket

Enterprise-only real-time analytics features:
- WebSocket-based live event streaming
- Real-time dashboard updates
- Live anomaly notifications
- Instant metric subscriptions
- Event-driven architecture
"""

import json
import threading
import queue
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Iterator
from datetime import datetime
from enum import Enum
import requests

try:
    import websocket
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False


# =============================================================================
# Enums & Types
# =============================================================================

class EventType(Enum):
    """Types of real-time events."""
    PROMPT_RECORDED = "PROMPT_RECORDED"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    THRESHOLD_EXCEEDED = "THRESHOLD_EXCEEDED"
    BUDGET_WARNING = "BUDGET_WARNING"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    ERROR_SPIKE = "ERROR_SPIKE"
    LATENCY_SPIKE = "LATENCY_SPIKE"
    PII_DETECTED = "PII_DETECTED"
    SESSION_STARTED = "SESSION_STARTED"
    SESSION_ENDED = "SESSION_ENDED"
    CONVERSATION_ESCALATED = "CONVERSATION_ESCALATED"
    MODEL_SWITCHED = "MODEL_SWITCHED"


@dataclass
class RealtimeEvent:
    """A real-time analytics event."""
    event_type: str
    timestamp: str
    agent_id: Optional[str] = None
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    severity: Optional[str] = None
    requires_action: bool = False


@dataclass
class MetricSnapshot:
    """Point-in-time metric snapshot."""
    metric: str
    value: float
    timestamp: str
    agent_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class EventSubscription:
    """Subscription to real-time events."""
    subscription_id: str
    event_types: List[str]
    filters: Dict[str, Any]
    created_at: str
    active: bool = True
    callback_url: Optional[str] = None


# =============================================================================
# Real-time Analytics
# =============================================================================

class RealtimeAnalytics:
    """
    Real-time analytics with live streaming.

    Provides WebSocket-based live updates for:
    - Prompt events as they happen
    - Anomaly detection alerts
    - Budget notifications
    - Metric streams

    Example:
        client = SwfteClient(api_key="sk-swfte-...")

        # Stream live events
        for event in client.analytics.realtime.stream(agent_id="agent-123"):
            print(f"{event.event_type}: {event.data}")

        # Or with callback
        def on_event(event):
            if event.event_type == "ANOMALY_DETECTED":
                send_alert(event)

        stream = client.analytics.realtime.subscribe(
            event_types=["ANOMALY_DETECTED", "BUDGET_WARNING"],
            callback=on_event
        )
        stream.start()
    """

    def __init__(self, client):
        self._client = client
        self._streams = {}
        self._dashboard = None

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v1/gateway", "")

    def _get_ws_url(self) -> str:
        base = self._get_base_url()
        return base.replace("https://", "wss://").replace("http://", "ws://")

    def stream(
        self,
        agent_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        timeout: Optional[float] = None,
    ) -> Iterator[RealtimeEvent]:
        """
        Stream real-time events.

        Args:
            agent_id: Filter by agent
            workspace_id: Filter by workspace
            event_types: Filter by event types
            timeout: Optional timeout in seconds

        Yields:
            RealtimeEvent objects
        """
        # Fall back to polling if WebSocket not available
        if not HAS_WEBSOCKET:
            yield from self._poll_events(agent_id, workspace_id, event_types, timeout)
            return

        ws_url = f"{self._get_ws_url()}/v1/analytics/realtime/stream"

        params = []
        if agent_id:
            params.append(f"agentId={agent_id}")
        if workspace_id:
            params.append(f"workspaceId={workspace_id}")
        if event_types:
            params.append(f"eventTypes={','.join(event_types)}")

        if params:
            ws_url += "?" + "&".join(params)

        event_queue = queue.Queue()
        stop_event = threading.Event()

        def on_message(ws, message):
            try:
                data = json.loads(message)
                event = RealtimeEvent(
                    event_type=data.get("eventType", ""),
                    timestamp=data.get("timestamp", ""),
                    agent_id=data.get("agentId"),
                    workspace_id=data.get("workspaceId"),
                    user_id=data.get("userId"),
                    data=data.get("data", {}),
                    severity=data.get("severity"),
                    requires_action=data.get("requiresAction", False),
                )
                event_queue.put(event)
            except Exception:
                pass

        def on_error(ws, error):
            event_queue.put(None)  # Signal error

        def on_close(ws, close_status_code, close_msg):
            stop_event.set()

        ws = websocket.WebSocketApp(
            ws_url,
            header={"Authorization": f"Bearer {self._client.api_key}"},
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        ws_thread = threading.Thread(target=ws.run_forever, daemon=True)
        ws_thread.start()

        try:
            start_time = datetime.now()
            while not stop_event.is_set():
                try:
                    event = event_queue.get(timeout=1.0)
                    if event is None:
                        break
                    yield event
                except queue.Empty:
                    if timeout and (datetime.now() - start_time).total_seconds() > timeout:
                        break
                    continue
        finally:
            ws.close()

    def _poll_events(
        self,
        agent_id: Optional[str],
        workspace_id: Optional[str],
        event_types: Optional[List[str]],
        timeout: Optional[float],
    ) -> Iterator[RealtimeEvent]:
        """Fallback polling for environments without WebSocket."""
        import time

        url = f"{self._get_base_url()}/v1/analytics/realtime/events"
        last_timestamp = None
        start_time = datetime.now()

        while True:
            params = {"limit": 100}
            if agent_id:
                params["agentId"] = agent_id
            if workspace_id:
                params["workspaceId"] = workspace_id
            if event_types:
                params["eventTypes"] = ",".join(event_types)
            if last_timestamp:
                params["since"] = last_timestamp

            try:
                response = requests.get(
                    url,
                    headers=self._client._get_headers(),
                    params=params,
                    timeout=self._client.timeout
                )
                response.raise_for_status()

                events = response.json().get("events", [])
                for data in events:
                    event = RealtimeEvent(
                        event_type=data.get("eventType", ""),
                        timestamp=data.get("timestamp", ""),
                        agent_id=data.get("agentId"),
                        workspace_id=data.get("workspaceId"),
                        user_id=data.get("userId"),
                        data=data.get("data", {}),
                        severity=data.get("severity"),
                        requires_action=data.get("requiresAction", False),
                    )
                    last_timestamp = event.timestamp
                    yield event
            except Exception:
                pass

            if timeout and (datetime.now() - start_time).total_seconds() > timeout:
                break

            time.sleep(2.0)  # Poll interval

    def subscribe(
        self,
        event_types: List[str],
        callback: Callable[[RealtimeEvent], None],
        agent_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> "AnalyticsStream":
        """
        Subscribe to events with a callback.

        Args:
            event_types: Event types to subscribe to
            callback: Function called for each event
            agent_id: Optional agent filter
            workspace_id: Optional workspace filter
            filters: Additional filters

        Returns:
            AnalyticsStream that can be started/stopped
        """
        stream = AnalyticsStream(
            client=self._client,
            event_types=event_types,
            callback=callback,
            agent_id=agent_id,
            workspace_id=workspace_id,
            filters=filters or {},
        )
        return stream

    def create_subscription(
        self,
        event_types: List[str],
        callback_url: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> EventSubscription:
        """
        Create a webhook subscription for events.

        Args:
            event_types: Event types to subscribe to
            callback_url: URL to receive events
            filters: Optional filters

        Returns:
            EventSubscription with subscription ID
        """
        url = f"{self._get_base_url()}/v1/analytics/realtime/subscriptions"

        payload = {
            "eventTypes": event_types,
            "callbackUrl": callback_url,
            "filters": filters or {},
        }

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return EventSubscription(
            subscription_id=data.get("subscriptionId", ""),
            event_types=data.get("eventTypes", []),
            filters=data.get("filters", {}),
            created_at=data.get("createdAt", ""),
            active=data.get("active", True),
            callback_url=data.get("callbackUrl"),
        )

    def list_subscriptions(self) -> List[EventSubscription]:
        """List all active subscriptions."""
        url = f"{self._get_base_url()}/v1/analytics/realtime/subscriptions"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        subscriptions = []
        for data in response.json().get("subscriptions", []):
            subscriptions.append(EventSubscription(
                subscription_id=data.get("subscriptionId", ""),
                event_types=data.get("eventTypes", []),
                filters=data.get("filters", {}),
                created_at=data.get("createdAt", ""),
                active=data.get("active", True),
                callback_url=data.get("callbackUrl"),
            ))

        return subscriptions

    def delete_subscription(self, subscription_id: str) -> bool:
        """Delete a subscription."""
        url = f"{self._get_base_url()}/v1/analytics/realtime/subscriptions/{subscription_id}"

        response = requests.delete(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )

        return response.status_code == 204

    def metrics_stream(
        self,
        metrics: List[str],
        agent_id: Optional[str] = None,
        interval_seconds: int = 5,
    ) -> Iterator[MetricSnapshot]:
        """
        Stream metric values at regular intervals.

        Args:
            metrics: Metric names to stream
            agent_id: Optional agent filter
            interval_seconds: Update interval

        Yields:
            MetricSnapshot objects
        """
        import time

        url = f"{self._get_base_url()}/v1/analytics/realtime/metrics"

        while True:
            params = {"metrics": ",".join(metrics)}
            if agent_id:
                params["agentId"] = agent_id

            try:
                response = requests.get(
                    url,
                    headers=self._client._get_headers(),
                    params=params,
                    timeout=self._client.timeout
                )
                response.raise_for_status()

                for data in response.json().get("snapshots", []):
                    yield MetricSnapshot(
                        metric=data.get("metric", ""),
                        value=data.get("value", 0.0),
                        timestamp=data.get("timestamp", ""),
                        agent_id=data.get("agentId"),
                        tags=data.get("tags", {}),
                    )
            except Exception:
                pass

            time.sleep(interval_seconds)

    @property
    def dashboard(self) -> "LiveDashboard":
        """Access the live dashboard."""
        if self._dashboard is None:
            self._dashboard = LiveDashboard(self._client)
        return self._dashboard


# =============================================================================
# Analytics Stream
# =============================================================================

class AnalyticsStream:
    """
    Managed event stream with callback.

    Example:
        stream = client.analytics.realtime.subscribe(
            event_types=["ANOMALY_DETECTED"],
            callback=handle_anomaly
        )
        stream.start()
        # ... later
        stream.stop()
    """

    def __init__(
        self,
        client,
        event_types: List[str],
        callback: Callable[[RealtimeEvent], None],
        agent_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        filters: Dict[str, Any] = None,
    ):
        self._client = client
        self._event_types = event_types
        self._callback = callback
        self._agent_id = agent_id
        self._workspace_id = workspace_id
        self._filters = filters or {}
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        """Start streaming events."""
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop streaming events."""
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)

    def _run(self):
        """Internal event loop."""
        realtime = RealtimeAnalytics(self._client)

        try:
            for event in realtime.stream(
                agent_id=self._agent_id,
                workspace_id=self._workspace_id,
                event_types=self._event_types,
            ):
                if self._stop_event.is_set():
                    break

                # Apply additional filters
                if self._should_process(event):
                    try:
                        self._callback(event)
                    except Exception:
                        pass  # Don't let callback errors stop the stream
        except Exception:
            pass
        finally:
            self._running = False

    def _should_process(self, event: RealtimeEvent) -> bool:
        """Check if event passes filters."""
        for key, value in self._filters.items():
            event_value = event.data.get(key) or getattr(event, key, None)
            if event_value != value:
                return False
        return True

    @property
    def is_running(self) -> bool:
        """Check if stream is running."""
        return self._running


# =============================================================================
# Live Dashboard
# =============================================================================

class LiveDashboard:
    """
    Real-time dashboard with live updates.

    Example:
        dashboard = client.analytics.realtime.dashboard

        # Get current state
        state = dashboard.get_state("workspace-123")

        # Start live updates
        for update in dashboard.live_updates("workspace-123"):
            render(update)
    """

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v1/gateway", "")

    def get_state(
        self,
        workspace_id: str,
        include_agents: bool = True,
        include_metrics: bool = True,
        include_alerts: bool = True,
    ) -> Dict[str, Any]:
        """
        Get current dashboard state.

        Args:
            workspace_id: Workspace ID
            include_agents: Include per-agent stats
            include_metrics: Include current metrics
            include_alerts: Include active alerts

        Returns:
            Dashboard state dictionary
        """
        url = f"{self._get_base_url()}/v1/analytics/realtime/dashboard/state"

        params = {
            "workspaceId": workspace_id,
            "includeAgents": str(include_agents).lower(),
            "includeMetrics": str(include_metrics).lower(),
            "includeAlerts": str(include_alerts).lower(),
        }

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json()

    def live_updates(
        self,
        workspace_id: str,
        interval_seconds: int = 5,
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream live dashboard updates.

        Args:
            workspace_id: Workspace ID
            interval_seconds: Update interval

        Yields:
            Dashboard state updates
        """
        import time

        while True:
            try:
                state = self.get_state(workspace_id)
                yield state
            except Exception:
                pass

            time.sleep(interval_seconds)

    def get_widgets(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get dashboard widget configurations."""
        url = f"{self._get_base_url()}/v1/analytics/realtime/dashboard/widgets"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params={"workspaceId": workspace_id},
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json().get("widgets", [])

    def save_layout(
        self,
        workspace_id: str,
        layout: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Save custom dashboard layout."""
        url = f"{self._get_base_url()}/v1/analytics/realtime/dashboard/layout"

        response = requests.put(
            url,
            headers=self._client._get_headers(),
            json={"workspaceId": workspace_id, "layout": layout},
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json()
