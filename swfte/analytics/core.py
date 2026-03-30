"""
Core Analytics Module - Foundation for Swfte Analytics

This module provides the foundational analytics capabilities that are shared
across all tiers. Enterprise features build on top of these core components.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import requests
import json


# =============================================================================
# Enums
# =============================================================================

class Intent(Enum):
    """Prompt intent classification."""
    QUESTION = "QUESTION"
    COMMAND = "COMMAND"
    REQUEST = "REQUEST"
    CREATIVE = "CREATIVE"
    COMPLAINT = "COMPLAINT"
    FEEDBACK = "FEEDBACK"
    CLARIFICATION = "CLARIFICATION"
    CONTINUATION = "CONTINUATION"


class Topic(Enum):
    """Prompt topic classification."""
    CODING = "CODING"
    WRITING = "WRITING"
    DATA = "DATA"
    EDUCATION = "EDUCATION"
    SUPPORT = "SUPPORT"
    BUSINESS = "BUSINESS"
    HEALTH = "HEALTH"
    LEGAL = "LEGAL"
    FINANCE = "FINANCE"
    CREATIVE = "CREATIVE"
    RESEARCH = "RESEARCH"
    GENERAL = "GENERAL"


class Sentiment(Enum):
    """Sentiment classification."""
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    FRUSTRATED = "FRUSTRATED"
    CONFUSED = "CONFUSED"
    SATISFIED = "SATISFIED"


class PIIType(Enum):
    """Types of PII detected."""
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    SSN = "SSN"
    CREDIT_CARD = "CREDIT_CARD"
    ADDRESS = "ADDRESS"
    NAME = "NAME"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    IP_ADDRESS = "IP_ADDRESS"
    PASSPORT = "PASSPORT"
    DRIVERS_LICENSE = "DRIVERS_LICENSE"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    MEDICAL_ID = "MEDICAL_ID"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PromptInsight:
    """Individual prompt insight record with full metadata."""
    id: str
    agent_id: str
    sanitized_prompt: str
    intent: str
    topic: str
    sentiment: str
    complexity: int  # 1-5
    pii_types_detected: List[str] = field(default_factory=list)
    pii_count: int = 0
    latency_ms: int = 0
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    sanitized_response: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    was_streaming: bool = False
    created_at: Optional[str] = None
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None
    # Enterprise fields
    confidence_scores: Optional[Dict[str, float]] = None
    custom_dimensions: Optional[Dict[str, Any]] = None
    ab_test_variant: Optional[str] = None
    trace_id: Optional[str] = None
    parent_span_id: Optional[str] = None


@dataclass
class PromptPatternSummary:
    """Comprehensive summary of prompt patterns."""
    total_prompts: int
    intent_distribution: Dict[str, int]
    topic_distribution: Dict[str, int]
    sentiment_distribution: Dict[str, int]
    frustration_rate: float
    avg_complexity: float = 0.0
    total_pii_detected: int = 0
    avg_latency_ms: float = 0.0
    avg_tokens_per_prompt: float = 0.0
    avg_response_tokens: float = 0.0
    avg_estimated_cost_usd: float = 0.0
    streaming_rate: float = 0.0
    error_rate: float = 0.0
    # Enterprise fields
    unique_users: int = 0
    unique_sessions: int = 0
    satisfaction_score: Optional[float] = None
    resolution_rate: Optional[float] = None
    escalation_rate: Optional[float] = None
    model_distribution: Optional[Dict[str, int]] = None
    provider_distribution: Optional[Dict[str, int]] = None
    hourly_distribution: Optional[Dict[int, int]] = None
    percentiles: Optional[Dict[str, Dict[str, float]]] = None


@dataclass
class TrendingTopic:
    """A trending topic with trend analysis."""
    topic: str
    count: int
    percentage: float
    trend: str  # UP, DOWN, STABLE
    change_from_previous: float = 0.0
    # Enterprise fields
    velocity: float = 0.0  # Rate of change
    forecast_next_period: Optional[int] = None
    related_topics: List[str] = field(default_factory=list)
    sentiment_breakdown: Optional[Dict[str, int]] = None


@dataclass
class PIITestResult:
    """Result of PII detection with detailed findings."""
    original_text: str
    sanitized_text: str
    pii_types_detected: List[str]
    pii_count: int
    detections: List[Dict[str, Any]] = field(default_factory=list)
    # Enterprise fields
    risk_score: float = 0.0
    compliance_flags: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class ConversationMessage:
    """A message in a conversation with full metadata."""
    role: str  # USER, ASSISTANT, SYSTEM
    content: str
    created_at: int  # Unix timestamp
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Enterprise fields
    tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    sentiment: Optional[str] = None
    intent: Optional[str] = None
    model: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class ConversationHistory:
    """Full conversation history with analytics."""
    id: str
    agent_id: str
    messages: List[ConversationMessage]
    message_count: int
    active: bool
    created_at: str
    last_modified_at: str
    conversation_type: str = "STANDARD"
    participants: List[str] = field(default_factory=list)
    # Enterprise fields
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: int = 0
    resolution_status: Optional[str] = None
    satisfaction_rating: Optional[int] = None
    escalated: bool = False
    tags: List[str] = field(default_factory=list)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Analytics Classes
# =============================================================================

class Analytics:
    """
    Core Analytics API - Foundation for all analytics features.

    Example:
        client = SwfteClient(api_key="sk-swfte-...")

        # Get prompt pattern summary
        summary = client.analytics.prompts.summary("agent-123")
        print(f"Frustration rate: {summary.frustration_rate:.1%}")

        # Access enterprise features
        anomalies = client.analytics.enterprise.anomalies.detect("agent-123")
        forecast = client.analytics.enterprise.forecasting.predict_usage()
    """

    def __init__(self, client):
        self._client = client
        self._prompts = None
        self._pii = None
        self._conversations = None
        self._enterprise = None
        self._realtime = None
        self._alerts = None
        self._custom = None

    @property
    def prompts(self) -> "PromptAnalytics":
        """Access prompt analytics."""
        if self._prompts is None:
            self._prompts = PromptAnalytics(self._client)
        return self._prompts

    @property
    def pii(self) -> "PIIAnalytics":
        """Access PII detection tools."""
        if self._pii is None:
            self._pii = PIIAnalytics(self._client)
        return self._pii

    @property
    def conversations(self) -> "ConversationAnalytics":
        """Access conversation history."""
        if self._conversations is None:
            self._conversations = ConversationAnalytics(self._client)
        return self._conversations

    @property
    def enterprise(self):
        """Access enterprise analytics features."""
        if self._enterprise is None:
            from .enterprise import EnterpriseAnalytics
            self._enterprise = EnterpriseAnalytics(self._client)
        return self._enterprise

    @property
    def realtime(self):
        """Access real-time streaming analytics."""
        if self._realtime is None:
            from .realtime import RealtimeAnalytics
            self._realtime = RealtimeAnalytics(self._client)
        return self._realtime

    @property
    def alerts(self):
        """Access alert management."""
        if self._alerts is None:
            from .alerts import AlertManager
            self._alerts = AlertManager(self._client)
        return self._alerts

    @property
    def custom(self):
        """Access custom metrics and dimensions."""
        if self._custom is None:
            from .custom import CustomMetrics
            self._custom = CustomMetrics(self._client)
        return self._custom


class PromptAnalytics:
    """Prompt pattern analytics with enterprise extensions."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def summary(
        self,
        agent_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_percentiles: bool = False,
        include_distributions: bool = True,
    ) -> PromptPatternSummary:
        """
        Get comprehensive prompt pattern summary.

        Args:
            agent_id: The agent ID to analyze
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            include_percentiles: Include latency/token percentiles (Enterprise)
            include_distributions: Include hourly/model distributions

        Returns:
            PromptPatternSummary with full analytics
        """
        url = f"{self._get_base_url()}/v1/analytics/prompts/agents/{agent_id}/summary"

        params = {
            "includePercentiles": str(include_percentiles).lower(),
            "includeDistributions": str(include_distributions).lower(),
        }
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()
        data = response.json().get("summary", {})

        return PromptPatternSummary(
            total_prompts=data.get("totalPrompts", 0),
            intent_distribution=data.get("intentDistribution", {}),
            topic_distribution=data.get("topicDistribution", {}),
            sentiment_distribution=data.get("sentimentDistribution", {}),
            frustration_rate=data.get("frustrationRate", 0.0),
            avg_complexity=data.get("avgComplexity", 0.0),
            total_pii_detected=data.get("totalPiiDetected", 0),
            avg_latency_ms=data.get("avgLatencyMs", 0.0),
            avg_tokens_per_prompt=data.get("avgTokensPerPrompt", 0.0),
            avg_response_tokens=data.get("avgResponseTokens", 0.0),
            avg_estimated_cost_usd=data.get("avgEstimatedCostUsd", 0.0),
            streaming_rate=data.get("streamingRate", 0.0),
            error_rate=data.get("errorRate", 0.0),
            unique_users=data.get("uniqueUsers", 0),
            unique_sessions=data.get("uniqueSessions", 0),
            satisfaction_score=data.get("satisfactionScore"),
            resolution_rate=data.get("resolutionRate"),
            escalation_rate=data.get("escalationRate"),
            model_distribution=data.get("modelDistribution"),
            provider_distribution=data.get("providerDistribution"),
            hourly_distribution=data.get("hourlyDistribution"),
            percentiles=data.get("percentiles"),
        )

    def insights(
        self,
        agent_id: str,
        limit: int = 50,
        offset: int = 0,
        intent: Optional[str] = None,
        topic: Optional[str] = None,
        sentiment: Optional[str] = None,
        has_pii: Optional[bool] = None,
        min_latency_ms: Optional[int] = None,
        max_latency_ms: Optional[int] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
        ab_test_variant: Optional[str] = None,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> List[PromptInsight]:
        """
        Get filtered list of prompt insights.

        Args:
            agent_id: The agent ID
            limit: Maximum number of insights
            offset: Pagination offset
            intent: Filter by intent
            topic: Filter by topic
            sentiment: Filter by sentiment
            has_pii: Filter for PII presence
            min_latency_ms: Minimum latency filter
            max_latency_ms: Maximum latency filter
            user_id: Filter by user ID
            session_id: Filter by session ID
            model: Filter by model
            ab_test_variant: Filter by A/B test variant
            order_by: Field to order by
            order_dir: Order direction (asc/desc)

        Returns:
            List of PromptInsight objects
        """
        url = f"{self._get_base_url()}/v1/analytics/prompts/agents/{agent_id}/insights"

        params = {"limit": limit, "offset": offset, "orderBy": order_by, "orderDir": order_dir}
        if intent:
            params["intent"] = intent
        if topic:
            params["topic"] = topic
        if sentiment:
            params["sentiment"] = sentiment
        if has_pii is not None:
            params["hasPii"] = str(has_pii).lower()
        if min_latency_ms:
            params["minLatencyMs"] = min_latency_ms
        if max_latency_ms:
            params["maxLatencyMs"] = max_latency_ms
        if user_id:
            params["userId"] = user_id
        if session_id:
            params["sessionId"] = session_id
        if model:
            params["model"] = model
        if ab_test_variant:
            params["abTestVariant"] = ab_test_variant

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        insights = []
        for item in response.json().get("insights", []):
            insights.append(PromptInsight(
                id=item.get("id", ""),
                agent_id=item.get("agentId", ""),
                sanitized_prompt=item.get("sanitizedPrompt", ""),
                intent=item.get("intent", ""),
                topic=item.get("topic", ""),
                sentiment=item.get("sentiment", ""),
                complexity=item.get("complexity", 1),
                pii_types_detected=item.get("piiTypesDetected", []),
                pii_count=item.get("piiCount", 0),
                latency_ms=item.get("latencyMs", 0),
                input_tokens=item.get("inputTokens"),
                output_tokens=item.get("outputTokens"),
                estimated_cost_usd=item.get("estimatedCostUsd"),
                sanitized_response=item.get("sanitizedResponse"),
                provider=item.get("provider"),
                model=item.get("model"),
                was_streaming=item.get("wasStreaming", False),
                created_at=item.get("createdAt"),
                workspace_id=item.get("workspaceId"),
                user_id=item.get("userId"),
                conversation_id=item.get("conversationId"),
                session_id=item.get("sessionId"),
                confidence_scores=item.get("confidenceScores"),
                custom_dimensions=item.get("customDimensions"),
                ab_test_variant=item.get("abTestVariant"),
                trace_id=item.get("traceId"),
                parent_span_id=item.get("parentSpanId"),
            ))

        return insights

    def trending(
        self,
        workspace_id: str,
        limit: int = 10,
        days: int = 7,
        include_forecast: bool = False,
        include_related: bool = False,
    ) -> List[TrendingTopic]:
        """
        Get trending topics with advanced analysis.

        Args:
            workspace_id: The workspace ID
            limit: Maximum topics to return
            days: Number of days to analyze
            include_forecast: Include next-period forecast (Enterprise)
            include_related: Include related topics (Enterprise)

        Returns:
            List of TrendingTopic objects
        """
        url = f"{self._get_base_url()}/v1/analytics/prompts/workspaces/{workspace_id}/trending"

        params = {
            "limit": limit,
            "days": days,
            "includeForecast": str(include_forecast).lower(),
            "includeRelated": str(include_related).lower(),
        }

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        topics = []
        for item in response.json().get("trendingTopics", []):
            topics.append(TrendingTopic(
                topic=item.get("topic", ""),
                count=item.get("count", 0),
                percentage=item.get("percentage", 0.0),
                trend=item.get("trend", "STABLE"),
                change_from_previous=item.get("changeFromPrevious", 0.0),
                velocity=item.get("velocity", 0.0),
                forecast_next_period=item.get("forecastNextPeriod"),
                related_topics=item.get("relatedTopics", []),
                sentiment_breakdown=item.get("sentimentBreakdown"),
            ))

        return topics

    def compare(
        self,
        agent_ids: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, PromptPatternSummary]:
        """
        Compare analytics across multiple agents (Enterprise).

        Args:
            agent_ids: List of agent IDs to compare
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            Dict mapping agent_id to PromptPatternSummary
        """
        url = f"{self._get_base_url()}/v1/analytics/prompts/compare"

        params = {"agentIds": ",".join(agent_ids)}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        result = {}
        for agent_id, data in response.json().get("comparisons", {}).items():
            result[agent_id] = PromptPatternSummary(
                total_prompts=data.get("totalPrompts", 0),
                intent_distribution=data.get("intentDistribution", {}),
                topic_distribution=data.get("topicDistribution", {}),
                sentiment_distribution=data.get("sentimentDistribution", {}),
                frustration_rate=data.get("frustrationRate", 0.0),
                avg_complexity=data.get("avgComplexity", 0.0),
                total_pii_detected=data.get("totalPiiDetected", 0),
                avg_latency_ms=data.get("avgLatencyMs", 0.0),
                avg_tokens_per_prompt=data.get("avgTokensPerPrompt", 0.0),
                avg_response_tokens=data.get("avgResponseTokens", 0.0),
                avg_estimated_cost_usd=data.get("avgEstimatedCostUsd", 0.0),
                streaming_rate=data.get("streamingRate", 0.0),
                error_rate=data.get("errorRate", 0.0),
            )

        return result


class PIIAnalytics:
    """Enterprise PII detection with compliance features."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def test(self, text: str, compliance_mode: Optional[str] = None) -> PIITestResult:
        """
        Test PII detection with optional compliance mode.

        Args:
            text: Text to analyze
            compliance_mode: Optional compliance mode (GDPR, HIPAA, SOC2, PCI)

        Returns:
            PIITestResult with detailed findings
        """
        url = f"{self._get_base_url()}/v1/analytics/prompts/pii/test"

        payload = {"text": text}
        if compliance_mode:
            payload["complianceMode"] = compliance_mode

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        result = response.json().get("result", {})
        return PIITestResult(
            original_text=result.get("originalText", text),
            sanitized_text=result.get("sanitizedText", ""),
            pii_types_detected=result.get("piiTypesDetected", []),
            pii_count=result.get("piiCount", 0),
            detections=result.get("detections", []),
            risk_score=result.get("riskScore", 0.0),
            compliance_flags=result.get("complianceFlags", []),
            recommended_actions=result.get("recommendedActions", []),
        )

    def check(self, text: str) -> bool:
        """Check if text contains PII."""
        url = f"{self._get_base_url()}/v1/analytics/prompts/pii/check"

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json={"text": text},
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json().get("containsPII", False)

    def audit_log(
        self,
        workspace_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get PII detection audit log (Enterprise).

        Args:
            workspace_id: Workspace ID
            start_date: Start date
            end_date: End date
            limit: Maximum entries

        Returns:
            List of audit log entries
        """
        url = f"{self._get_base_url()}/v1/analytics/prompts/pii/audit"

        params = {"workspaceId": workspace_id, "limit": limit}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json().get("auditLog", [])

    def risk_report(
        self,
        workspace_id: str,
        period: str = "30d",
    ) -> Dict[str, Any]:
        """
        Generate PII risk report (Enterprise).

        Args:
            workspace_id: Workspace ID
            period: Time period (7d, 30d, 90d)

        Returns:
            Risk report with scores and recommendations
        """
        url = f"{self._get_base_url()}/v1/analytics/prompts/pii/risk-report"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params={"workspaceId": workspace_id, "period": period},
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json()


class ConversationAnalytics:
    """Conversation analytics with enterprise features."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def get(
        self,
        conversation_id: str,
        include_analytics: bool = True,
    ) -> ConversationHistory:
        """
        Get full conversation with analytics.

        Args:
            conversation_id: Conversation ID
            include_analytics: Include per-message analytics

        Returns:
            ConversationHistory with full metadata
        """
        url = f"{self._get_base_url()}/v1/conversations/{conversation_id}"

        params = {"includeAnalytics": str(include_analytics).lower()}

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        messages = []
        for msg in data.get("messages", []):
            messages.append(ConversationMessage(
                role=msg.get("role", ""),
                content=msg.get("content", ""),
                created_at=msg.get("creationDate", 0),
                metadata=msg.get("metadata", {}),
                tokens=msg.get("tokens"),
                latency_ms=msg.get("latencyMs"),
                sentiment=msg.get("sentiment"),
                intent=msg.get("intent"),
                model=msg.get("model"),
                tool_calls=msg.get("toolCalls"),
            ))

        return ConversationHistory(
            id=data.get("id", ""),
            agent_id=data.get("agentId", ""),
            messages=messages,
            message_count=data.get("messageCount", len(messages)),
            active=data.get("active", True),
            created_at=str(data.get("creationDate", "")),
            last_modified_at=str(data.get("lastModifiedDate", "")),
            conversation_type=data.get("conversationType", "STANDARD"),
            participants=data.get("participants", []),
            total_tokens=data.get("totalTokens", 0),
            total_cost_usd=data.get("totalCostUsd", 0.0),
            total_latency_ms=data.get("totalLatencyMs", 0),
            resolution_status=data.get("resolutionStatus"),
            satisfaction_rating=data.get("satisfactionRating"),
            escalated=data.get("escalated", False),
            tags=data.get("tags", []),
            custom_attributes=data.get("customAttributes", {}),
        )

    def messages(
        self,
        conversation_id: str,
        limit: int = 50,
        newest_first: bool = True,
    ) -> List[ConversationMessage]:
        """Get paginated messages from a conversation."""
        url = f"{self._get_base_url()}/v1/conversations/{conversation_id}/messages"

        params = {"limit": limit, "newestFirst": str(newest_first).lower()}

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        messages = []
        for msg in response.json().get("messages", []):
            messages.append(ConversationMessage(
                role=msg.get("role", ""),
                content=msg.get("content", ""),
                created_at=msg.get("createdAt", 0),
                metadata=msg.get("metadata", {}),
                tokens=msg.get("tokens"),
                latency_ms=msg.get("latencyMs"),
                sentiment=msg.get("sentiment"),
                intent=msg.get("intent"),
                model=msg.get("model"),
                tool_calls=msg.get("toolCalls"),
            ))

        return messages

    def search(
        self,
        workspace_id: str,
        query: Optional[str] = None,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        resolution_status: Optional[str] = None,
        escalated: Optional[bool] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
    ) -> List[ConversationHistory]:
        """
        Search conversations with filters (Enterprise).

        Args:
            workspace_id: Workspace ID
            query: Text search query
            agent_id: Filter by agent
            user_id: Filter by user
            tags: Filter by tags
            resolution_status: Filter by resolution
            escalated: Filter escalated conversations
            start_date: Start date
            end_date: End date
            limit: Maximum results

        Returns:
            List of matching conversations
        """
        url = f"{self._get_base_url()}/v1/conversations/search"

        params = {"workspaceId": workspace_id, "limit": limit}
        if query:
            params["query"] = query
        if agent_id:
            params["agentId"] = agent_id
        if user_id:
            params["userId"] = user_id
        if tags:
            params["tags"] = ",".join(tags)
        if resolution_status:
            params["resolutionStatus"] = resolution_status
        if escalated is not None:
            params["escalated"] = str(escalated).lower()
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        conversations = []
        for data in response.json().get("conversations", []):
            conversations.append(ConversationHistory(
                id=data.get("id", ""),
                agent_id=data.get("agentId", ""),
                messages=[],  # Search doesn't return full messages
                message_count=data.get("messageCount", 0),
                active=data.get("active", True),
                created_at=str(data.get("creationDate", "")),
                last_modified_at=str(data.get("lastModifiedDate", "")),
                conversation_type=data.get("conversationType", "STANDARD"),
                participants=data.get("participants", []),
                total_tokens=data.get("totalTokens", 0),
                total_cost_usd=data.get("totalCostUsd", 0.0),
                total_latency_ms=data.get("totalLatencyMs", 0),
                resolution_status=data.get("resolutionStatus"),
                satisfaction_rating=data.get("satisfactionRating"),
                escalated=data.get("escalated", False),
                tags=data.get("tags", []),
                custom_attributes=data.get("customAttributes", {}),
            ))

        return conversations

    def summary(
        self,
        workspace_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get conversation summary statistics (Enterprise).

        Args:
            workspace_id: Workspace ID
            start_date: Start date
            end_date: End date

        Returns:
            Summary statistics
        """
        url = f"{self._get_base_url()}/v1/conversations/summary"

        params = {"workspaceId": workspace_id}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json()
