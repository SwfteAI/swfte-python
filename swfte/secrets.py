"""
Secret management for the Swfte SDK.
Handles creation, retrieval, and management of secrets (API keys, OAuth tokens, MCP tokens).
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import requests


class SecretType(Enum):
    """Secret type enumeration."""
    MANUAL = "MANUAL"
    OAUTH = "OAUTH"
    MCP = "MCP"


class SecretStatus(Enum):
    """Secret status enumeration."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    PENDING = "PENDING"


@dataclass
class Secret:
    """Represents a secret."""
    id: str
    name: str
    workspace_id: str
    secret_type: SecretType
    status: SecretStatus
    description: Optional[str] = None
    category: Optional[str] = None
    environment: Optional[str] = None
    tool_id: Optional[str] = None
    provider: Optional[str] = None
    masked_value: Optional[str] = None
    expires_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_used_at: Optional[str] = None
    metadata: Optional[Dict] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Secret":
        """Create a Secret from a dictionary."""
        secret_type_str = data.get("secretType", data.get("secret_type", "MANUAL"))
        try:
            secret_type = SecretType(secret_type_str)
        except ValueError:
            secret_type = SecretType.MANUAL

        status_str = data.get("status", "ACTIVE")
        try:
            status = SecretStatus(status_str)
        except ValueError:
            status = SecretStatus.ACTIVE

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            workspace_id=data.get("workspaceId", data.get("workspace_id", "")),
            secret_type=secret_type,
            status=status,
            description=data.get("description"),
            category=data.get("category"),
            environment=data.get("environment"),
            tool_id=data.get("toolId", data.get("tool_id")),
            provider=data.get("provider"),
            masked_value=data.get("maskedValue", data.get("masked_value")),
            expires_at=data.get("expiresAt", data.get("expires_at")),
            created_at=data.get("createdAt", data.get("created_at")),
            updated_at=data.get("updatedAt", data.get("updated_at")),
            last_used_at=data.get("lastUsedAt", data.get("last_used_at")),
            metadata=data.get("metadata"),
        )


@dataclass
class OAuthToken:
    """Represents an OAuth token."""
    id: str
    provider: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    scope: Optional[str] = None
    expires_in: Optional[int] = None
    expires_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OAuthToken":
        """Create an OAuthToken from a dictionary."""
        return cls(
            id=data.get("id", ""),
            provider=data.get("provider", ""),
            access_token=data.get("accessToken", data.get("access_token")),
            refresh_token=data.get("refreshToken", data.get("refresh_token")),
            token_type=data.get("tokenType", data.get("token_type")),
            scope=data.get("scope"),
            expires_in=data.get("expiresIn", data.get("expires_in")),
            expires_at=data.get("expiresAt", data.get("expires_at")),
        )


