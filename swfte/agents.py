"""
Agent management for the Swfte SDK.
"""

import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from urllib.parse import quote
import requests

from .exceptions import InvalidRequestError

#: ``user_id`` used by :meth:`Agents.chat` when none is given. The agents
#: service keeps one conversation space per (agent, user_id), so every call
#: that omits ``user_id`` shares this identity. Pass your own end-user id when
#: several people talk to the same agent through your application.
DEFAULT_CHAT_USER_ID = "sdk-user"


@dataclass
class AgentChatResponse:
    """Reply from ``POST /v1/agents/{agent_id}/chat/{user_id}``.

    ``response`` is the agent's reply text. Some agents-service builds return
    it under ``content``; both are normalised to ``response``. ``raw`` is the
    full response body.
    """
    response: str
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    duration_ms: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "AgentChatResponse":
        data = data if isinstance(data, dict) else {}
        reply = data.get("response")
        if reply is None:
            reply = data.get("content")
        if reply is None:
            reply = ""
        if not isinstance(reply, str):
            reply = json.dumps(reply)
        return cls(
            response=reply,
            conversation_id=data.get("conversationId"),
            session_id=data.get("sessionId"),
            agent_id=data.get("agentId"),
            user_id=data.get("userId"),
            request_id=data.get("requestId"),
            model=data.get("model"),
            provider=data.get("provider"),
            duration_ms=data.get("durationMs"),
            input_tokens=data.get("inputTokens"),
            output_tokens=data.get("outputTokens"),
            raw=data,
        )


