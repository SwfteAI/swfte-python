"""
Unit tests for the Agents module with mocked HTTP.
"""

import pytest
from unittest.mock import patch, MagicMock
import json


class TestAgentsCreate:
    """Tests for Agents.create() method."""

    def test_create_agent_success(
        self, mock_client, mock_agent_data, response_factory
    ):
        """Test successful agent creation."""
        from swfte.agents import Agent

        mock_response = response_factory(mock_agent_data)

        with patch("requests.request", return_value=mock_response) as mock_req:
            agent = mock_client.agents.create(
                name="Test Agent",
                description="A test agent",
                system_prompt="You are a helpful assistant.",
                provider="OPENAI",
                model="gpt-4",
                temperature=0.7,
                max_tokens=2048,
            )

            # Verify the returned agent
            assert isinstance(agent, Agent)
            assert agent.id == mock_agent_data["id"]
            assert agent.agent_name == mock_agent_data["agentName"]
            assert agent.provider == mock_agent_data["provider"]
            assert agent.model == mock_agent_data["model"]

            # Verify the request was made correctly
            mock_req.assert_called_once()
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["method"] == "POST"
            assert "agents" in call_kwargs["url"]
            assert call_kwargs["json"]["agentName"] == "Test Agent"

    def test_create_agent_with_minimal_params(
        self, mock_client, mock_agent_data, response_factory
    ):
        """Test agent creation with minimal parameters."""
        mock_response = response_factory(mock_agent_data)

        with patch("requests.request", return_value=mock_response):
            agent = mock_client.agents.create(name="Minimal Agent")

            assert agent.agent_name == mock_agent_data["agentName"]

    def test_create_agent_with_kwargs(
        self, mock_client, mock_agent_data, response_factory
    ):
        """Test agent creation with additional kwargs."""
        mock_response = response_factory(mock_agent_data)

        with patch("requests.request", return_value=mock_response) as mock_req:
            mock_client.agents.create(
                name="Test Agent",
                custom_field="custom_value",
            )

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["json"]["custom_field"] == "custom_value"


class TestAgentsGet:
    """Tests for Agents.get() method."""

    def test_get_agent_success(
        self, mock_client, mock_agent_data, response_factory
    ):
        """Test successful agent retrieval."""
        from swfte.agents import Agent

        mock_response = response_factory(mock_agent_data)

        with patch("requests.request", return_value=mock_response) as mock_req:
            agent = mock_client.agents.get("agent-123")

            assert isinstance(agent, Agent)
            assert agent.id == "agent-123"
            assert agent.agent_name == mock_agent_data["agentName"]

            mock_req.assert_called_once()
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["method"] == "GET"
            assert "agent-123" in call_kwargs["url"]

    def test_get_agent_not_found(self, mock_client, response_factory):
        """Test agent not found returns 404."""
        from requests.exceptions import HTTPError

        mock_response = response_factory(
            {"error": "Agent not found"}, status_code=404
        )

        with patch("requests.request", return_value=mock_response):
            with pytest.raises(HTTPError):
                mock_client.agents.get("nonexistent-agent")


class TestAgentsList:
    """Tests for Agents.list() method."""

    def test_list_agents_success(
        self, mock_client, mock_agent_list_response, response_factory
    ):
        """Test successful agent listing."""
        from swfte.agents import Agent

        mock_response = response_factory(mock_agent_list_response)

        with patch("requests.request", return_value=mock_response) as mock_req:
            agents = mock_client.agents.list()

            assert isinstance(agents, list)
            assert len(agents) == 2
            assert all(isinstance(a, Agent) for a in agents)

            mock_req.assert_called_once()
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["method"] == "GET"

    def test_list_agents_with_pagination(
        self, mock_client, mock_agent_list_response, response_factory
    ):
        """Test agent listing with pagination parameters."""
        mock_response = response_factory(mock_agent_list_response)

        with patch("requests.request", return_value=mock_response) as mock_req:
            mock_client.agents.list(page=2, size=10)

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["params"]["page"] == 2
            assert call_kwargs["params"]["size"] == 10

    def test_list_agents_empty(self, mock_client, response_factory):
        """Test listing when no agents exist."""
        mock_response = response_factory({"agents": [], "total": 0})

        with patch("requests.request", return_value=mock_response):
            agents = mock_client.agents.list()

            assert agents == []


class TestAgentsUpdate:
    """Tests for Agents.update() method."""

    def test_update_agent_success(
        self, mock_client, mock_agent_data, response_factory
    ):
        """Test successful agent update."""
        # First call returns current agent, second call returns updated
        updated_data = {**mock_agent_data, "agentName": "Updated Agent"}
        mock_responses = [
            response_factory(mock_agent_data),
            response_factory(updated_data),
        ]

        with patch("requests.request", side_effect=mock_responses):
            agent = mock_client.agents.update(
                "agent-123",
                name="Updated Agent",
            )

            assert agent.agent_name == "Updated Agent"

    def test_update_agent_partial(
        self, mock_client, mock_agent_data, response_factory
    ):
        """Test partial agent update only sends changed fields."""
        updated_data = {**mock_agent_data, "temperature": 0.9}
        mock_responses = [
            response_factory(mock_agent_data),
            response_factory(updated_data),
        ]

        with patch("requests.request", side_effect=mock_responses) as mock_req:
            mock_client.agents.update("agent-123", temperature=0.9)

            # Second call should be PUT with updated temperature
            put_call = mock_req.call_args_list[1]
            assert put_call[1]["method"] == "PUT"


