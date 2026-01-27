"""
Unit tests for SwfteClient initialization and configuration.
"""

import pytest
from unittest.mock import patch, MagicMock
import os


class TestSwfteClientInitialization:
    """Tests for SwfteClient initialization."""

    def test_client_initialization_with_api_key(self, mock_api_key, mock_base_url):
        """Test client initializes correctly with API key."""
        from swfte import SwfteClient

        client = SwfteClient(
            api_key=mock_api_key,
            base_url=mock_base_url,
        )

        assert client.api_key == mock_api_key
        assert client.base_url == mock_base_url.rstrip("/")
        assert client.timeout == 60
        assert client.max_retries == 3

    def test_client_initialization_with_env_api_key(self, mock_base_url):
        """Test client reads API key from environment variable."""
        from swfte import SwfteClient

        env_key = "sk-swfte-env-test-key"
        with patch.dict(os.environ, {"SWFTE_API_KEY": env_key}):
            client = SwfteClient(base_url=mock_base_url)
            assert client.api_key == env_key

    def test_client_initialization_without_api_key_raises(self, mock_base_url):
        """Test client raises ValueError when API key is missing."""
        from swfte import SwfteClient

        with patch.dict(os.environ, {}, clear=True):
            # Clear the env var if it exists
            os.environ.pop("SWFTE_API_KEY", None)
            with pytest.raises(ValueError) as exc_info:
                SwfteClient(base_url=mock_base_url)
            assert "API key is required" in str(exc_info.value)

    def test_client_initialization_with_workspace_id(
        self, mock_api_key, mock_base_url, mock_workspace_id
    ):
        """Test client accepts workspace ID."""
        from swfte import SwfteClient

        client = SwfteClient(
            api_key=mock_api_key,
            base_url=mock_base_url,
            workspace_id=mock_workspace_id,
        )

        assert client.workspace_id == mock_workspace_id

    def test_client_initialization_with_env_workspace_id(
        self, mock_api_key, mock_base_url
    ):
        """Test client reads workspace ID from environment."""
        from swfte import SwfteClient

        env_workspace = "ws-env-test"
        with patch.dict(os.environ, {"SWFTE_WORKSPACE_ID": env_workspace}):
            client = SwfteClient(
                api_key=mock_api_key,
                base_url=mock_base_url,
            )
            assert client.workspace_id == env_workspace

    def test_client_initialization_with_custom_timeout(
        self, mock_api_key, mock_base_url
    ):
        """Test client accepts custom timeout."""
        from swfte import SwfteClient

        client = SwfteClient(
            api_key=mock_api_key,
            base_url=mock_base_url,
            timeout=120,
        )

        assert client.timeout == 120

    def test_client_initialization_with_custom_max_retries(
        self, mock_api_key, mock_base_url
    ):
        """Test client accepts custom max retries."""
        from swfte import SwfteClient

        client = SwfteClient(
            api_key=mock_api_key,
            base_url=mock_base_url,
            max_retries=5,
        )

        assert client.max_retries == 5

    def test_client_base_url_trailing_slash_stripped(self, mock_api_key):
        """Test client strips trailing slash from base URL."""
        from swfte import SwfteClient

        client = SwfteClient(
            api_key=mock_api_key,
            base_url="https://api.test.swfte.com/v1/gateway/",
        )

        assert not client.base_url.endswith("/")

    def test_client_default_base_url(self, mock_api_key):
        """Test client uses default base URL."""
        from swfte import SwfteClient

        client = SwfteClient(api_key=mock_api_key)

        assert client.base_url == "https://api.swfte.com/v1/gateway"


class TestSwfteClientHeaders:
    """Tests for SwfteClient header generation."""

    def test_get_headers_includes_authorization(self, mock_client, mock_api_key):
        """Test headers include authorization token."""
        headers = mock_client._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {mock_api_key}"

    def test_get_headers_includes_content_type(self, mock_client):
        """Test headers include content type."""
        headers = mock_client._get_headers()

        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"

    def test_get_headers_includes_user_agent(self, mock_client):
        """Test headers include user agent."""
        headers = mock_client._get_headers()

        assert "User-Agent" in headers
        assert "swfte-python" in headers["User-Agent"]

    def test_get_headers_includes_workspace_id_when_set(
        self, mock_client, mock_workspace_id
    ):
        """Test headers include workspace ID when configured."""
        headers = mock_client._get_headers()

        assert "X-Workspace-ID" in headers
        assert headers["X-Workspace-ID"] == mock_workspace_id

    def test_get_headers_excludes_workspace_id_when_not_set(
        self, mock_api_key, mock_base_url
    ):
        """Test headers exclude workspace ID when not configured."""
        from swfte import SwfteClient

        client = SwfteClient(
            api_key=mock_api_key,
            base_url=mock_base_url,
        )
        headers = client._get_headers()

        assert "X-Workspace-ID" not in headers


class TestSwfteClientResources:
    """Tests for SwfteClient resource accessors."""

    def test_chat_property_returns_chat_instance(self, mock_client):
        """Test chat property returns Chat instance."""
        from swfte.chat import Chat

        chat = mock_client.chat
        assert isinstance(chat, Chat)

    def test_chat_property_returns_same_instance(self, mock_client):
        """Test chat property returns cached instance."""
        chat1 = mock_client.chat
        chat2 = mock_client.chat
        assert chat1 is chat2

    def test_agents_property_returns_agents_instance(self, mock_client):
        """Test agents property returns Agents instance."""
        from swfte.agents import Agents

        agents = mock_client.agents
        assert isinstance(agents, Agents)

    def test_agents_property_returns_same_instance(self, mock_client):
        """Test agents property returns cached instance."""
        agents1 = mock_client.agents
        agents2 = mock_client.agents
        assert agents1 is agents2

    def test_workflows_property_returns_workflows_instance(self, mock_client):
        """Test workflows property returns Workflows instance."""
        from swfte.workflows import Workflows

        workflows = mock_client.workflows
        assert isinstance(workflows, Workflows)

    def test_deployments_property_returns_deployments_instance(self, mock_client):
        """Test deployments property returns Deployments instance."""
        from swfte.deployments import Deployments

        deployments = mock_client.deployments
        assert isinstance(deployments, Deployments)

    def test_models_property_returns_models_instance(self, mock_client):
        """Test models property returns Models instance."""
        from swfte.models import Models

        models = mock_client.models
        assert isinstance(models, Models)

    def test_images_property_returns_images_instance(self, mock_client):
        """Test images property returns Images instance."""
        from swfte.images import Images

        images = mock_client.images
        assert isinstance(images, Images)

    def test_embeddings_property_returns_embeddings_instance(self, mock_client):
        """Test embeddings property returns Embeddings instance."""
        from swfte.embeddings import Embeddings

        embeddings = mock_client.embeddings
        assert isinstance(embeddings, Embeddings)

    def test_audio_property_returns_audio_instance(self, mock_client):
        """Test audio property returns Audio instance."""
        from swfte.audio import Audio

        audio = mock_client.audio
        assert isinstance(audio, Audio)

    def test_secrets_property_returns_secrets_instance(self, mock_client):
        """Test secrets property returns Secrets instance."""
        from swfte.secrets import Secrets

        secrets = mock_client.secrets
        assert isinstance(secrets, Secrets)

    def test_conversations_property_returns_conversations_instance(self, mock_client):
        """Test conversations property returns Conversations instance."""
        from swfte.conversations import Conversations

        conversations = mock_client.conversations
        assert isinstance(conversations, Conversations)