@dataclass
class Agent:
    """Represents an AI agent."""
    id: str
    agent_name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    active: bool = True
    verified: bool = False
    input_type: str = "TEXT"
    output_type: str = "TEXT"
    workspace_id: Optional[str] = None
    mode: Optional[str] = None
    workflow_id: Optional[str] = None
    use_workflow: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        """Create an Agent from a dictionary."""
        return cls(
            id=data.get("id", ""),
            agent_name=data.get("agentName", data.get("agent_name", "")),
            description=data.get("description"),
            system_prompt=data.get("systemPrompt", data.get("system_prompt")),
            provider=data.get("provider"),
            model=data.get("model"),
            temperature=data.get("temperature"),
            max_tokens=data.get("maxTokens", data.get("max_tokens")),
            active=data.get("active", True),
            verified=data.get("verified", False),
            input_type=data.get("inputType", data.get("input_type", "TEXT")),
            output_type=data.get("outputType", data.get("output_type", "TEXT")),
            workspace_id=data.get("workspaceId", data.get("workspace_id")),
            mode=data.get("mode"),
            workflow_id=data.get("workflowId", data.get("workflow_id")),
            use_workflow=data.get("useWorkflow", data.get("use_workflow", False)),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Agent to dictionary."""
        return {
            "id": self.id,
            "agentName": self.agent_name,
            "description": self.description,
            "systemPrompt": self.system_prompt,
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "maxTokens": self.max_tokens,
            "active": self.active,
            "verified": self.verified,
            "inputType": self.input_type,
            "outputType": self.output_type,
            "workspaceId": self.workspace_id,
            "mode": self.mode,
            "workflowId": self.workflow_id,
            "useWorkflow": self.use_workflow,
        }


class Agents:
    """
    Agent management API for creating, updating, and managing AI agents.
    
    Example:
        client = SwfteClient(api_key="sk-swfte-...")
        
        # Create an agent
        agent = client.agents.create(
            name="My Assistant",
            system_prompt="You are a helpful assistant.",
            provider="OPENAI",
            model="gpt-4"
        )
        
        # Get agent details
        agent = client.agents.get(agent.id)
        
        # List all agents
        agents = client.agents.list()

        # Chat with it (reply text is .response)
        reply = client.agents.chat(agent.id, "Hello!", user_id="user-42")
        
        # Delete an agent
        client.agents.delete(agent.id)
    """
    
    def __init__(self, client):
        self._client = client
    
    def _get_base_url(self) -> str:
        """Get the base URL for agent endpoints."""
        base = self._client.api_base_url
        return f"{base}/v1/agents"

    def _get_v2_base_url(self) -> str:
        """Get the base URL for V2 agent endpoints."""
        base = self._client.api_base_url
        return f"{base}/v2/agents"
    
    def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """Make an HTTP request."""
        headers = self._client._get_headers()
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params,
            timeout=self._client.timeout,
        )
        
        response.raise_for_status()
        
        if response.content:
            return response.json()
        return {}
    
    def create(
        self,
        name: str,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        provider: str = "OPENAI",
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        mode: str = "agent-chat",
        **kwargs,
    ) -> Agent:
        """
        Create a new agent.
        
        Args:
            name: The name of the agent.
            description: A description of the agent.
            system_prompt: The system prompt for the agent.
            provider: The AI provider (OPENAI, ANTHROPIC, etc.).
            model: The model to use.
            temperature: The temperature for generation.
            max_tokens: Maximum tokens for generation.
            mode: Agent mode (agent-chat, workflow, etc.).
            **kwargs: Additional agent properties.
        
        Returns:
            The created Agent.
        """
        payload = {
            "agentName": name,
            "description": description,
            "systemPrompt": system_prompt,
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "maxTokens": max_tokens,
            "mode": mode,
            **kwargs,
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        response = self._make_request("POST", self._get_base_url(), data=payload)
        return Agent.from_dict(response)
    
    def get(self, agent_id: str) -> Agent:
        """
        Get an agent by ID.
        
        Args:
            agent_id: The ID of the agent.
        
        Returns:
            The Agent.
        """
        url = f"{self._get_base_url()}/{agent_id}"
        response = self._make_request("GET", url)
        return Agent.from_dict(response)
    
    def update(
        self,
        agent_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Agent:
        """
        Update an existing agent.
        
        Args:
            agent_id: The ID of the agent to update.
            name: New name for the agent.
            description: New description.
            system_prompt: New system prompt.
            provider: New provider.
            model: New model.
            temperature: New temperature.
            max_tokens: New max tokens.
            **kwargs: Additional properties to update.
        
        Returns:
            The updated Agent.
        """
        # First get the current agent
        current = self.get(agent_id)
        
        # Merge updates
        payload = current.to_dict()
        if name is not None:
            payload["agentName"] = name
        if description is not None:
            payload["description"] = description
        if system_prompt is not None:
            payload["systemPrompt"] = system_prompt
        if provider is not None:
            payload["provider"] = provider
        if model is not None:
            payload["model"] = model
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["maxTokens"] = max_tokens
        
        payload.update(kwargs)
        
        url = f"{self._get_base_url()}/{agent_id}"
        response = self._make_request("PUT", url, data=payload)
        return Agent.from_dict(response)
    
    def patch(self, agent_id: str, **updates) -> Agent:
        """
        Partially update an agent using PATCH.
        
        Args:
            agent_id: The ID of the agent to update.
            **updates: Fields to update.
        
        Returns:
            The updated Agent.
        """
        url = f"{self._get_v2_base_url()}/{agent_id}"
        response = self._make_request("PATCH", url, data=updates)
        return Agent.from_dict(response)
    
    def delete(self, agent_id: str) -> None:
        """
        Delete an agent.
        
        Args:
            agent_id: The ID of the agent to delete.
        """
        url = f"{self._get_base_url()}/{agent_id}"
        self._make_request("DELETE", url)
    
    def list(
        self,
        page: int = 1,
        size: int = 20,
    ) -> List[Agent]:
        """
        List all agents.
        
        Args:
            page: Page number (1-based).
            size: Number of agents per page.
        
        Returns:
            List of agents.
        """
        params = {"page": page, "size": size}
        response = self._make_request("GET", self._get_base_url(), params=params)
        
        agents_data = response.get("agents", [])
        return [Agent.from_dict(a) for a in agents_data]
    
    def get_io_types(self) -> Dict[str, List[Dict]]:
        """
        Get available input/output types.
        
        Returns:
            Dictionary with inputTypes and outputTypes.
        """
        url = f"{self._get_base_url()}/io-types"
        return self._make_request("GET", url)
    
    def get_model_options(self, provider: str) -> List[Dict]:
        """
        Get available model options for a provider.
        
        Args:
            provider: The provider name (OPENAI, ANTHROPIC, etc.).
        
        Returns:
            List of model options.
        """
        url = f"{self._get_base_url()}/models/{provider.upper()}"
        return self._make_request("GET", url)
    
    def associate_workflow(self, agent_id: str, workflow_id: str) -> Agent:
        """
        Associate a workflow with an agent.
        
        Args:
            agent_id: The ID of the agent.
            workflow_id: The ID of the workflow to associate.
        
        Returns:
            The updated Agent.
        """
        url = f"{self._get_v2_base_url()}/{agent_id}/workflow"
        response = self._make_request("POST", url, data={"workflowId": workflow_id})
        return Agent.from_dict(response)
    
    def update_avatar(self, agent_id: str, avatar_config: Dict[str, Any]) -> Agent:
        """
        Update agent avatar configuration.
        
        Args:
            agent_id: The ID of the agent.
            avatar_config: Avatar configuration dictionary.
        
        Returns:
            The updated Agent.
        """
        url = f"{self._get_v2_base_url()}/{agent_id}/avatar"
        response = self._make_request("PATCH", url, data=avatar_config)
        return Agent.from_dict(response)
    
    def get_system_agents(self) -> List[Dict]:
        """
        Get system agents.
        
        Returns:
            List of system agents.
        """
        url = f"{self._get_base_url()}/system"
        return self._make_request("GET", url)

    def chat(
        self,
        agent_id: str,
        message: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> AgentChatResponse:
        """
        Send one message to an agent and return its reply.

        ``POST {api_base_url}/v1/agents/{agent_id}/chat/{user_id}`` with body
        ``{"message": ..., "conversationId": ...}``. Runs the agent's full
        configuration (tools, knowledge, memory) and keeps history per
        (agent, user_id). Not retried: a retry would send the message twice.

        Args:
            agent_id: The agent to talk to.
            message: The user's message.
            user_id: Conversation owner. Defaults to ``DEFAULT_CHAT_USER_ID`` ("sdk-user").
            conversation_id: Continue an earlier conversation.

        Returns:
            AgentChatResponse with ``response`` (reply text) and ``conversation_id``.

        Raises:
            AuthenticationError (401/403), RateLimitError (429), APIError (other non-2xx).
        """
        if not agent_id:
            raise InvalidRequestError("agent_id is required")
        if not isinstance(message, str) or not message:
            raise InvalidRequestError("message must be a non-empty string")
        uid = user_id or DEFAULT_CHAT_USER_ID
        body: Dict[str, Any] = {"message": message}
        if conversation_id:
            body["conversationId"] = conversation_id
        raw = self._client._api_request(
            "POST",
            f"/v1/agents/{quote(agent_id, safe='')}/chat/{quote(uid, safe='')}",
            json=body,
        )
        return AgentChatResponse.from_dict(raw)

