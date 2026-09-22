"""
Catalog — find proven artifacts across kinds, read their evidence and the
contract for calling them.

Responses are returned as plain dicts with the server's camelCase keys (see the
SOT catalog contract): ``CatalogEntrySummary``, ``CatalogEntryDetail`` and
``CatalogContract``.
"""

from typing import Any, Dict, Iterable, Optional, Union
from urllib.parse import quote

from .exceptions import InvalidRequestError

#: Artifact kinds known to the catalog (wire values).
CATALOG_KINDS = (
    "workflow",
    "agent",
    "chatflow",
    "widget",
    "application",
    "mcp-server",
    "model",
    "module",
    "solution",
)

#: Evidence levels, weakest to strongest, plus the two degraded states.
EVIDENCE_LEVELS = (
    "unmeasured",
    "observed",
    "corroborated",
    "validated",
    "verified",
    "stale",
    "disputed",
)


def _entry_path(kind: str, id: str) -> str:
    if not kind:
        raise InvalidRequestError("kind is required")
    if not id:
        raise InvalidRequestError("id is required")
    return f"/v2/catalog/{quote(kind, safe='')}/{quote(id, safe='')}"


class Catalog:
    """
    Catalog API.

    Example:
        page = client.catalog.search(q="invoice", kinds=["workflow"], min_evidence="corroborated")
        detail = client.catalog.get("workflow", page["items"][0]["id"])
        contract = client.catalog.contract("workflow", page["items"][0]["id"])
        print(contract["invoke"]["method"], contract["invoke"]["path"])
    """

    def __init__(self, client):
        self._client = client

    def search(
        self,
        q: Optional[str] = None,
        kinds: Optional[Union[str, Iterable[str]]] = None,
        scope: Optional[str] = None,
        domain: Optional[str] = None,
        capability: Optional[str] = None,
        industry: Optional[str] = None,
        min_evidence: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """``GET /v2/catalog/search``.

        Args:
            q: Free-text query.
            kinds: Kinds to include (sent comma-separated), e.g. ``["workflow", "agent"]``.
            scope: ``"workspace"``, ``"public"`` or ``"all"``.
            domain / capability / industry: Facet filters.
            min_evidence: Only entries at or above this evidence level.
            limit: Page size (server default 20).
            cursor: ``nextCursor`` from the previous page.

        Returns:
            ``{"items": [...], "nextCursor": str | None, "degraded": [...]}`` —
            ``degraded`` names subsystems that were unavailable; the search still answered.
        """
        if kinds is not None and not isinstance(kinds, str):
            kinds = list(kinds)
        res = self._client._api_request(
            "GET",
            "/v2/catalog/search",
            params={
                "q": q,
                "kinds": kinds,
                "scope": scope,
                "domain": domain,
                "capability": capability,
                "industry": industry,
                "minEvidence": min_evidence,
                "limit": limit,
                "cursor": cursor,
            },
        ) or {}
        return {
            "items": res.get("items") or [],
            "nextCursor": res.get("nextCursor"),
            "degraded": res.get("degraded") or [],
        }

    def get(self, kind: str, id: str) -> Dict[str, Any]:
        """``GET /v2/catalog/{kind}/{id}`` — evidence records, dependencies, reviews."""
        return self._client._api_request("GET", _entry_path(kind, id))

    def contract(self, kind: str, id: str) -> Dict[str, Any]:
        """``GET /v2/catalog/{kind}/{id}/contract`` — invoke method/path, schemas, snippets."""
        return self._client._api_request("GET", f"{_entry_path(kind, id)}/contract")