class Secrets:
    """
    Secret management API for storing and managing API keys, OAuth tokens, and MCP tokens.

    Example:
        client = SwfteClient(api_key="sk-swfte-...")

        # Create a secret
        secret = client.secrets.create(
            name="openai-api-key",
            value="sk-...",
            description="OpenAI API key for production"
        )

        # List secrets
        secrets = client.secrets.list()

        # Delete a secret
        client.secrets.delete(secret.id)
    """

    def __init__(self, client):
        self._client = client

    def _get_base_url(self) -> str:
        """Get the base URL for secret endpoints."""
        base = self._client.base_url
        # Remove /gateway if present to get the service root
        if "/gateway" in base:
            base = base.replace("/v1/gateway", "").replace("/v2/gateway", "")
        return f"{base}/v1/secrets"

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
        value: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        environment: Optional[str] = None,
        tool_id: Optional[str] = None,
        expires_at: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Secret:
        """
        Create a new manual secret.

        Args:
            name: The name of the secret.
            value: The secret value.
            description: Description of the secret.
            category: Category for organization.
            environment: Environment (e.g., "production", "development").
            tool_id: Associated tool ID if applicable.
            expires_at: Expiration date (ISO format).
            metadata: Additional metadata.

        Returns:
            The created Secret.
        """
        payload = {
            "name": name,
            "value": value,
        }

        if description:
            payload["description"] = description
        if category:
            payload["category"] = category
        if environment:
            payload["environment"] = environment
        if tool_id:
            payload["toolId"] = tool_id
        if expires_at:
            payload["expiresAt"] = expires_at
        if metadata:
            payload["metadata"] = metadata

        response = self._make_request("POST", self._get_base_url(), data=payload)
        return Secret.from_dict(response)

    def create_oauth(
        self,
        provider: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_type: str = "Bearer",
        scope: Optional[str] = None,
        expires_in: Optional[int] = None,
        tool_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Secret:
        """
        Create an OAuth token secret.

        Args:
            provider: OAuth provider name (e.g., "google", "github").
            access_token: The access token.
            refresh_token: The refresh token.
            token_type: Token type (default: "Bearer").
            scope: OAuth scope.
            expires_in: Token expiration in seconds.
            tool_id: Associated tool ID.
            metadata: Additional metadata.

        Returns:
            The created Secret.
        """
        payload = {
            "provider": provider,
            "accessToken": access_token,
            "tokenType": token_type,
        }

        if refresh_token:
            payload["refreshToken"] = refresh_token
        if scope:
            payload["scope"] = scope
        if expires_in:
            payload["expiresIn"] = expires_in
        if tool_id:
            payload["toolId"] = tool_id
        if metadata:
            payload["metadata"] = metadata

        url = f"{self._get_base_url()}/oauth"
        response = self._make_request("POST", url, data=payload)
        return Secret.from_dict(response)

    def create_mcp(
        self,
        tool_id: str,
        token: str,
        token_type: str = "Bearer",
        scope: Optional[str] = None,
        expires_in: Optional[int] = None,
        metadata: Optional[Dict] = None,
    ) -> Secret:
        """
        Create an MCP token secret.

        Args:
            tool_id: The MCP tool ID.
            token: The MCP token.
            token_type: Token type (default: "Bearer").
            scope: Token scope.
            expires_in: Token expiration in seconds.
            metadata: Additional metadata.

        Returns:
            The created Secret.
        """
        payload = {
            "toolId": tool_id,
            "token": token,
            "tokenType": token_type,
        }

        if scope:
            payload["scope"] = scope
        if expires_in:
            payload["expiresIn"] = expires_in
        if metadata:
            payload["metadata"] = metadata

        url = f"{self._get_base_url()}/mcp"
        response = self._make_request("POST", url, data=payload)
        return Secret.from_dict(response)

    def get(self, secret_id: str) -> Secret:
        """
        Get a secret by ID.

        Args:
            secret_id: The secret ID.

        Returns:
            The Secret.
        """
        url = f"{self._get_base_url()}/{secret_id}"
        response = self._make_request("GET", url)
        return Secret.from_dict(response)

    def list(
        self,
        environment: Optional[str] = None,
        tool_id: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 0,
        size: int = 20,
    ) -> List[Secret]:
        """
        List secrets with optional filtering.

        Args:
            environment: Filter by environment.
            tool_id: Filter by tool ID.
            category: Filter by category.
            status: Filter by status.
            page: Page number (0-based).
            size: Number of secrets per page.

        Returns:
            List of secrets.
        """
        params = {"page": page, "size": size}

        if environment:
            params["environment"] = environment
        if tool_id:
            params["toolId"] = tool_id
        if category:
            params["category"] = category
        if status:
            params["status"] = status

        response = self._make_request("GET", self._get_base_url(), params=params)

        # Handle both list and paginated response formats
        if isinstance(response, list):
            return [Secret.from_dict(s) for s in response]

        secrets_data = response.get("secrets", response.get("content", []))
        return [Secret.from_dict(s) for s in secrets_data]

    def update(
        self,
        secret_id: str,
        name: Optional[str] = None,
        value: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        environment: Optional[str] = None,
        expires_at: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Secret:
        """
        Update a secret.

        Args:
            secret_id: The secret ID.
            name: New name.
            value: New value.
            description: New description.
            category: New category.
            environment: New environment.
            expires_at: New expiration date.
            metadata: New metadata.

        Returns:
            The updated Secret.
        """
        payload = {}

        if name:
            payload["name"] = name
        if value:
            payload["value"] = value
        if description:
            payload["description"] = description
        if category:
            payload["category"] = category
        if environment:
            payload["environment"] = environment
        if expires_at:
            payload["expiresAt"] = expires_at
        if metadata:
            payload["metadata"] = metadata

        url = f"{self._get_base_url()}/{secret_id}"
        response = self._make_request("PUT", url, data=payload)
        return Secret.from_dict(response)

    def delete(self, secret_id: str) -> None:
        """
        Delete a secret.

        Args:
            secret_id: The secret ID to delete.
        """
        url = f"{self._get_base_url()}/{secret_id}"
        self._make_request("DELETE", url)

    def refresh_oauth(self, secret_id: str) -> Secret:
        """
        Refresh an OAuth token.

        Args:
            secret_id: The OAuth secret ID.

        Returns:
            The refreshed Secret.
        """
        url = f"{self._get_base_url()}/{secret_id}/refresh"
        response = self._make_request("POST", url)
        return Secret.from_dict(response)

    def revoke(self, secret_id: str) -> Secret:
        """
        Revoke a secret.

        Args:
            secret_id: The secret ID to revoke.

        Returns:
            The revoked Secret.
        """
        url = f"{self._get_base_url()}/{secret_id}/revoke"
        response = self._make_request("POST", url)
        return Secret.from_dict(response)

    def get_value(self, secret_id: str) -> str:
        """
        Get the actual secret value (decrypted).

        Args:
            secret_id: The secret ID.

        Returns:
            The secret value.
        """
        url = f"{self._get_base_url()}/{secret_id}/value"
        response = self._make_request("GET", url)
        return response.get("value", "")

    def rotate(
        self,
        secret_id: str,
        new_value: str,
    ) -> Secret:
        """
        Rotate a secret with a new value.

        Args:
            secret_id: The secret ID.
            new_value: The new secret value.

        Returns:
            The rotated Secret.
        """
        payload = {"value": new_value}
        url = f"{self._get_base_url()}/{secret_id}/rotate"
        response = self._make_request("POST", url, data=payload)
        return Secret.from_dict(response)

