"""
Swfte Enterprise Analytics - Backwards Compatibility Module

This module provides backwards compatibility. The full analytics suite
has been moved to the analytics/ package.

For new code, use:
    from swfte.analytics import Analytics, EnterpriseAnalytics, ...

This module re-exports core analytics for backwards compatibility.

"

# Re-export from analytics package for backwards compatibility
from .analytics.core import (
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

__all__ = [
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
]
