"""
Internal helpers shared by V2 resource clients.

These helpers keep the per-resource modules small and consistent.
"""

from typing import Any, Dict, Optional

import requests

from . import _http
from ._privacy import credential_safe
from .exceptions import AuthenticationError, RateLimitError


def _service_root(base_url: str) -> str:
    """
    Strip the gateway suffix from the configured base URL so V2 controller
    paths (e.g. ``/v2/agents``) resolve against the agents-service root.
    """
    base = base_url.rstrip("/")
    for suffix in ("/v2/gateway", "/v1/gateway", "/gateway"):
        if base.endswith(suffix):
            return base[: -len(suffix)]
    return base


def _raise_for_status(response: Any, method: str, url: str) -> None:
    """Map 401/403 -> AuthenticationError and 429 -> RateLimitError; any other
    HTTP error still raises ``requests.HTTPError`` as before."""
    if response.status_code in (401, 403):
        raise AuthenticationError(f"API error: {response.status_code} {method} {url}")
    if response.status_code == 429:
        raise RateLimitError(f"Rate limit exceeded: {method} {url}")
    response.raise_for_status()


@credential_safe
class V2Resource:
    """
    Base class for V2 resource clients.

    Subclasses set ``_path_prefix`` (e.g. ``"/v2/chatflows"``) and call
    :py:meth:`_request` for any HTTP verb. The class deliberately avoids
    smart retries, async, or pluggable transports — keep it simple, keep it
    Pythonic, mirror the existing V1 modules.
    """

    _path_prefix: str = ""

    def __init__(self, client: Any) -> None:
        self._client = client

    # ---- URL helpers --------------------------------------------------

    def _root(self) -> str:
        """Return the agents-service root URL."""
        return self._client.api_base_url

    def _url(self, path: str = "") -> str:
        """Build a full URL under this resource's path prefix."""
        suffix = path if path.startswith("/") or not path else f"/{path}"
        return f"{self._root()}{self._path_prefix}{suffix}"

    def _abs(self, path: str) -> str:
        """Build a URL relative to the service root (used for cross-prefix calls)."""
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self._root()}{path}"

    # ---- HTTP ---------------------------------------------------------

    def _request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> Any:
        """Perform an HTTP request and return parsed JSON (or raw response if streaming)."""
        headers = self._client._get_headers()
        if files is not None:
            # let requests build the multipart boundary
            headers.pop("Content-Type", None)

        response = _http.request(
            method=method,
            url=url,
            headers=headers,
            json=data if files is None else None,
            data=None if files is None else data,
            params=params,
            files=files,
            timeout=self._client.timeout,
            stream=stream,
        )
        _raise_for_status(response, method, url)

        if stream:
            return response

        if not response.content:
            return {}

        ctype = (response.headers.get("Content-Type") or "").lower()
        # Try JSON first when content-type says so, or when the header is
        # missing (a lot of test doubles and proxies omit it). Fall back to
        # raw bytes for binary downloads (csv export, file download, etc.).
        if "json" in ctype or not ctype:
            try:
                return response.json()
            except ValueError:
                return response.content
        return response.content
