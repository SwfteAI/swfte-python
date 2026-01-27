"""
Pytest configuration and fixtures for Swfte SDK tests.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


# Mock response factory
class MockResponse:
    """Mock HTTP response object."""

    def __init__(self, json_data, status_code=200, headers=None):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = headers or {}
        self.content = json.dumps(json_data).encode() if json_data else b''
        self.text = json.dumps(json_data) if json_data else ''
        self.ok = 200 <= status_code < 300

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if not self.ok:
            from requests.exceptions import HTTPError
            raise HTTPError(f"HTTP Error: {self.status_code}")


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for testing."""
    return "sk-swfte-test-key-12345"


@pytest.fixture
def mock_workspace_id():
    """Provide a mock workspace ID for testing."""
    return "ws-test-12345"


@pytest.fixture
def mock_base_url():
    """Provide a mock base URL for testing."""
    return "https://api.test.swfte.com/v1/gateway"


@pytest.fixture
def mock_client(mock_api_key, mock_workspace_id, mock_base_url):
    """Create a mock SwfteClient for testing."""
    with patch.dict('os.environ', {}, clear=False):
        from swfte import SwfteClient
        return SwfteClient(
            api_key=mock_api_key,
            base_url=mock_base_url,
            workspace_id=mock_workspace_id,
            timeout=30,
            max_retries=1,
        )


@pytest.fixture
def mock_agent_data():
    """Provide mock agent data for testing."""
    return {
        "id": "agent-123",
        "agentName": "Test Agent",
        "description": "A test agent for unit testing",
        "systemPrompt": "You are a helpful test assistant.",
        "provider": "OPENAI",
        "model": "gpt-4",
        "temperature": 0.7,
        "maxTokens": 2048,
        "active": True,
        "verified": False,
        "inputType": "TEXT",
        "outputType": "TEXT",
        "workspaceId": "ws-test-12345",
        "mode": "agent-chat",
        "workflowId": None,
        "useWorkflow": False,
    }


@pytest.fixture
def mock_agent_list_response(mock_agent_data):
    """Provide mock agent list response."""
    return {
        "agents": [
            mock_agent_data,
            {
                **mock_agent_data,
                "id": "agent-456",
                "agentName": "Second Test Agent",
            }
        ],
        "total": 2,
        "page": 1,
        "size": 20,
    }


@pytest.fixture
def mock_chat_response():
    """Provide mock chat completion response."""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1699000000,
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you today?"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }


@pytest.fixture
def mock_workflow_data():
    """Provide mock workflow data for testing."""
    return {
        "id": "wf-123",
        "name": "Test Workflow",
        "description": "A test workflow",
        "workspaceId": "ws-test-12345",
        "nodes": [
            {
                "id": "node-1",
                "type": "input",
                "position": {"x": 0, "y": 0},
                "data": {}
            },
            {
                "id": "node-2",
                "type": "agent",
                "position": {"x": 200, "y": 0},
                "data": {"agentId": "agent-123"}
            }
        ],
        "edges": [
            {
                "id": "edge-1",
                "source": "node-1",
                "target": "node-2",
            }
        ],
        "active": True,
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_deployment_data():
    """Provide mock deployment data for testing."""
    return {
        "id": "deploy-123",
        "name": "Test Deployment",
        "workspaceId": "ws-test-12345",
        "modelId": "model-123",
        "state": "RUNNING",
        "gpuType": "NVIDIA A100",
        "gpuCount": 1,
        "endpoint": "https://api.runpod.ai/v2/deploy-123",
        "createdAt": "2024-01-01T00:00:00Z",
        "metrics": {
            "requestsPerMinute": 10,
            "averageLatencyMs": 150,
            "errorRate": 0.01,
        }
    }


@pytest.fixture
def mock_requests(request):
    """Create a mock for the requests library that can be configured per test."""
    with patch('requests.request') as mock_request:
        yield mock_request


def create_mock_response(json_data, status_code=200):
    """Helper to create MockResponse objects."""
    return MockResponse(json_data, status_code)


# Export helper for use in tests
@pytest.fixture
def response_factory():
    """Factory fixture for creating mock responses."""
    return create_mock_response
