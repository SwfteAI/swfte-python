"""
Swfte Enterprise Analytics Suite

The most comprehensive analytics platform for LLM applications.
Far beyond basic analytics - enterprise-grade features for production AI systems.

Enterprise Features (Not available in OSS):
- ML-Powered Classification (vs regex-based)
- Real-time Streaming Analytics via WebSocket
- Multi-User/Team Analytics
- Anomaly Detection with Auto-Alerts
- A/B Testing Framework
- Usage Forecasting & Budgeting
- Compliance Reporting (SOC2, GDPR, HIPAA)
- Custom Metrics & Dimensions
- Agent Performance Benchmarking
- Cost Optimization Recommendations
- Model Comparison Analytics
- User Journey Tracking
- RAG Quality Metrics
- Embedding Analytics
- Webhook Integrations
- Data Retention Policies
"""

from .core import (
    Analytics,
    PromptAnalytics,
    PIIAnalytics,
    ConversationAnalytics,
    PromptInsight,
    PromptPatternSummary,
    TrendingTopic,
    PIITestResult,
    ConversationMessage,
    ConversationHistory,
    Intent,
    Topic,
    Sentiment,
    PIIType,
)

from .enterprise import (
    EnterpriseAnalytics,
    TeamAnalytics,
    AnomalyDetection,
    ABTestingAnalytics,
    ComplianceReporting,
    CostOptimization,
    ModelComparison,
    UserJourneyAnalytics,
    RAGQualityMetrics,
    EmbeddingAnalytics,
)

from .realtime import (
    RealtimeAnalytics,
    AnalyticsStream,
    LiveDashboard,
    EventSubscription,
)

from .alerts import (
    AlertManager,
    AlertRule,
    AlertPolicy,
    WebhookDestination,
    SlackIntegration,
    PagerDutyIntegration,
    AlertEscalation,
)

from .forecasting import (
    UsageForecaster,
    BudgetPredictor,
    CapacityPlanner,
    TrendAnalyzer,
)

from .custom import (
    CustomMetrics,
    MetricDefinition,
    DimensionDefinition,
    CustomDashboard,
    MetricAggregation,
)

__all__ = [
    # Core Analytics
    "Analytics",
    "PromptAnalytics",
    "PIIAnalytics",
    "ConversationAnalytics",
    "PromptInsight",
    "PromptPatternSummary",
    "TrendingTopic",
    "PIITestResult",
    "ConversationMessage",
    "ConversationHistory",
    "Intent",
    "Topic",
    "Sentiment",
    "PIIType",

    # Enterprise Analytics
    "EnterpriseAnalytics",
    "TeamAnalytics",
    "AnomalyDetection",
    "ABTestingAnalytics",
    "ComplianceReporting",
    "CostOptimization",
    "ModelComparison",
    "UserJourneyAnalytics",
    "RAGQualityMetrics",
    "EmbeddingAnalytics",

    # Real-time
    "RealtimeAnalytics",
    "AnalyticsStream",
    "LiveDashboard",
    "EventSubscription",

    # Alerts
    "AlertManager",
    "AlertRule",
    "AlertPolicy",
    "WebhookDestination",
    "SlackIntegration",
    "PagerDutyIntegration",
    "AlertEscalation",

    # Forecasting
    "UsageForecaster",
    "BudgetPredictor",
    "CapacityPlanner",
    "TrendAnalyzer",

    # Custom Metrics
    "CustomMetrics",
    "MetricDefinition",
    "DimensionDefinition",
    "CustomDashboard",
    "MetricAggregation",
]
