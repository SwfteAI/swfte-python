"""
Enterprise Alert Management Module

Advanced alerting features:
- Custom alert rules with flexible conditions
- Multi-channel notifications (Webhook, Slack, PagerDuty, Email)
- Escalation policies with automatic escalation
- Alert acknowledgment and resolution tracking
- Mute/snooze capabilities
- Alert correlation and deduplication
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
import requests
import json


# =============================================================================
# Enums
# =============================================================================

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertStatus(Enum):
    """Alert status."""
    FIRING = "FIRING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    MUTED = "MUTED"


class ConditionOperator(Enum):
    """Alert condition operators."""
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    GREATER_OR_EQUAL = "GREATER_OR_EQUAL"
    LESS_OR_EQUAL = "LESS_OR_EQUAL"
    CONTAINS = "CONTAINS"
    RATE_INCREASE = "RATE_INCREASE"
    RATE_DECREASE = "RATE_DECREASE"
    ANOMALY = "ANOMALY"


class NotificationChannel(Enum):
    """Notification channels."""
    WEBHOOK = "WEBHOOK"
    SLACK = "SLACK"
    PAGERDUTY = "PAGERDUTY"
    EMAIL = "EMAIL"
    SMS = "SMS"
    OPSGENIE = "OPSGENIE"
    TEAMS = "TEAMS"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AlertCondition:
    """Condition that triggers an alert."""
    metric: str
    operator: str
    threshold: Union[float, str]
    duration_seconds: int = 0  # How long condition must be true
    aggregation: str = "avg"  # avg, max, min, sum, count


@dataclass
class AlertRule:
    """Complete alert rule definition."""
    id: str
    name: str
    description: str
    conditions: List[AlertCondition]
    severity: str
    enabled: bool = True
    agent_ids: List[str] = field(default_factory=list)  # Empty = all agents
    workspace_id: Optional[str] = None
    notification_channels: List[str] = field(default_factory=list)
    escalation_policy_id: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Alert:
    """An active or historical alert."""
    id: str
    rule_id: str
    rule_name: str
    status: str
    severity: str
    fired_at: str
    resolved_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    acknowledged_by: Optional[str] = None
    agent_id: Optional[str] = None
    workspace_id: Optional[str] = None
    metric: str = ""
    current_value: float = 0.0
    threshold: float = 0.0
    message: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    notifications_sent: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WebhookDestination:
    """Webhook notification destination."""
    id: str
    name: str
    url: str
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    template: Optional[str] = None  # Custom JSON template
    enabled: bool = True
    created_at: Optional[str] = None


@dataclass
class SlackIntegration:
    """Slack notification integration."""
    id: str
    name: str
    webhook_url: str
    channel: Optional[str] = None
    username: str = "Swfte Alerts"
    icon_emoji: str = ":warning:"
    enabled: bool = True
    include_details: bool = True


@dataclass
class PagerDutyIntegration:
    """PagerDuty integration."""
    id: str
    name: str
    integration_key: str
    severity_mapping: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class AlertEscalation:
    """Escalation policy definition."""
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]  # Each step has delay, channels, etc.
    repeat_interval_minutes: int = 0  # 0 = no repeat
    enabled: bool = True


@dataclass
class AlertPolicy:
    """Alert notification policy."""
    id: str
    name: str
    match_labels: Dict[str, str]
    notification_channels: List[str]
    escalation_policy_id: Optional[str] = None
    mute_time_windows: List[Dict[str, str]] = field(default_factory=list)
    enabled: bool = True


# =============================================================================
# Alert Manager
# =============================================================================

class AlertManager:
    """
    Enterprise alert management.

    Example:
        alerts = client.analytics.alerts

        # Create a rule
        rule = alerts.create_rule(
            name="High Latency",
            conditions=[
                AlertCondition(
                    metric="latency_ms",
                    operator="GREATER_THAN",
                    threshold=5000,
                    duration_seconds=60
                )
            ],
            severity="WARNING",
            notification_channels=["slack-ops"]
        )

        # List active alerts
        for alert in alerts.list_active():
            print(f"{alert.severity}: {alert.message}")

        # Acknowledge an alert
        alerts.acknowledge(alert_id, user="john@example.com")
    """

    def __init__(self, client):
        self._client = client
        self._webhooks = None
        self._slack = None
        self._pagerduty = None
        self._escalations = None
        self._policies = None

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    # -------------------------------------------------------------------------
    # Alert Rules
    # -------------------------------------------------------------------------

    def create_rule(
        self,
        name: str,
        conditions: List[AlertCondition],
        severity: str,
        description: str = "",
        agent_ids: Optional[List[str]] = None,
        notification_channels: Optional[List[str]] = None,
        escalation_policy_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        annotations: Optional[Dict[str, str]] = None,
    ) -> AlertRule:
        """Create a new alert rule."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/rules"

        payload = {
            "name": name,
            "description": description,
            "conditions": [
                {
                    "metric": c.metric,
                    "operator": c.operator,
                    "threshold": c.threshold,
                    "durationSeconds": c.duration_seconds,
                    "aggregation": c.aggregation,
                }
                for c in conditions
            ],
            "severity": severity,
            "agentIds": agent_ids or [],
            "notificationChannels": notification_channels or [],
            "labels": labels or {},
            "annotations": annotations or {},
        }
        if escalation_policy_id:
            payload["escalationPolicyId"] = escalation_policy_id

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_rule(response.json())

    def get_rule(self, rule_id: str) -> AlertRule:
        """Get an alert rule by ID."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/rules/{rule_id}"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_rule(response.json())

    def list_rules(
        self,
        enabled: Optional[bool] = None,
        severity: Optional[str] = None,
    ) -> List[AlertRule]:
        """List all alert rules."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/rules"

        params = {}
        if enabled is not None:
            params["enabled"] = str(enabled).lower()
        if severity:
            params["severity"] = severity

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return [self._parse_rule(r) for r in response.json().get("rules", [])]

    def update_rule(self, rule_id: str, **updates) -> AlertRule:
        """Update an alert rule."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/rules/{rule_id}"

        response = requests.patch(
            url,
            headers=self._client._get_headers(),
            json=updates,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_rule(response.json())

    def delete_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/rules/{rule_id}"

        response = requests.delete(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )

        return response.status_code == 204

    def enable_rule(self, rule_id: str) -> AlertRule:
        """Enable an alert rule."""
        return self.update_rule(rule_id, enabled=True)

    def disable_rule(self, rule_id: str) -> AlertRule:
        """Disable an alert rule."""
        return self.update_rule(rule_id, enabled=False)

    def _parse_rule(self, data: Dict[str, Any]) -> AlertRule:
        conditions = []
        for c in data.get("conditions", []):
            conditions.append(AlertCondition(
                metric=c.get("metric", ""),
                operator=c.get("operator", ""),
                threshold=c.get("threshold", 0),
                duration_seconds=c.get("durationSeconds", 0),
                aggregation=c.get("aggregation", "avg"),
            ))

        return AlertRule(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            conditions=conditions,
            severity=data.get("severity", ""),
            enabled=data.get("enabled", True),
            agent_ids=data.get("agentIds", []),
            workspace_id=data.get("workspaceId"),
            notification_channels=data.get("notificationChannels", []),
            escalation_policy_id=data.get("escalationPolicyId"),
            labels=data.get("labels", {}),
            annotations=data.get("annotations", {}),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )

    # -------------------------------------------------------------------------
    # Active Alerts
    # -------------------------------------------------------------------------

    def list_active(
        self,
        workspace_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[Alert]:
        """List active (firing) alerts."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/active"

        params = {}
        if workspace_id:
            params["workspaceId"] = workspace_id
        if agent_id:
            params["agentId"] = agent_id
        if severity:
            params["severity"] = severity

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return [self._parse_alert(a) for a in response.json().get("alerts", [])]

    def list_history(
        self,
        workspace_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """List historical alerts."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/history"

        params = {"limit": limit}
        if workspace_id:
            params["workspaceId"] = workspace_id
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if status:
            params["status"] = status

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return [self._parse_alert(a) for a in response.json().get("alerts", [])]

    def get_alert(self, alert_id: str) -> Alert:
        """Get alert details."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/{alert_id}"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_alert(response.json())

    def acknowledge(
        self,
        alert_id: str,
        user: str,
        comment: Optional[str] = None,
    ) -> Alert:
        """Acknowledge an alert."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/{alert_id}/acknowledge"

        payload = {"user": user}
        if comment:
            payload["comment"] = comment

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_alert(response.json())

    def resolve(
        self,
        alert_id: str,
        user: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Alert:
        """Manually resolve an alert."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/{alert_id}/resolve"

        payload = {}
        if user:
            payload["user"] = user
        if comment:
            payload["comment"] = comment

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_alert(response.json())

    def mute(
        self,
        alert_id: str,
        duration_minutes: int,
        user: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Alert:
        """Mute an alert for a duration."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/{alert_id}/mute"

        payload = {"durationMinutes": duration_minutes}
        if user:
            payload["user"] = user
        if reason:
            payload["reason"] = reason

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_alert(response.json())

    def _parse_alert(self, data: Dict[str, Any]) -> Alert:
        return Alert(
            id=data.get("id", ""),
            rule_id=data.get("ruleId", ""),
            rule_name=data.get("ruleName", ""),
            status=data.get("status", ""),
            severity=data.get("severity", ""),
            fired_at=data.get("firedAt", ""),
            resolved_at=data.get("resolvedAt"),
            acknowledged_at=data.get("acknowledgedAt"),
            acknowledged_by=data.get("acknowledgedBy"),
            agent_id=data.get("agentId"),
            workspace_id=data.get("workspaceId"),
            metric=data.get("metric", ""),
            current_value=data.get("currentValue", 0.0),
            threshold=data.get("threshold", 0.0),
            message=data.get("message", ""),
            labels=data.get("labels", {}),
            annotations=data.get("annotations", {}),
            notifications_sent=data.get("notificationsSent", []),
        )

    # -------------------------------------------------------------------------
    # Notification Channels
    # -------------------------------------------------------------------------

    @property
    def webhooks(self) -> "WebhookManager":
        """Manage webhook destinations."""
        if self._webhooks is None:
            self._webhooks = WebhookManager(self._client)
        return self._webhooks

    @property
    def slack(self) -> "SlackManager":
        """Manage Slack integrations."""
        if self._slack is None:
            self._slack = SlackManager(self._client)
        return self._slack

    @property
    def pagerduty(self) -> "PagerDutyManager":
        """Manage PagerDuty integrations."""
        if self._pagerduty is None:
            self._pagerduty = PagerDutyManager(self._client)
        return self._pagerduty

    @property
    def escalations(self) -> "EscalationManager":
        """Manage escalation policies."""
        if self._escalations is None:
            self._escalations = EscalationManager(self._client)
        return self._escalations

    @property
    def policies(self) -> "PolicyManager":
        """Manage notification policies."""
        if self._policies is None:
            self._policies = PolicyManager(self._client)
        return self._policies


# =============================================================================
# Webhook Manager
# =============================================================================

class WebhookManager:
    """Manage webhook destinations."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def create(
        self,
        name: str,
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        template: Optional[str] = None,
    ) -> WebhookDestination:
        """Create a webhook destination."""
        api_url = f"{self._get_base_url()}/v1/analytics/alerts/channels/webhooks"

        payload = {
            "name": name,
            "url": url,
            "method": method,
            "headers": headers or {},
        }
        if template:
            payload["template"] = template

        response = requests.post(
            api_url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return WebhookDestination(
            id=data.get("id", ""),
            name=data.get("name", ""),
            url=data.get("url", ""),
            method=data.get("method", "POST"),
            headers=data.get("headers", {}),
            template=data.get("template"),
            enabled=data.get("enabled", True),
            created_at=data.get("createdAt"),
        )

    def list(self) -> List[WebhookDestination]:
        """List all webhook destinations."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/channels/webhooks"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        webhooks = []
        for data in response.json().get("webhooks", []):
            webhooks.append(WebhookDestination(
                id=data.get("id", ""),
                name=data.get("name", ""),
                url=data.get("url", ""),
                method=data.get("method", "POST"),
                headers=data.get("headers", {}),
                template=data.get("template"),
                enabled=data.get("enabled", True),
                created_at=data.get("createdAt"),
            ))

        return webhooks

    def delete(self, webhook_id: str) -> bool:
        """Delete a webhook destination."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/channels/webhooks/{webhook_id}"

        response = requests.delete(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )

        return response.status_code == 204

    def test(self, webhook_id: str) -> Dict[str, Any]:
        """Test a webhook destination."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/channels/webhooks/{webhook_id}/test"

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json()


# =============================================================================
# Slack Manager
# =============================================================================

class SlackManager:
    """Manage Slack integrations."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def create(
        self,
        name: str,
        webhook_url: str,
        channel: Optional[str] = None,
        username: str = "Swfte Alerts",
        icon_emoji: str = ":warning:",
    ) -> SlackIntegration:
        """Create a Slack integration."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/channels/slack"

        payload = {
            "name": name,
            "webhookUrl": webhook_url,
            "username": username,
            "iconEmoji": icon_emoji,
        }
        if channel:
            payload["channel"] = channel

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return SlackIntegration(
            id=data.get("id", ""),
            name=data.get("name", ""),
            webhook_url=data.get("webhookUrl", ""),
            channel=data.get("channel"),
            username=data.get("username", "Swfte Alerts"),
            icon_emoji=data.get("iconEmoji", ":warning:"),
            enabled=data.get("enabled", True),
        )

    def list(self) -> List[SlackIntegration]:
        """List all Slack integrations."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/channels/slack"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        integrations = []
        for data in response.json().get("integrations", []):
            integrations.append(SlackIntegration(
                id=data.get("id", ""),
                name=data.get("name", ""),
                webhook_url=data.get("webhookUrl", ""),
                channel=data.get("channel"),
                username=data.get("username", "Swfte Alerts"),
                icon_emoji=data.get("iconEmoji", ":warning:"),
                enabled=data.get("enabled", True),
            ))

        return integrations

    def delete(self, integration_id: str) -> bool:
        """Delete a Slack integration."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/channels/slack/{integration_id}"

        response = requests.delete(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )

        return response.status_code == 204


# =============================================================================
# PagerDuty Manager
# =============================================================================

class PagerDutyManager:
    """Manage PagerDuty integrations."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def create(
        self,
        name: str,
        integration_key: str,
        severity_mapping: Optional[Dict[str, str]] = None,
    ) -> PagerDutyIntegration:
        """Create a PagerDuty integration."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/channels/pagerduty"

        payload = {
            "name": name,
            "integrationKey": integration_key,
            "severityMapping": severity_mapping or {
                "INFO": "info",
                "WARNING": "warning",
                "ERROR": "error",
                "CRITICAL": "critical",
            },
        }

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return PagerDutyIntegration(
            id=data.get("id", ""),
            name=data.get("name", ""),
            integration_key=data.get("integrationKey", ""),
            severity_mapping=data.get("severityMapping", {}),
            enabled=data.get("enabled", True),
        )

    def list(self) -> List[PagerDutyIntegration]:
        """List all PagerDuty integrations."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/channels/pagerduty"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        integrations = []
        for data in response.json().get("integrations", []):
            integrations.append(PagerDutyIntegration(
                id=data.get("id", ""),
                name=data.get("name", ""),
                integration_key=data.get("integrationKey", ""),
                severity_mapping=data.get("severityMapping", {}),
                enabled=data.get("enabled", True),
            ))

        return integrations


