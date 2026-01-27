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

__version__ = "1.0.0"
__all__ = [
    "SwfteClient",
    "ChatCompletion",
    "ChatCompletionChunk",
    "Message",
    "ImageGenerationResponse",
    "EmbeddingResponse",
    "Model",
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
]

