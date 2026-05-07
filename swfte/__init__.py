"""
Swfte SDK - Python client for the Swfte AI Gateway

A unified gateway to access all AI providers (OpenAI, Anthropic, Google, etc.)
and self-hosted models through a single API.

Example usage:
    from swfte import SwfteClient

    client = SwfteClient(api_key="sk-swfte-...")

    # Chat completion
    response = client.chat.completions.create(
        model="openai:gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)

    # Streaming
    for chunk in client.chat.completions.create(
        model="anthropic:claude-3-opus",
        messages=[{"role": "user", "content": "Tell me a story"}],
        stream=True
    ):
        print(chunk.choices[0].delta.content, end="")

Enterprise Analytics (v2.0):
    # Access enterprise analytics features
    client = SwfteClient(api_key="sk-swfte-...")

    # Team analytics
    team = client.analytics.enterprise.teams.summary("team-123")

    # Anomaly detection
    anomalies = client.analytics.enterprise.anomalies.detect("agent-123")

    # Real-time streaming
    for event in client.analytics.realtime.stream():
        print(event)

    # Custom alerts
    client.analytics.alerts.create_rule(...)
"""

from .client import SwfteClient
from .models import (
    ChatCompletion,
    ChatCompletionChunk,
    Message,
    ImageGenerationResponse,
    EmbeddingResponse,
    Model,
)
from .exceptions import (
    SwfteError,
    AuthenticationError,
    RateLimitError,
    APIError,
    InvalidRequestError,
)
from .agents import Agent, Agents
from .deployments import Deployment, DeploymentState, HealthStatus, Deployments
from .workflows import (
    Workflow,
    WorkflowNode,
    WorkflowEdge,
    WorkflowExecution,
    ExecutionStatus,
    ValidationResult,
    Workflows,
)

# Core analytics (backwards compatible import)
from .analytics import (
    Analytics,
    PromptInsight,
    PromptPatternSummary,
    TrendingTopic,
    PIITestResult,
    ConversationMessage,
    ConversationHistory,
)

# V2 resources (1.1.0)
from .agent_wizard import AgentWizard
from .audit import Audit
from .chatflows import ChatFlows
from .cost_control import CostControl
from .datasets import Datasets
from .documents import Documents
from .files import Files
from .marketplace import Marketplace
from .mcp import Mcp
from .modules import Modules
from .rag import Rag
from .voice_calls import VoiceCalls

__version__ = "1.1.0"

__all__ = [
    # Client
    "SwfteClient",

    # Models
    "ChatCompletion",
    "ChatCompletionChunk",
    "Message",
    "ImageGenerationResponse",
    "EmbeddingResponse",
    "Model",

    # Exceptions
    "SwfteError",
    "AuthenticationError",
    "RateLimitError",
    "APIError",
    "InvalidRequestError",

    # Agent management
    "Agent",
    "Agents",

    # Deployment management
    "Deployment",
    "DeploymentState",
    "HealthStatus",
    "Deployments",

    # Workflow management
    "Workflow",
    "WorkflowNode",
    "WorkflowEdge",
    "WorkflowExecution",
    "ExecutionStatus",
    "ValidationResult",
    "Workflows",

    # Analytics (core - for backwards compatibility)
    "Analytics",
    "PromptInsight",
    "PromptPatternSummary",
    "TrendingTopic",
    "PIITestResult",
    "ConversationMessage",
    "ConversationHistory",

    # V2 resources (1.1.0)
    "AgentWizard",
    "Audit",
    "ChatFlows",
    "CostControl",
    "Datasets",
    "Documents",
    "Files",
    "Marketplace",
    "Mcp",
    "Modules",
    "Rag",
    "VoiceCalls",
]
