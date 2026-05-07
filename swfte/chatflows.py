"""
ChatFlows V2 resource client.

ChatFlows are conversational forms — onboarding, lead-qualification, support,
surveys — with field extraction, validation, branching, and multi-channel
delivery. See https://www.swfte.com/products/chatflows for product details.
"""

from typing import Any, Dict, List, Optional

from ._base import V2Resource


class ChatFlows(V2Resource):
    """Client for ``/v2/chatflows``, ``/v2/chatflows/builder`` and version sub-routes."""

    _path_prefix = "/v2/chatflows"

    # ---- core CRUD ----------------------------------------------------

    def create(self, definition: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chatflow from a definition payload."""
        return self._request("POST", self._url(""), data=definition)

    def get(self, chatflow_id: str) -> Dict[str, Any]:
        """Fetch a chatflow by id."""
        return self._request("GET", self._url(f"/{chatflow_id}"))

    def list(
        self,
        page: int = 0,
        size: int = 20,
        **filters: Any,
    ) -> Dict[str, Any]:
        """List chatflows in the current workspace."""
        params: Dict[str, Any] = {"page": page, "size": size, **filters}
        return self._request("GET", self._url(""), params=params)

    def update(self, chatflow_id: str, definition: Dict[str, Any]) -> Dict[str, Any]:
        """Replace a chatflow's definition."""
        return self._request("PUT", self._url(f"/{chatflow_id}"), data=definition)

    def delete(self, chatflow_id: str) -> None:
        """Delete a chatflow."""
        self._request("DELETE", self._url(f"/{chatflow_id}"))

    # ---- lifecycle ----------------------------------------------------

    def validate(self, chatflow_id: str) -> Dict[str, Any]:
        """Validate the chatflow definition (server-side checks)."""
        return self._request("POST", self._url(f"/{chatflow_id}/validate"))

    def deploy(self, chatflow_id: str, channel: Optional[str] = None) -> Dict[str, Any]:
        """Deploy a chatflow to its configured channels."""
        body = {"channel": channel} if channel else None
        return self._request("POST", self._url(f"/{chatflow_id}/deploy"), data=body)

    def undeploy(self, chatflow_id: str) -> Dict[str, Any]:
        """Undeploy a previously-deployed chatflow."""
        return self._request("POST", self._url(f"/{chatflow_id}/undeploy"))

    # ---- sessions -----------------------------------------------------

    def start_session(
        self,
        chatflow_id: str,
        channel: str = "WEB",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Start a new chatflow session."""
        body: Dict[str, Any] = {"channel": channel}
        if context:
            body["context"] = context
        return self._request("POST", self._url(f"/{chatflow_id}/sessions"), data=body)

    def list_sessions(
        self,
        chatflow_id: str,
        page: int = 0,
        size: int = 20,
    ) -> Dict[str, Any]:
        """List sessions for a chatflow."""
        return self._request(
            "GET",
            self._url(f"/{chatflow_id}/sessions"),
            params={"page": page, "size": size},
        )

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get a session by id (cross-chatflow lookup)."""
        return self._request("GET", self._url(f"/sessions/{session_id}"))

    def stats(self, chatflow_id: str) -> Dict[str, Any]:
        """Aggregate session statistics for a chatflow."""
        return self._request("GET", self._url(f"/{chatflow_id}/stats"))

    # ---- builder ------------------------------------------------------

    def field_types(self) -> List[Dict[str, Any]]:
        """List supported field types."""
        return self._request("GET", self._url("/builder/field-types"))

    def action_types(self) -> List[Dict[str, Any]]:
        """List supported action types."""
        return self._request("GET", self._url("/builder/action-types"))

    def press_strategies(self) -> List[Dict[str, Any]]:
        """List supported press (re-engagement) strategies."""
        return self._request("GET", self._url("/builder/press-strategies"))

    def builder_templates(self) -> List[Dict[str, Any]]:
        """List builder templates."""
        return self._request("GET", self._url("/builder/templates"))

    def from_template(
        self,
        template_id: str,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a chatflow from a builder template."""
        return self._request(
            "POST",
            self._url(f"/builder/from-template/{template_id}"),
            data=overrides or {},
        )

    def preview(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Preview a draft definition without persisting."""
        return self._request("POST", self._url("/builder/preview"), data=draft)

    def test(self, chatflow_id: str, input: Dict[str, Any]) -> Dict[str, Any]:
        """Test a chatflow with a synthetic input payload."""
        return self._request("POST", self._url(f"/builder/{chatflow_id}/test"), data=input)

    def export(self, chatflow_id: str) -> Dict[str, Any]:
        """Export a chatflow as JSON."""
        return self._request("GET", self._url(f"/builder/{chatflow_id}/export"))

    def import_(self, definition: Dict[str, Any]) -> Dict[str, Any]:
        """Import a chatflow JSON definition."""
        return self._request("POST", self._url("/builder/import"), data=definition)

    def preview_voice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Preview voice playback for a draft chatflow."""
        return self._request("POST", self._url("/builder/preview-voice"), data=payload)

    # ---- versions -----------------------------------------------------

    def list_versions(self, chatflow_id: str) -> List[Dict[str, Any]]:
        """List versions of a chatflow."""
        return self._request("GET", self._url(f"/{chatflow_id}/versions"))

    def get_version(self, chatflow_id: str, version: str) -> Dict[str, Any]:
        """Get a specific version of a chatflow."""
        return self._request("GET", self._url(f"/{chatflow_id}/versions/{version}"))

    def create_version(
        self,
        chatflow_id: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Snapshot the current chatflow as a new version."""
        body = {"notes": notes} if notes else {}
        return self._request("POST", self._url(f"/{chatflow_id}/versions"), data=body)

    def promote_version(self, chatflow_id: str, version: str) -> Dict[str, Any]:
        """Promote a version to the published slot."""
        return self._request(
            "POST",
            self._url(f"/{chatflow_id}/versions/{version}/promote"),
        )

    def archive_version(self, chatflow_id: str, version: str) -> Dict[str, Any]:
        """Archive a version."""
        return self._request(
            "POST",
            self._url(f"/{chatflow_id}/versions/{version}/archive"),
        )

    # ---- publishing ---------------------------------------------------

    def publish(self, chatflow_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Publish a chatflow."""
        return self._request("POST", self._url(f"/{chatflow_id}/publish"), data=payload or {})

    def get_published(self, chatflow_id: str) -> Dict[str, Any]:
        """Get published metadata for a chatflow."""
        return self._request("GET", self._url(f"/{chatflow_id}/published"))
