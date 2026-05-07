"""
MCP V2 resource client — Model Context Protocol server connect, tool list,
execute, batch, analytics. See https://www.swfte.com/products/mcp.
"""

from typing import Any, Dict, List, Optional

from ._base import V2Resource


class Mcp(V2Resource):
    """Client for ``/api/v2/mcp``."""

    _path_prefix = "/api/v2/mcp"

    # ---- servers ------------------------------------------------------

    def connect_server(
        self,
        provider_id: str,
        endpoint: str,
        auth: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Connect a remote MCP server."""
        payload: Dict[str, Any] = {
            "providerId": provider_id,
            "endpoint": endpoint,
            **kwargs,
        }
        if auth is not None:
            payload["auth"] = auth
        return self._request("POST", self._url("/servers/connect"), data=payload)

    def list_servers(self) -> List[Dict[str, Any]]:
        """List connected MCP servers."""
        return self._request("GET", self._url("/servers"))

    def disconnect_server(self, provider_id: str) -> None:
        """Disconnect a connected MCP server."""
        self._request("DELETE", self._url(f"/servers/{provider_id}"))

    # ---- tools --------------------------------------------------------

    def list_tools(self, **filters: Any) -> List[Dict[str, Any]]:
        """List available MCP tools."""
        return self._request("GET", self._url("/tools"), params=filters or None)

    def tool_schema(self, tool_id: str) -> Dict[str, Any]:
        """Return the JSON schema describing a tool's inputs/outputs."""
        return self._request("GET", self._url(f"/tools/{tool_id}/schema"))

    def execute(self, tool_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with the given arguments."""
        return self._request(
            "POST",
            self._url(f"/tools/{tool_id}/execute"),
            data={"arguments": arguments},
        )

    def batch_execute(self, calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute many tool calls in a single round-trip."""
        return self._request("POST", self._url("/tools/batch-execute"), data={"calls": calls})

    def tool_status(self, tool_id: str) -> Dict[str, Any]:
        """Return current status of a tool."""
        return self._request("GET", self._url(f"/tools/{tool_id}/status"))

    # ---- ops ----------------------------------------------------------

    def analytics(self, **filters: Any) -> Dict[str, Any]:
        """Return tool usage analytics."""
        return self._request("GET", self._url("/analytics"), params=filters or None)

    def health_check(self, provider_id: Optional[str] = None) -> Dict[str, Any]:
        """Run a health check across servers (or a single one when ``provider_id`` is set)."""
        body = {"providerId": provider_id} if provider_id else {}
        return self._request("POST", self._url("/health-check"), data=body)