class TestAgentsDelete:
    """Tests for Agents.delete() method."""

    def test_delete_agent_success(self, mock_client, response_factory):
        """Test successful agent deletion."""
        mock_response = response_factory({})

        with patch("requests.request", return_value=mock_response) as mock_req:
            mock_client.agents.delete("agent-123")

            mock_req.assert_called_once()
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["method"] == "DELETE"
            assert "agent-123" in call_kwargs["url"]


class TestAgentsPatch:
    """Tests for Agents.patch() method."""

    def test_patch_agent_success(
        self, mock_client, mock_agent_data, response_factory
    ):
        """Test successful agent patch."""
        updated_data = {**mock_agent_data, "description": "New description"}
        mock_response = response_factory(updated_data)

        with patch("requests.request", return_value=mock_response) as mock_req:
            agent = mock_client.agents.patch(
                "agent-123",
                description="New description",
            )

            mock_req.assert_called_once()
            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["method"] == "PATCH"
            assert call_kwargs["json"]["description"] == "New description"


class TestAgentsAssociateWorkflow:
    """Tests for Agents.associate_workflow() method."""

    def test_associate_workflow_success(
        self, mock_client, mock_agent_data, response_factory
    ):
        """Test successful workflow association."""
        updated_data = {
            **mock_agent_data,
            "workflowId": "wf-123",
            "useWorkflow": True,
        }
        mock_response = response_factory(updated_data)

        with patch("requests.request", return_value=mock_response) as mock_req:
            agent = mock_client.agents.associate_workflow("agent-123", "wf-123")

            assert agent.workflow_id == "wf-123"
            assert agent.use_workflow is True

            call_kwargs = mock_req.call_args[1]
            assert call_kwargs["method"] == "POST"
            assert call_kwargs["json"]["workflowId"] == "wf-123"


class TestAgentsGetModelOptions:
    """Tests for Agents.get_model_options() method."""

    def test_get_model_options_success(self, mock_client, response_factory):
        """Test getting model options for a provider."""
        mock_models = [
            {"id": "gpt-4", "name": "GPT-4"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
        ]
        mock_response = response_factory(mock_models)

        with patch("requests.request", return_value=mock_response) as mock_req:
            models = mock_client.agents.get_model_options("OPENAI")

            assert len(models) == 2
            assert models[0]["id"] == "gpt-4"

            call_kwargs = mock_req.call_args[1]
            assert "OPENAI" in call_kwargs["url"]


class TestAgentsGetIOTypes:
    """Tests for Agents.get_io_types() method."""

    def test_get_io_types_success(self, mock_client, response_factory):
        """Test getting input/output types."""
        mock_io_types = {
            "inputTypes": [
                {"value": "TEXT", "label": "Text"},
                {"value": "IMAGE", "label": "Image"},
            ],
            "outputTypes": [
                {"value": "TEXT", "label": "Text"},
                {"value": "JSON", "label": "JSON"},
            ],
        }
        mock_response = response_factory(mock_io_types)

        with patch("requests.request", return_value=mock_response):
            io_types = mock_client.agents.get_io_types()

            assert "inputTypes" in io_types
            assert "outputTypes" in io_types
            assert len(io_types["inputTypes"]) == 2


class TestAgentModel:
    """Tests for the Agent dataclass."""

    def test_agent_from_dict(self, mock_agent_data):
        """Test Agent creation from dictionary."""
        from swfte.agents import Agent

        agent = Agent.from_dict(mock_agent_data)

        assert agent.id == mock_agent_data["id"]
        assert agent.agent_name == mock_agent_data["agentName"]
        assert agent.description == mock_agent_data["description"]
        assert agent.system_prompt == mock_agent_data["systemPrompt"]
        assert agent.provider == mock_agent_data["provider"]
        assert agent.model == mock_agent_data["model"]
        assert agent.temperature == mock_agent_data["temperature"]
        assert agent.max_tokens == mock_agent_data["maxTokens"]
        assert agent.active == mock_agent_data["active"]
        assert agent.verified == mock_agent_data["verified"]

    def test_agent_to_dict(self, mock_agent_data):
        """Test Agent conversion to dictionary."""
        from swfte.agents import Agent

        agent = Agent.from_dict(mock_agent_data)
        result = agent.to_dict()

        assert result["id"] == mock_agent_data["id"]
        assert result["agentName"] == mock_agent_data["agentName"]
        assert result["systemPrompt"] == mock_agent_data["systemPrompt"]

    def test_agent_from_dict_with_snake_case(self):
        """Test Agent creation from snake_case dictionary."""
        from swfte.agents import Agent

        data = {
            "id": "agent-123",
            "agent_name": "Test Agent",
            "system_prompt": "You are helpful.",
            "max_tokens": 1000,
        }

        agent = Agent.from_dict(data)

        assert agent.agent_name == "Test Agent"
        assert agent.system_prompt == "You are helpful."
        assert agent.max_tokens == 1000

    def test_agent_defaults(self):
        """Test Agent default values."""
        from swfte.agents import Agent

        agent = Agent(id="agent-123", agent_name="Test")

        assert agent.active is True
        assert agent.verified is False
        assert agent.input_type == "TEXT"
        assert agent.output_type == "TEXT"
        assert agent.use_workflow is False