# =============================================================================
# Escalation Manager
# =============================================================================

class EscalationManager:
    """Manage escalation policies."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def create(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        description: str = "",
        repeat_interval_minutes: int = 0,
    ) -> AlertEscalation:
        """
        Create an escalation policy.

        Args:
            name: Policy name
            steps: List of escalation steps, each with:
                   - delay_minutes: Wait time before this step
                   - channels: List of notification channel IDs
            description: Policy description
            repeat_interval_minutes: Repeat interval (0 = no repeat)

        Returns:
            AlertEscalation policy
        """
        url = f"{self._get_base_url()}/v1/analytics/alerts/escalations"

        payload = {
            "name": name,
            "description": description,
            "steps": steps,
            "repeatIntervalMinutes": repeat_interval_minutes,
        }

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return AlertEscalation(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            steps=data.get("steps", []),
            repeat_interval_minutes=data.get("repeatIntervalMinutes", 0),
            enabled=data.get("enabled", True),
        )

    def list(self) -> List[AlertEscalation]:
        """List all escalation policies."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/escalations"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        policies = []
        for data in response.json().get("escalations", []):
            policies.append(AlertEscalation(
                id=data.get("id", ""),
                name=data.get("name", ""),
                description=data.get("description", ""),
                steps=data.get("steps", []),
                repeat_interval_minutes=data.get("repeatIntervalMinutes", 0),
                enabled=data.get("enabled", True),
            ))

        return policies


