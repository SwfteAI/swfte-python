"""
Enterprise Analytics Module - Premium Features

Features exclusive to Swfte Enterprise:
- ML-Powered Classification (not regex-based)
- Team Analytics & Multi-User Insights
- Anomaly Detection with Auto-Alerting
- A/B Testing Framework
- Compliance Reporting (SOC2, GDPR, HIPAA, PCI)
- Cost Optimization Recommendations
- Model Comparison & Benchmarking
- User Journey Tracking
- RAG Quality Metrics
- Embedding Analytics
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

class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    SOC2 = "SOC2"
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI_DSS"
    CCPA = "CCPA"
    ISO_27001 = "ISO_27001"


class AnomalyType(Enum):
    """Types of anomalies detected."""
    LATENCY_SPIKE = "LATENCY_SPIKE"
    ERROR_SURGE = "ERROR_SURGE"
    COST_ANOMALY = "COST_ANOMALY"
    PII_SURGE = "PII_SURGE"
    FRUSTRATION_SPIKE = "FRUSTRATION_SPIKE"
    TRAFFIC_ANOMALY = "TRAFFIC_ANOMALY"
    MODEL_DEGRADATION = "MODEL_DEGRADATION"


class JourneyStage(Enum):
    """User journey stages."""
    AWARENESS = "AWARENESS"
    CONSIDERATION = "CONSIDERATION"
    DECISION = "DECISION"
    ONBOARDING = "ONBOARDING"
    ACTIVATION = "ACTIVATION"
    RETENTION = "RETENTION"
    EXPANSION = "EXPANSION"
    ADVOCACY = "ADVOCACY"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class TeamMember:
    """Team member analytics."""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    total_prompts: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    frustration_rate: float = 0.0
    most_used_agents: List[str] = field(default_factory=list)
    last_active: Optional[str] = None


@dataclass
class TeamSummary:
    """Team-level analytics summary."""
    team_id: str
    total_members: int
    total_prompts: int
    total_cost_usd: float
    avg_cost_per_user: float
    avg_latency_ms: float
    frustration_rate: float
    top_users: List[TeamMember] = field(default_factory=list)
    cost_trend: str = "STABLE"  # UP, DOWN, STABLE
    usage_trend: str = "STABLE"


@dataclass
class Anomaly:
    """Detected anomaly."""
    id: str
    type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    detected_at: str
    metric: str
    expected_value: float
    actual_value: float
    deviation_percent: float
    affected_agents: List[str] = field(default_factory=list)
    affected_users: List[str] = field(default_factory=list)
    auto_resolved: bool = False
    resolved_at: Optional[str] = None
    root_cause: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ABTestResult:
    """A/B test result."""
    test_id: str
    test_name: str
    variant_a: str
    variant_b: str
    status: str  # RUNNING, COMPLETED, STOPPED
    started_at: str
    ended_at: Optional[str] = None
    variant_a_prompts: int = 0
    variant_b_prompts: int = 0
    variant_a_metrics: Dict[str, float] = field(default_factory=dict)
    variant_b_metrics: Dict[str, float] = field(default_factory=dict)
    winner: Optional[str] = None
    confidence: float = 0.0
    statistical_significance: bool = False
    lift: Optional[float] = None


@dataclass
class ComplianceReport:
    """Compliance audit report."""
    report_id: str
    framework: str
    generated_at: str
    period_start: str
    period_end: str
    overall_score: float  # 0-100
    status: str  # COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW
    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    data_retention_compliant: bool = True
    pii_handling_compliant: bool = True
    access_control_compliant: bool = True
    audit_log_compliant: bool = True
    encryption_compliant: bool = True


@dataclass
class CostOptimizationRecommendation:
    """Cost optimization recommendation."""
    id: str
    category: str  # MODEL_SWITCH, CACHING, PROMPT_OPTIMIZATION, BATCH_PROCESSING
    title: str
    description: str
    estimated_savings_usd: float
    estimated_savings_percent: float
    effort: str  # LOW, MEDIUM, HIGH
    impact: str  # LOW, MEDIUM, HIGH
    implementation_steps: List[str] = field(default_factory=list)
    affected_agents: List[str] = field(default_factory=list)


@dataclass
class ModelBenchmark:
    """Model comparison benchmark."""
    model: str
    provider: str
    total_requests: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    avg_input_tokens: float
    avg_output_tokens: float
    avg_cost_per_request: float
    quality_score: Optional[float] = None  # Based on user feedback
    tasks_excels_at: List[str] = field(default_factory=list)


@dataclass
class UserJourney:
    """User journey analytics."""
    user_id: str
    current_stage: str
    first_interaction: str
    last_interaction: str
    total_sessions: int
    total_prompts: int
    total_cost_usd: float
    stage_progression: List[Dict[str, Any]] = field(default_factory=list)
    conversion_events: List[Dict[str, Any]] = field(default_factory=list)
    churn_risk: float = 0.0
    lifetime_value: float = 0.0
    satisfaction_trend: str = "STABLE"


@dataclass
class RAGQualityMetric:
    """RAG quality measurement."""
    agent_id: str
    period: str
    total_queries: int
    retrieval_accuracy: float  # % of relevant docs retrieved
    answer_relevance: float  # % of answers deemed relevant
    faithfulness: float  # % of answers grounded in context
    context_precision: float
    context_recall: float
    answer_correctness: float
    latency_retrieval_ms: float
    latency_generation_ms: float
    fallback_rate: float  # % that fell back to non-RAG
    no_answer_rate: float


@dataclass
class EmbeddingMetric:
    """Embedding quality and usage metrics."""
    model: str
    total_embeddings: int
    avg_dimensions: int
    avg_tokens_per_embedding: int
    avg_latency_ms: float
    total_cost_usd: float
    similarity_distribution: Dict[str, float] = field(default_factory=dict)
    clustering_quality: Optional[float] = None
    retrieval_performance: Optional[Dict[str, float]] = None


# =============================================================================
# Enterprise Analytics Class
# =============================================================================

class EnterpriseAnalytics:
    """
    Enterprise-only analytics features.

    These features are not available in the OSS version and require
    a Swfte Enterprise subscription.

    Example:
        client = SwfteClient(api_key="sk-swfte-...")

        # Team analytics
        team = client.analytics.enterprise.teams.summary("team-123")
        print(f"Team cost: ${team.total_cost_usd:.2f}")

        # Anomaly detection
        anomalies = client.analytics.enterprise.anomalies.detect("agent-123")
        for anomaly in anomalies:
            print(f"{anomaly.type}: {anomaly.severity}")

        # A/B Testing
        result = client.analytics.enterprise.ab_testing.get_result("test-123")
        print(f"Winner: {result.winner} (confidence: {result.confidence:.1%})")

        # Compliance
        report = client.analytics.enterprise.compliance.generate_report("SOC2")
        print(f"Compliance score: {report.overall_score}")
    """

    def __init__(self, client):
        self._client = client
        self._teams = None
        self._anomalies = None
        self._ab_testing = None
        self._compliance = None
        self._cost_optimization = None
        self._model_comparison = None
        self._user_journeys = None
        self._rag_quality = None
        self._embeddings = None
        self._forecasting = None
        self._budget = None

    @property
    def teams(self) -> "TeamAnalytics":
        """Team and multi-user analytics."""
        if self._teams is None:
            self._teams = TeamAnalytics(self._client)
        return self._teams

    @property
    def anomalies(self) -> "AnomalyDetection":
        """Anomaly detection and alerting."""
        if self._anomalies is None:
            self._anomalies = AnomalyDetection(self._client)
        return self._anomalies

    @property
    def ab_testing(self) -> "ABTestingAnalytics":
        """A/B testing framework."""
        if self._ab_testing is None:
            self._ab_testing = ABTestingAnalytics(self._client)
        return self._ab_testing

    @property
    def compliance(self) -> "ComplianceReporting":
        """Compliance reporting and auditing."""
        if self._compliance is None:
            self._compliance = ComplianceReporting(self._client)
        return self._compliance

    @property
    def cost_optimization(self) -> "CostOptimization":
        """Cost optimization recommendations."""
        if self._cost_optimization is None:
            self._cost_optimization = CostOptimization(self._client)
        return self._cost_optimization

    @property
    def model_comparison(self) -> "ModelComparison":
        """Model benchmarking and comparison."""
        if self._model_comparison is None:
            self._model_comparison = ModelComparison(self._client)
        return self._model_comparison

    @property
    def user_journeys(self) -> "UserJourneyAnalytics":
        """User journey tracking and analysis."""
        if self._user_journeys is None:
            self._user_journeys = UserJourneyAnalytics(self._client)
        return self._user_journeys

    @property
    def rag_quality(self) -> "RAGQualityMetrics":
        """RAG system quality metrics."""
        if self._rag_quality is None:
            self._rag_quality = RAGQualityMetrics(self._client)
        return self._rag_quality

    @property
    def embeddings(self) -> "EmbeddingAnalytics":
        """Embedding quality and usage analytics."""
        if self._embeddings is None:
            self._embeddings = EmbeddingAnalytics(self._client)
        return self._embeddings

    @property
    def forecasting(self):
        """Usage forecasting and prediction."""
        if self._forecasting is None:
            from .forecasting import UsageForecaster
            self._forecasting = UsageForecaster(self._client)
        return self._forecasting

    @property
    def budget(self):
        """Budget forecasting and planning."""
        if self._budget is None:
            from .forecasting import BudgetPredictor
            self._budget = BudgetPredictor(self._client)
        return self._budget


# =============================================================================
# Team Analytics
# =============================================================================

class TeamAnalytics:
    """Multi-user and team analytics."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def summary(
        self,
        team_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> TeamSummary:
        """Get team-level analytics summary."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/teams/{team_id}/summary"

        params = {}
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
        data = response.json()

        top_users = []
        for user in data.get("topUsers", []):
            top_users.append(TeamMember(
                user_id=user.get("userId", ""),
                name=user.get("name"),
                email=user.get("email"),
                total_prompts=user.get("totalPrompts", 0),
                total_cost_usd=user.get("totalCostUsd", 0.0),
                avg_latency_ms=user.get("avgLatencyMs", 0.0),
                frustration_rate=user.get("frustrationRate", 0.0),
                most_used_agents=user.get("mostUsedAgents", []),
                last_active=user.get("lastActive"),
            ))

        return TeamSummary(
            team_id=data.get("teamId", team_id),
            total_members=data.get("totalMembers", 0),
            total_prompts=data.get("totalPrompts", 0),
            total_cost_usd=data.get("totalCostUsd", 0.0),
            avg_cost_per_user=data.get("avgCostPerUser", 0.0),
            avg_latency_ms=data.get("avgLatencyMs", 0.0),
            frustration_rate=data.get("frustrationRate", 0.0),
            top_users=top_users,
            cost_trend=data.get("costTrend", "STABLE"),
            usage_trend=data.get("usageTrend", "STABLE"),
        )

    def members(
        self,
        team_id: str,
        order_by: str = "total_cost_usd",
        order_dir: str = "desc",
        limit: int = 50,
    ) -> List[TeamMember]:
        """Get all team members with analytics."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/teams/{team_id}/members"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params={"orderBy": order_by, "orderDir": order_dir, "limit": limit},
            timeout=self._client.timeout
        )
        response.raise_for_status()

        members = []
        for user in response.json().get("members", []):
            members.append(TeamMember(
                user_id=user.get("userId", ""),
                name=user.get("name"),
                email=user.get("email"),
                total_prompts=user.get("totalPrompts", 0),
                total_cost_usd=user.get("totalCostUsd", 0.0),
                avg_latency_ms=user.get("avgLatencyMs", 0.0),
                frustration_rate=user.get("frustrationRate", 0.0),
                most_used_agents=user.get("mostUsedAgents", []),
                last_active=user.get("lastActive"),
            ))

        return members

    def usage_by_department(
        self,
        workspace_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Get usage breakdown by department."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/teams/usage-by-department"

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

        return response.json().get("departments", {})


# =============================================================================
# Anomaly Detection
# =============================================================================

class AnomalyDetection:
    """ML-powered anomaly detection."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def detect(
        self,
        agent_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        lookback_hours: int = 24,
        sensitivity: str = "medium",  # low, medium, high
    ) -> List[Anomaly]:
        """Detect anomalies in metrics."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/anomalies/detect"

        params = {"lookbackHours": lookback_hours, "sensitivity": sensitivity}
        if agent_id:
            params["agentId"] = agent_id
        if workspace_id:
            params["workspaceId"] = workspace_id

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        anomalies = []
        for item in response.json().get("anomalies", []):
            anomalies.append(Anomaly(
                id=item.get("id", ""),
                type=item.get("type", ""),
                severity=item.get("severity", "LOW"),
                detected_at=item.get("detectedAt", ""),
                metric=item.get("metric", ""),
                expected_value=item.get("expectedValue", 0.0),
                actual_value=item.get("actualValue", 0.0),
                deviation_percent=item.get("deviationPercent", 0.0),
                affected_agents=item.get("affectedAgents", []),
                affected_users=item.get("affectedUsers", []),
                auto_resolved=item.get("autoResolved", False),
                resolved_at=item.get("resolvedAt"),
                root_cause=item.get("rootCause"),
                recommendations=item.get("recommendations", []),
            ))

        return anomalies

    def history(
        self,
        workspace_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[Anomaly]:
        """Get historical anomalies."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/anomalies/history"

        params = {"workspaceId": workspace_id, "limit": limit}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if severity:
            params["severity"] = severity

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        anomalies = []
        for item in response.json().get("anomalies", []):
            anomalies.append(Anomaly(
                id=item.get("id", ""),
                type=item.get("type", ""),
                severity=item.get("severity", "LOW"),
                detected_at=item.get("detectedAt", ""),
                metric=item.get("metric", ""),
                expected_value=item.get("expectedValue", 0.0),
                actual_value=item.get("actualValue", 0.0),
                deviation_percent=item.get("deviationPercent", 0.0),
                affected_agents=item.get("affectedAgents", []),
                affected_users=item.get("affectedUsers", []),
                auto_resolved=item.get("autoResolved", False),
                resolved_at=item.get("resolvedAt"),
                root_cause=item.get("rootCause"),
                recommendations=item.get("recommendations", []),
            ))

        return anomalies

    def configure_thresholds(
        self,
        workspace_id: str,
        thresholds: Dict[str, Dict[str, float]],
    ) -> Dict[str, Any]:
        """Configure custom anomaly thresholds."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/anomalies/thresholds"

        response = requests.put(
            url,
            headers=self._client._get_headers(),
            json={"workspaceId": workspace_id, "thresholds": thresholds},
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json()


# =============================================================================
# A/B Testing
# =============================================================================

class ABTestingAnalytics:
    """A/B testing framework for LLM experiments."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def create_test(
        self,
        name: str,
        agent_id: str,
        variant_a_config: Dict[str, Any],
        variant_b_config: Dict[str, Any],
        traffic_split: float = 0.5,
        metrics: List[str] = None,
        min_sample_size: int = 100,
    ) -> ABTestResult:
        """Create a new A/B test."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/ab-tests"

        payload = {
            "name": name,
            "agentId": agent_id,
            "variantAConfig": variant_a_config,
            "variantBConfig": variant_b_config,
            "trafficSplit": traffic_split,
            "metrics": metrics or ["latency_ms", "satisfaction", "completion_rate"],
            "minSampleSize": min_sample_size,
        }

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return self._parse_test_result(data)

    def get_result(self, test_id: str) -> ABTestResult:
        """Get A/B test results."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/ab-tests/{test_id}"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_test_result(response.json())

    def list_tests(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[ABTestResult]:
        """List A/B tests."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/ab-tests"

        params = {"limit": limit}
        if agent_id:
            params["agentId"] = agent_id
        if status:
            params["status"] = status

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return [self._parse_test_result(item) for item in response.json().get("tests", [])]

    def stop_test(self, test_id: str, winner: Optional[str] = None) -> ABTestResult:
        """Stop an A/B test."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/ab-tests/{test_id}/stop"

        payload = {}
        if winner:
            payload["winner"] = winner

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return self._parse_test_result(response.json())

    def _parse_test_result(self, data: Dict[str, Any]) -> ABTestResult:
        return ABTestResult(
            test_id=data.get("testId", ""),
            test_name=data.get("testName", ""),
            variant_a=data.get("variantA", ""),
            variant_b=data.get("variantB", ""),
            status=data.get("status", ""),
            started_at=data.get("startedAt", ""),
            ended_at=data.get("endedAt"),
            variant_a_prompts=data.get("variantAPrompts", 0),
            variant_b_prompts=data.get("variantBPrompts", 0),
            variant_a_metrics=data.get("variantAMetrics", {}),
            variant_b_metrics=data.get("variantBMetrics", {}),
            winner=data.get("winner"),
            confidence=data.get("confidence", 0.0),
            statistical_significance=data.get("statisticalSignificance", False),
            lift=data.get("lift"),
        )


# =============================================================================
# Compliance Reporting
# =============================================================================

class ComplianceReporting:
    """Compliance auditing and reporting."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def generate_report(
        self,
        framework: str,
        workspace_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> ComplianceReport:
        """Generate a compliance report."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/compliance/report"

        payload = {"framework": framework}
        if workspace_id:
            payload["workspaceId"] = workspace_id
        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return ComplianceReport(
            report_id=data.get("reportId", ""),
            framework=data.get("framework", framework),
            generated_at=data.get("generatedAt", ""),
            period_start=data.get("periodStart", ""),
            period_end=data.get("periodEnd", ""),
            overall_score=data.get("overallScore", 0.0),
            status=data.get("status", ""),
            findings=data.get("findings", []),
            recommendations=data.get("recommendations", []),
            data_retention_compliant=data.get("dataRetentionCompliant", True),
            pii_handling_compliant=data.get("piiHandlingCompliant", True),
            access_control_compliant=data.get("accessControlCompliant", True),
            audit_log_compliant=data.get("auditLogCompliant", True),
            encryption_compliant=data.get("encryptionCompliant", True),
        )

    def get_audit_log(
        self,
        workspace_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get detailed audit log."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/compliance/audit-log"

        params = {"workspaceId": workspace_id, "limit": limit}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if action_type:
            params["actionType"] = action_type

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json().get("auditLog", [])

    def data_retention_policy(
        self,
        workspace_id: str,
        retention_days: int,
        pii_retention_days: Optional[int] = None,
        auto_delete: bool = True,
    ) -> Dict[str, Any]:
        """Configure data retention policy."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/compliance/retention"

        payload = {
            "workspaceId": workspace_id,
            "retentionDays": retention_days,
            "autoDelete": auto_delete,
        }
        if pii_retention_days:
            payload["piiRetentionDays"] = pii_retention_days

        response = requests.put(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json()


# =============================================================================
# Cost Optimization
# =============================================================================

class CostOptimization:
    """AI-powered cost optimization recommendations."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def get_recommendations(
        self,
        workspace_id: str,
        min_savings_usd: float = 0.0,
        max_effort: str = "HIGH",
    ) -> List[CostOptimizationRecommendation]:
        """Get cost optimization recommendations."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/cost/recommendations"

        params = {
            "workspaceId": workspace_id,
            "minSavingsUsd": min_savings_usd,
            "maxEffort": max_effort,
        }

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        recommendations = []
        for item in response.json().get("recommendations", []):
            recommendations.append(CostOptimizationRecommendation(
                id=item.get("id", ""),
                category=item.get("category", ""),
                title=item.get("title", ""),
                description=item.get("description", ""),
                estimated_savings_usd=item.get("estimatedSavingsUsd", 0.0),
                estimated_savings_percent=item.get("estimatedSavingsPercent", 0.0),
                effort=item.get("effort", "MEDIUM"),
                impact=item.get("impact", "MEDIUM"),
                implementation_steps=item.get("implementationSteps", []),
                affected_agents=item.get("affectedAgents", []),
            ))

        return recommendations

    def cost_breakdown(
        self,
        workspace_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: str = "agent",  # agent, model, user, day
    ) -> Dict[str, Any]:
        """Get detailed cost breakdown."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/cost/breakdown"

        params = {"workspaceId": workspace_id, "groupBy": group_by}
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

    def set_budget(
        self,
        workspace_id: str,
        daily_budget_usd: Optional[float] = None,
        monthly_budget_usd: Optional[float] = None,
        alert_threshold_percent: float = 80.0,
    ) -> Dict[str, Any]:
        """Set budget limits and alerts."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/cost/budget"

        payload = {
            "workspaceId": workspace_id,
            "alertThresholdPercent": alert_threshold_percent,
        }
        if daily_budget_usd:
            payload["dailyBudgetUsd"] = daily_budget_usd
        if monthly_budget_usd:
            payload["monthlyBudgetUsd"] = monthly_budget_usd

        response = requests.put(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json()


# =============================================================================
# Model Comparison
# =============================================================================

class ModelComparison:
    """Model benchmarking and comparison analytics."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def benchmark(
        self,
        workspace_id: str,
        models: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[ModelBenchmark]:
        """Get model performance benchmarks."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/models/benchmark"

        params = {"workspaceId": workspace_id}
        if models:
            params["models"] = ",".join(models)
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

        benchmarks = []
        for item in response.json().get("benchmarks", []):
            benchmarks.append(ModelBenchmark(
                model=item.get("model", ""),
                provider=item.get("provider", ""),
                total_requests=item.get("totalRequests", 0),
                avg_latency_ms=item.get("avgLatencyMs", 0.0),
                p50_latency_ms=item.get("p50LatencyMs", 0.0),
                p95_latency_ms=item.get("p95LatencyMs", 0.0),
                p99_latency_ms=item.get("p99LatencyMs", 0.0),
                error_rate=item.get("errorRate", 0.0),
                avg_input_tokens=item.get("avgInputTokens", 0.0),
                avg_output_tokens=item.get("avgOutputTokens", 0.0),
                avg_cost_per_request=item.get("avgCostPerRequest", 0.0),
                quality_score=item.get("qualityScore"),
                tasks_excels_at=item.get("tasksExcelsAt", []),
            ))

        return benchmarks

    def recommend_model(
        self,
        task_type: str,
        priority: str = "balanced",  # cost, quality, speed
        max_cost_per_request: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Get model recommendation for a task."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/models/recommend"

        params = {"taskType": task_type, "priority": priority}
        if max_cost_per_request:
            params["maxCostPerRequest"] = max_cost_per_request

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json()


# =============================================================================
# User Journey Analytics
# =============================================================================

class UserJourneyAnalytics:
    """User journey tracking and lifecycle analytics."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def get_journey(self, user_id: str) -> UserJourney:
        """Get a user's journey."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/journeys/{user_id}"

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            timeout=self._client.timeout
        )
        response.raise_for_status()

        data = response.json()
        return UserJourney(
            user_id=data.get("userId", user_id),
            current_stage=data.get("currentStage", ""),
            first_interaction=data.get("firstInteraction", ""),
            last_interaction=data.get("lastInteraction", ""),
            total_sessions=data.get("totalSessions", 0),
            total_prompts=data.get("totalPrompts", 0),
            total_cost_usd=data.get("totalCostUsd", 0.0),
            stage_progression=data.get("stageProgression", []),
            conversion_events=data.get("conversionEvents", []),
            churn_risk=data.get("churnRisk", 0.0),
            lifetime_value=data.get("lifetimeValue", 0.0),
            satisfaction_trend=data.get("satisfactionTrend", "STABLE"),
        )

    def cohort_analysis(
        self,
        workspace_id: str,
        cohort_by: str = "week",  # day, week, month
        metric: str = "retention",  # retention, activation, revenue
        periods: int = 12,
    ) -> Dict[str, Any]:
        """Get cohort analysis."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/journeys/cohorts"

        params = {
            "workspaceId": workspace_id,
            "cohortBy": cohort_by,
            "metric": metric,
            "periods": periods,
        }

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json()

    def churn_prediction(
        self,
        workspace_id: str,
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Get users at risk of churning."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/journeys/churn-risk"

        params = {"workspaceId": workspace_id, "threshold": threshold}

        response = requests.get(
            url,
            headers=self._client._get_headers(),
            params=params,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json().get("atRiskUsers", [])


# =============================================================================
# RAG Quality Metrics
# =============================================================================

class RAGQualityMetrics:
    """RAG system quality and performance metrics."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def get_metrics(
        self,
        agent_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> RAGQualityMetric:
        """Get RAG quality metrics for an agent."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/rag/{agent_id}/metrics"

        params = {}
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

        data = response.json()
        return RAGQualityMetric(
            agent_id=data.get("agentId", agent_id),
            period=data.get("period", ""),
            total_queries=data.get("totalQueries", 0),
            retrieval_accuracy=data.get("retrievalAccuracy", 0.0),
            answer_relevance=data.get("answerRelevance", 0.0),
            faithfulness=data.get("faithfulness", 0.0),
            context_precision=data.get("contextPrecision", 0.0),
            context_recall=data.get("contextRecall", 0.0),
            answer_correctness=data.get("answerCorrectness", 0.0),
            latency_retrieval_ms=data.get("latencyRetrievalMs", 0.0),
            latency_generation_ms=data.get("latencyGenerationMs", 0.0),
            fallback_rate=data.get("fallbackRate", 0.0),
            no_answer_rate=data.get("noAnswerRate", 0.0),
        )

    def evaluate_response(
        self,
        query: str,
        response: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
    ) -> Dict[str, float]:
        """Evaluate a RAG response."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/rag/evaluate"

        payload = {
            "query": query,
            "response": response,
            "contexts": contexts,
        }
        if ground_truth:
            payload["groundTruth"] = ground_truth

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json().get("scores", {})


# =============================================================================
# Embedding Analytics
# =============================================================================

class EmbeddingAnalytics:
    """Embedding quality and usage analytics."""

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        return self._client.base_url.replace("/v2/gateway", "").replace("/v1/gateway", "")

    def get_metrics(
        self,
        workspace_id: str,
        model: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[EmbeddingMetric]:
        """Get embedding usage metrics."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/embeddings/metrics"

        params = {"workspaceId": workspace_id}
        if model:
            params["model"] = model
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

        metrics = []
        for item in response.json().get("metrics", []):
            metrics.append(EmbeddingMetric(
                model=item.get("model", ""),
                total_embeddings=item.get("totalEmbeddings", 0),
                avg_dimensions=item.get("avgDimensions", 0),
                avg_tokens_per_embedding=item.get("avgTokensPerEmbedding", 0),
                avg_latency_ms=item.get("avgLatencyMs", 0.0),
                total_cost_usd=item.get("totalCostUsd", 0.0),
                similarity_distribution=item.get("similarityDistribution", {}),
                clustering_quality=item.get("clusteringQuality"),
                retrieval_performance=item.get("retrievalPerformance"),
            ))

        return metrics

    def analyze_similarity(
        self,
        embeddings: List[List[float]],
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyze similarity patterns in embeddings."""
        url = f"{self._get_base_url()}/v1/analytics/enterprise/embeddings/analyze"

        payload = {"embeddings": embeddings}
        if labels:
            payload["labels"] = labels

        response = requests.post(
            url,
            headers=self._client._get_headers(),
            json=payload,
            timeout=self._client.timeout
        )
        response.raise_for_status()

        return response.json()
