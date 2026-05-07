"""
Voice Calls V2 resource client — list, fetch, transcript, recording, audit.
See https://www.swfte.com/products/voice for product context.
"""

from typing import Any, Dict, List, Optional

from ._base import V2Resource


class VoiceCalls(V2Resource):
    """Client for ``/v2/voice/calls`` and the chatflow-scoped call list."""

    _path_prefix = "/v2/voice/calls"

    def list(
        self,
        page: int = 0,
        size: int = 20,
        status: Optional[str] = None,
        **filters: Any,
    ) -> Dict[str, Any]:
        """List voice calls."""
        params: Dict[str, Any] = {"page": page, "size": size, **filters}
        if status is not None:
            params["status"] = status
        return self._request("GET", self._url(""), params=params)

    def in_progress(self) -> List[Dict[str, Any]]:
        """List currently in-progress calls."""
        return self._request("GET", self._url("/in-progress"))

    def get(self, call_sid: str) -> Dict[str, Any]:
        """Get a call by Twilio (or WebRTC) SID."""
        return self._request("GET", self._url(f"/{call_sid}"))

    def transcript(self, call_sid: str) -> Dict[str, Any]:
        """Get the transcript for a call."""
        return self._request("GET", self._url(f"/{call_sid}/transcript"))

    def recording(self, call_sid: str) -> Dict[str, Any]:
        """Return recording metadata (URL, duration, format) for a call."""
        return self._request("GET", self._url(f"/{call_sid}/recording"))

    def audit(self, call_sid: str) -> Dict[str, Any]:
        """Return the audit trail for a call."""
        return self._request("GET", self._url(f"/{call_sid}/audit"))

    def calls_for_chatflow(
        self,
        chatflow_id: str,
        page: int = 0,
        size: int = 20,
    ) -> Dict[str, Any]:
        """List calls placed against a specific chatflow."""
        return self._request(
            "GET",
            self._abs(f"/v2/chatflows/{chatflow_id}/calls"),
            params={"page": page, "size": size},
        )
