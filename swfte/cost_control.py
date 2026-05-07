"""
Cost Control V2 resource client — routing rules, usage caps, usage stats.
See https://www.swfte.com/products/cost-control.
"""

from typing import Any, Dict, List, Optional

from ._base import V2Resource


class CostControl(V2Resource):
    """Client for ``/v2/cost-control``."""

    _path_prefix = "/v2/cost-control"

    # ---- routing rules ------------------------------------------------

    def list_routing_rules(self) -> List[Dict[str, Any]]:
        """List configured routing rules."""
        return self._request("GET", self._url("/routing-rules"))

    def create_routing_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new routing rule."""
        return self._request("POST", self._url("/routing-rules"), data=rule)

    def get_routing_rule(self, rule_id: str) -> Dict[str, Any]:
        """Fetch a single routing rule."""
        return self._request("GET", self._url(f"/routing-rules/{rule_id}"))

    def update_routing_rule(self, rule_id: str, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Replace a routing rule."""
        return self._request("PUT", self._url(f"/routing-rules/{rule_id}"), data=rule)

    def delete_routing_rule(self, rule_id: str) -> None:
        """Delete a routing rule."""
        self._request("DELETE", self._url(f"/routing-rules/{rule_id}"))

    def toggle_routing_rule(self, rule_id: str, enabled: Optional[bool] = None) -> Dict[str, Any]:
        """Toggle (or explicitly set) a routing rule's enabled flag."""
        body = {} if enabled is None else {"enabled": enabled}
        return self._request("PATCH", self._url(f"/routing-rules/{rule_id}/toggle"), data=body)

    # ---- usage caps ---------------------------------------------------

    def list_usage_caps(self) -> List[Dict[str, Any]]:
        """List usage caps."""
        return self._request("GET", self._url("/usage-caps"))

    def set_workspace_cap(self, cap: Dict[str, Any]) -> Dict[str, Any]:
        """Set the workspace-level usage cap."""
        return self._request("PUT", self._url("/usage-caps/workspace"), data=cap)

    def set_model_cap(self, model_id: str, cap: Dict[str, Any]) -> Dict[str, Any]:
        """Set a per-model usage cap."""
        return self._request("PUT", self._url(f"/usage-caps/model/{model_id}"), data=cap)

    def delete_cap(self, cap_id: str) -> None:
        """Delete a usage cap."""
        self._request("DELETE", self._url(f"/usage-caps/{cap_id}"))

    # ---- stats & scaling ---------------------------------------------

    def usage_stats(self, **filters: Any) -> Dict[str, Any]:
        """Return aggregated usage statistics."""
        return self._request("GET", self._url("/usage-stats"), params=filters or None)

    def scaling(self, deployment_id: str) -> Dict[str, Any]:
        """Get the scaling configuration for a self-hosted deployment."""
        return self._request("GET", self._url(f"/scaling/{deployment_id}"))