# =============================================================================
# Policy Manager
# =============================================================================

class PolicyManager:
    """Manage notification policies."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def create(
        self,
        name: str,
        match_labels: Dict[str, str],
        notification_channels: List[str],
        escalation_policy_id: Optional[str] = None,
        mute_time_windows: Optional[List[Dict[str, str]]] = None,
    ) -> AlertPolicy:
        """Create a notification policy."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/policies"

        payload = {
            "name": name,
            "matchLabels": match_labels,
            "notificationChannels": notification_channels,
            "muteTimeWindows": mute_time_windows or [],
        }
        if escalation_policy_id:
            payload["escalationPolicyId"] = escalation_policy_id

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return AlertPolicy(
            id=data.get("id", ""),
            name=data.get("name", ""),
            match_labels=data.get("matchLabels", {}),
            notification_channels=data.get("notificationChannels", []),
            escalation_policy_id=data.get("escalationPolicyId"),
            mute_time_windows=data.get("muteTimeWindows", []),
            enabled=data.get("enabled", True),
        )

    def list(self) -> List[AlertPolicy]:
        """List all notification policies."""
        url = f"{self._get_base_url()}/v1/analytics/alerts/policies"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        policies = []
        for data in response.json().get("policies", []):
            policies.append(AlertPolicy(
                id=data.get("id", ""),
                name=data.get("name", ""),
                match_labels=data.get("matchLabels", {}),
                notification_channels=data.get("notificationChannels", []),
                escalation_policy_id=data.get("escalationPolicyId"),
                mute_time_windows=data.get("muteTimeWindows", []),
                enabled=data.get("enabled", True),
            ))

        return policies
