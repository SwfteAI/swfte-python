"""
Marketplace V2 resource client — browse, install, and uninstall publications.
"""

from typing import Any, Dict, List, Optional

from ._base import V2Resource


class Marketplace(V2Resource):
    """Client for ``/v2/marketplace``."""

    _path_prefix = "/v2/marketplace"

    def browse(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 0,
        size: int = 20,
        **filters: Any,
    ) -> Dict[str, Any]:
        """Browse marketplace publications."""
        params: Dict[str, Any] = {"page": page, "size": size, **filters}
        if query is not None:
            params["q"] = query
        if category is not None:
            params["category"] = category
        return self._request("GET", self._url(""), params=params)

    def get(self, publication_id: str) -> Dict[str, Any]:
        """Fetch a publication's full detail page."""
        return self._request("GET", self._url(f"/{publication_id}"))

    def install(
        self,
        publication_id: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Install a publication into the active workspace."""
        return self._request(
            "POST",
            self._url(f"/{publication_id}/install"),
            data=options or {},
        )

    def list_installations(self, page: int = 0, size: int = 20) -> Dict[str, Any]:
        """List installations in the workspace."""
        return self._request(
            "GET",
            self._url("/installations"),
            params={"page": page, "size": size},
        )

    def uninstall(self, installation_id: str) -> None:
        """Uninstall a previously installed publication."""
        self._request("DELETE", self._url(f"/installations/{installation_id}"))
