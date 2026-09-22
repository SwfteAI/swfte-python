"""
Main client class for the Swfte SDK.
"""

import os
from typing import Any, Dict, Optional

import requests

from ._base import _service_root

from .agent_wizard import AgentWizard
from .agents import Agents
from .analytics import Analytics
from .audio import Audio
from .audit import Audit
from .catalog import Catalog
from .chat import Chat
from .chatflows import ChatFlows
from .conversations import Conversations
from .cost_control import CostControl
from .datasets import Datasets
from .deployments import Deployments
from .documents import Documents
from .embeddings import Embeddings
from .exceptions import APIError, AuthenticationError, RateLimitError, SwfteError
from .files import Files
from .images import Images
from .marketplace import Marketplace
from .mcp import Mcp
from .models import Models
from .modules import Modules
from .rag import Rag
from .secrets import Secrets
from .voice_calls import VoiceCalls
from .workflows import Workflows


class SwfteClient:
    """
    Swfte API client for accessing AI models, agents, workflows, chatflows,
    RAG, voice and MCP through the unified Swfte platform.

    Args:
        api_key: Your Swfte API key. If not provided, reads from SWFTE_API_KEY env var.
        base_url: Gateway URL (chat completions, images, embeddings, audio, models).
            Defaults to https://api.swfte.com/agents/v2/gateway.
        timeout: Request timeout in seconds. Defaults to 60.
        max_retries: Maximum number of retries for failed requests. Defaults to 3.
        workspace_id: Workspace to scope requests to. Reads from SWFTE_WORKSPACE_ID.
        api_base_url: Root of the agents-service API, where agent chat
            (``/v1/agents/...``), workflow invoke (``/v2/workflows/...``), the
            catalog (``/v2/catalog/...``) and the other management resources live.
            Defaults to SWFTE_API_BASE_URL, else ``base_url`` with its trailing
            ``/v2/gateway``, ``/v1/gateway`` or ``/gateway`` removed
            (https://api.swfte.com/agents by default).

    Example:
        client = SwfteClient(api_key="sk-swfte-...")
        response = client.chat.completions.create(
            model="openai:gpt-4",
            messages=[{"role": "user", "content": "Hello!"}],
        )

    Learn more at https://www.swfte.com.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.swfte.com/agents/v2/gateway",
        timeout: int = 60,
        max_retries: int = 3,
        workspace_id: Optional[str] = None,
        api_base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("SWFTE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Pass api_key parameter or set SWFTE_API_KEY environment variable."
            )

        self.base_url = base_url.rstrip("/")
        explicit_api_base = api_base_url or os.environ.get("SWFTE_API_BASE_URL")
        self.api_base_url = (
            explicit_api_base.rstrip("/") if explicit_api_base else _service_root(self.base_url)
        )
        self.timeout = timeout
        self.max_retries = max_retries
        self.workspace_id = workspace_id or os.environ.get("SWFTE_WORKSPACE_ID")

        # Lazy-initialised resource handlers (existing surface).
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
        self._analytics = None

        # V2 resources added in 1.1.0.
        self._chatflows = None
        self._datasets = None
        self._documents = None
        self._files = None
        self._rag = None
        self._mcp = None
        self._modules = None
        self._marketplace = None
        self._voice_calls = None
        self._audit = None
        self._cost_control = None
        self._agent_wizard = None
        self._catalog = None

    # ---- existing resources -------------------------------------------------

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
        """Access deployment management API."""
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

    @property
    def analytics(self) -> Analytics:
        """Access prompt analytics, insights, and conversation history."""
        if self._analytics is None:
            self._analytics = Analytics(self)
        return self._analytics

    # ---- V2 resources (1.1.0) ----------------------------------------------

    @property
    def chatflows(self) -> ChatFlows:
        """Conversational form runtime — V2 ChatFlow API."""
        if self._chatflows is None:
            self._chatflows = ChatFlows(self)
        return self._chatflows

    @property
    def datasets(self) -> Datasets:
        """Datasets that group RAG documents."""
        if self._datasets is None:
            self._datasets = Datasets(self)
        return self._datasets

    @property
    def documents(self) -> Documents:
        """Documents inside a dataset."""
        if self._documents is None:
            self._documents = Documents(self)
        return self._documents

    @property
    def files(self) -> Files:
        """File upload/download."""
        if self._files is None:
            self._files = Files(self)
        return self._files

    @property
    def rag(self) -> Rag:
        """Hybrid retrieval and reranking."""
        if self._rag is None:
            self._rag = Rag(self)
        return self._rag

    @property
    def mcp(self) -> Mcp:
        """Model Context Protocol servers and tools."""
        if self._mcp is None:
            self._mcp = Mcp(self)
        return self._mcp

    @property
    def modules(self) -> Modules:
        """Reusable modules — bundles of agents, workflows and tools."""
        if self._modules is None:
            self._modules = Modules(self)
        return self._modules

    @property
    def marketplace(self) -> Marketplace:
        """Marketplace browse and install."""
        if self._marketplace is None:
            self._marketplace = Marketplace(self)
        return self._marketplace

    @property
    def voice_calls(self) -> VoiceCalls:
        """Voice call records, transcripts and recordings."""
        if self._voice_calls is None:
            self._voice_calls = VoiceCalls(self)
        return self._voice_calls

    @property
    def audit(self) -> Audit:
        """Audit events query and export."""
        if self._audit is None:
            self._audit = Audit(self)
        return self._audit

    @property
    def cost_control(self) -> CostControl:
        """Routing rules, usage caps, usage statistics."""
        if self._cost_control is None:
            self._cost_control = CostControl(self)
        return self._cost_control

    @property
    def agent_wizard(self) -> AgentWizard:
        """LLM-powered agent generation wizard."""
        if self._agent_wizard is None:
            self._agent_wizard = AgentWizard(self)
        return self._agent_wizard

    @property
    def catalog(self) -> Catalog:
        """Catalog — search proven artifacts, read their evidence and invoke contract."""
        if self._catalog is None:
            self._catalog = Catalog(self)
        return self._catalog

    # ---- request plumbing --------------------------------------------------

    def _get_headers(self) -> dict:
        """Get default headers for API requests."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "swfte-python/1.1.0",
        }
        if self.workspace_id:
            headers["X-Workspace-ID"] = self.workspace_id
            headers["x-workspace-id"] = self.workspace_id
        return headers

    def _api_request(
        self,
        method: str,
        path: str,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """One request against the agents-service API (``api_base_url``).

        Never retried: it backs non-idempotent calls such as agent chat and
        workflow invoke, where a silent retry could run (and bill) twice.
        Errors are typed: 401/403 -> AuthenticationError, 429 -> RateLimitError,
        any other non-2xx -> APIError (``status_code``, ``body``). Returns the
        parsed JSON body, or ``None`` for an empty body.
        """
        clean_params = None
        if params:
            clean_params = {}
            for key, value in params.items():
                if value is None or value == "":
                    continue
                if isinstance(value, (list, tuple)):
                    value = ",".join(str(v) for v in value)
                clean_params[key] = value
            clean_params = clean_params or None

        try:
            response = requests.request(
                method=method,
                url=f"{self.api_base_url}{path}",
                headers=self._get_headers(),
                json=json,
                params=clean_params,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise SwfteError(f"Request timed out: {method} {path}") from exc

        text = response.text or ""
        body: Any = None
        if text:
            try:
                body = response.json()
            except ValueError:
                body = text

        status = response.status_code
        if status < 200 or status >= 300:
            message = f"API error: {status} {method} {path}" + (f" - {text}" if text else "")
            if status in (401, 403):
                raise AuthenticationError(message)
            if status == 429:
                raise RateLimitError(message)
            raise APIError(message, status_code=status, body=body)
        return body

