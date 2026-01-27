"""
Conversation management for the Swfte SDK.
Handles conversation history with optimized message storage.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import requests


@dataclass
class Message:
    """Represents a message in a conversation."""
    id: str
    role: str
    content: str
    conversation_id: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict] = None
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create a Message from a dictionary."""
        return cls(
            id=data.get("id", ""),
            role=data.get("role", ""),
            content=data.get("content", ""),
            conversation_id=data.get("conversationId", data.get("conversation_id")),
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata"),
            tool_calls=data.get("toolCalls", data.get("tool_calls")),
            tool_call_id=data.get("toolCallId", data.get("tool_call_id")),
            name=data.get("name"),
        )


@dataclass
class Conversation:
    """Represents a conversation."""
    id: str
    workspace_id: str
    title: Optional[str] = None
    agent_id: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    message_count: int = 0
    total_tokens: int = 0
    metadata: Optional[Dict] = None
    messages: List[Message] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create a Conversation from a dictionary."""
        messages_data = data.get("messages", [])
        messages = [Message.from_dict(m) for m in messages_data]

        return cls(
            id=data.get("id", ""),
            workspace_id=data.get("workspaceId", data.get("workspace_id", "")),
            title=data.get("title"),
            agent_id=data.get("agentId", data.get("agent_id")),
            model=data.get("model"),
            system_prompt=data.get("systemPrompt", data.get("system_prompt")),
            created_at=data.get("createdAt", data.get("created_at")),
            updated_at=data.get("updatedAt", data.get("updated_at")),
            message_count=data.get("messageCount", data.get("message_count", 0)),
            total_tokens=data.get("totalTokens", data.get("total_tokens", 0)),
            metadata=data.get("metadata"),
            messages=messages,
        )


@dataclass
class MessagePage:
    """Represents a paginated page of messages."""
    messages: List[Message]
    has_more: bool
    next_token: Optional[str] = None
    total_count: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessagePage":
        """Create a MessagePage from a dictionary."""
        messages_data = data.get("messages", data.get("content", []))
        messages = [Message.from_dict(m) for m in messages_data]

        return cls(
            messages=messages,
            has_more=data.get("hasMore", data.get("has_more", False)),
            next_token=data.get("nextToken", data.get("next_token")),
            total_count=data.get("totalCount", data.get("total_count")),
        )


class Conversations:
    """
    Conversation management API for storing and managing conversation history.

    Example:
        client = SwfteClient(api_key="sk-swfte-...")

        # Create a conversation
        conversation = client.conversations.create(
            title="Chat about AI",
            model="gpt-4o"
        )

        # Add a message
        message = client.conversations.add_message(
            conversation.id,
            role="user",
            content="What is machine learning?"
        )

        # Get messages with pagination
        page = client.conversations.get_messages(conversation.id, limit=10)

        # Delete conversation
        client.conversations.delete(conversation.id)
    """

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        """Get the base URL for conversation endpoints."""
        base = self._client.base_url
        # Remove /gateway if present to get the service root
        if "/gateway" in base:
            base = base.replace("/v1/gateway", "").replace("/v2/gateway", "")
        return f"{base}/v1/conversations"

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
        title: Optional[str] = None,
        agent_id: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            title: Title for the conversation.
            agent_id: Associated agent ID.
            model: Model to use for the conversation.
            system_prompt: System prompt for the conversation.
            metadata: Additional metadata.

        Returns:
            The created Conversation.
        """
        payload = {}

        if title:
            payload["title"] = title
        if agent_id:
            payload["agentId"] = agent_id
        if model:
            payload["model"] = model
        if system_prompt:
            payload["systemPrompt"] = system_prompt
        if metadata:
            payload["metadata"] = metadata

        response = self._make_request("POST", self._get_base_url(), data=payload)
        return Conversation.from_dict(response)

    def get(self, conversation_id: str) -> Conversation:
        """
        Get a conversation by ID.

        Args:
            conversation_id: The conversation ID.

        Returns:
            The Conversation.
        """
        url = f"{self._get_base_url()}/{conversation_id}"
        response = self._make_request("GET", url)
        return Conversation.from_dict(response)

    def list(
        self,
        agent_id: Optional[str] = None,
        page: int = 0,
        size: int = 20,
    ) -> List[Conversation]:
        """
        List conversations.

        Args:
            agent_id: Filter by agent ID.
            page: Page number (0-based).
            size: Number of conversations per page.

        Returns:
            List of conversations.
        """
        params = {"page": page, "size": size}

        if agent_id:
            params["agentId"] = agent_id

        response = self._make_request("GET", self._get_base_url(), params=params)

        # Handle both list and paginated response formats
        if isinstance(response, list):
            return [Conversation.from_dict(c) for c in response]

        conversations_data = response.get("conversations", response.get("content", []))
        return [Conversation.from_dict(c) for c in conversations_data]

    def update(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Conversation:
        """
        Update a conversation.

        Args:
            conversation_id: The conversation ID.
            title: New title.
            metadata: New metadata.

        Returns:
            The updated Conversation.
        """
        payload = {}

        if title:
            payload["title"] = title
        if metadata:
            payload["metadata"] = metadata

        url = f"{self._get_base_url()}/{conversation_id}"
        response = self._make_request("PUT", url, data=payload)
        return Conversation.from_dict(response)

    def delete(self, conversation_id: str) -> None:
        """
        Delete a conversation.

        Args:
            conversation_id: The conversation ID to delete.
        """
        url = f"{self._get_base_url()}/{conversation_id}"
        self._make_request("DELETE", url)

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        name: Optional[str] = None,
        tool_calls: Optional[List[Dict]] = None,
        tool_call_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Message:
        """
        Add a message to a conversation.

        Args:
            conversation_id: The conversation ID.
            role: Message role ("user", "assistant", "system", "tool").
            content: Message content.
            name: Name of the message sender.
            tool_calls: Tool calls (for assistant messages).
            tool_call_id: Tool call ID (for tool response messages).
            metadata: Additional metadata.

        Returns:
            The created Message.
        """
        payload = {
            "role": role,
            "content": content,
        }

        if name:
            payload["name"] = name
        if tool_calls:
            payload["toolCalls"] = tool_calls
        if tool_call_id:
            payload["toolCallId"] = tool_call_id
        if metadata:
            payload["metadata"] = metadata

        url = f"{self._get_base_url()}/{conversation_id}/messages"
        response = self._make_request("POST", url, data=payload)
        return Message.from_dict(response)

    def get_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        before_token: Optional[str] = None,
        after_token: Optional[str] = None,
        order: str = "desc",
    ) -> MessagePage:
        """
        Get messages from a conversation with pagination.

        Args:
            conversation_id: The conversation ID.
            limit: Maximum number of messages to return.
            before_token: Cursor for messages before this token.
            after_token: Cursor for messages after this token.
            order: Sort order ("asc" or "desc").

        Returns:
            A MessagePage with messages and pagination info.
        """
        params = {"limit": limit, "order": order}

        if before_token:
            params["beforeToken"] = before_token
        if after_token:
            params["afterToken"] = after_token

        url = f"{self._get_base_url()}/{conversation_id}/messages"
        response = self._make_request("GET", url, params=params)
        return MessagePage.from_dict(response)

    def get_message(self, conversation_id: str, message_id: str) -> Message:
        """
        Get a specific message.

        Args:
            conversation_id: The conversation ID.
            message_id: The message ID.

        Returns:
            The Message.
        """
        url = f"{self._get_base_url()}/{conversation_id}/messages/{message_id}"
        response = self._make_request("GET", url)
        return Message.from_dict(response)

    def delete_message(self, conversation_id: str, message_id: str) -> None:
        """
        Delete a message from a conversation.

        Args:
            conversation_id: The conversation ID.
            message_id: The message ID to delete.
        """
        url = f"{self._get_base_url()}/{conversation_id}/messages/{message_id}"
        self._make_request("DELETE", url)

    def clear_messages(self, conversation_id: str) -> None:
        """
        Clear all messages from a conversation.

        Args:
            conversation_id: The conversation ID.
        """
        url = f"{self._get_base_url()}/{conversation_id}/messages/clear"
        self._make_request("POST", url)

    def get_context(
        self,
        conversation_id: str,
        max_tokens: int = 4000,
        include_system: bool = True,
    ) -> List[Message]:
        """
        Get conversation context optimized for LLM input.

        Args:
            conversation_id: The conversation ID.
            max_tokens: Maximum tokens for context window.
            include_system: Include system prompt in context.

        Returns:
            List of messages for context.
        """
        params = {
            "maxTokens": max_tokens,
            "includeSystem": str(include_system).lower(),
        }

        url = f"{self._get_base_url()}/{conversation_id}/context"
        response = self._make_request("GET", url, params=params)

        messages_data = response.get("messages", [])
        return [Message.from_dict(m) for m in messages_data]

    def fork(
        self,
        conversation_id: str,
        from_message_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Conversation:
        """
        Fork a conversation from a specific point.

        Args:
            conversation_id: The conversation ID to fork.
            from_message_id: Message ID to fork from (includes this message).
            title: Title for the forked conversation.

        Returns:
            The new forked Conversation.
        """
        payload = {}

        if from_message_id:
            payload["fromMessageId"] = from_message_id
        if title:
            payload["title"] = title

        url = f"{self._get_base_url()}/{conversation_id}/fork"
        response = self._make_request("POST", url, data=payload)
        return Conversation.from_dict(response)

    def export(
        self,
        conversation_id: str,
        format: str = "json",
    ) -> Dict:
        """
        Export a conversation.

        Args:
            conversation_id: The conversation ID.
            format: Export format ("json", "markdown").

        Returns:
            Exported conversation data.
        """
        params = {"format": format}
        url = f"{self._get_base_url()}/{conversation_id}/export"
        return self._make_request("GET", url, params=params)

    def summarize(
        self,
        conversation_id: str,
        max_length: int = 500,
    ) -> str:
        """
        Get a summary of the conversation.

        Args:
            conversation_id: The conversation ID.
            max_length: Maximum length of summary.

        Returns:
            Conversation summary.
        """
        params = {"maxLength": max_length}
        url = f"{self._get_base_url()}/{conversation_id}/summarize"
        response = self._make_request("GET", url, params=params)
        return response.get("summary", "")

