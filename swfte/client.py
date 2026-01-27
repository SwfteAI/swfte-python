"""
Main client class for the Swfte SDK.
"""

import os
from typing import Optional
from .chat import Chat
from .images import Images
from .embeddings import Embeddings
from .audio import Audio
from .models import Models
from .agents import Agents
from .deployments import Deployments
from .workflows import Workflows
from .secrets import Secrets
from .conversations import Conversations


class SwfteClient:
    """
    Swfte API client for accessing AI models through the unified gateway.
    
    Args:
        api_key: Your Swfte API key. If not provided, reads from SWFTE_API_KEY env var.
        base_url: Base URL for the API. Defaults to https://api.swfte.com/v1/gateway
        timeout: Request timeout in seconds. Defaults to 60.
        max_retries: Maximum number of retries for failed requests. Defaults to 3.
    
    Example:
        client = SwfteClient(api_key="sk-swfte-...")
        response = client.chat.completions.create(
            model="openai:gpt-4",
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.swfte.com/v1/gateway",
        timeout: int = 60,
        max_retries: int = 3,
        workspace_id: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("SWFTE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Pass api_key parameter or set SWFTE_API_KEY environment variable."
            )
        
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.workspace_id = workspace_id or os.environ.get("SWFTE_WORKSPACE_ID")
        
        # Initialize resource handlers
        self._chat = None
        self._images = None
        self._embeddings = None
        self._audio = None
        self._models = None
        self._agents = None
        self._deployments = None
        self._workflows = None
        self._secrets = None
        self._conversations = None
    
    @property
    def chat(self) -> Chat:
        """Access chat completions API."""
        if self._chat is None:
            self._chat = Chat(self)
        return self._chat
    
    @property
    def images(self) -> Images:
        """Access image generation API."""
        if self._images is None:
            self._images = Images(self)
        return self._images
    
    @property
    def embeddings(self) -> Embeddings:
        """Access embeddings API."""
        if self._embeddings is None:
            self._embeddings = Embeddings(self)
        return self._embeddings
    
    @property
    def audio(self) -> Audio:
        """Access audio API (transcription, text-to-speech)."""
        if self._audio is None:
            self._audio = Audio(self)
        return self._audio
    
    @property
    def models(self) -> Models:
        """Access models listing API."""
        if self._models is None:
            self._models = Models(self)
        return self._models
    
    @property
    def agents(self) -> Agents:
        """Access agent management API."""
        if self._agents is None:
            self._agents = Agents(self)
        return self._agents
    
    @property
    def deployments(self) -> Deployments:
        """Access deployment management API (RunPod)."""
        if self._deployments is None:
            self._deployments = Deployments(self)
        return self._deployments
    
    @property
    def workflows(self) -> Workflows:
        """Access workflow management API."""
        if self._workflows is None:
            self._workflows = Workflows(self)
        return self._workflows

    @property
    def secrets(self) -> Secrets:
        """Access secrets management API."""
        if self._secrets is None:
            self._secrets = Secrets(self)
        return self._secrets

    @property
    def conversations(self) -> Conversations:
        """Access conversation management API."""
        if self._conversations is None:
            self._conversations = Conversations(self)
        return self._conversations

    def _get_headers(self) -> dict:
        """Get default headers for API requests."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"swfte-python/1.0.0",
        }
        if self.workspace_id:
            headers["X-Workspace-ID"] = self.workspace_id
        return headers

