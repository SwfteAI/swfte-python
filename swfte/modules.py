"""
Modules V2 resource client — bundle agents, workflows, datasets and tools as
reusable, versioned modules. See https://www.swfte.com/marketplace.
"""

from typing import Any, Dict, List, Optional

from ._base import V2Resource


class Modules(V2Resource):
    """Client for ``/v2/modules``."""

    _path_prefix = "/v2/modules"

    # ---- CRUD ---------------------------------------------------------

    def list(self, page: int = 0, size: int = 20, **filters: Any) -> Dict[str, Any]:
        """List modules in the workspace."""
        params: Dict[str, Any] = {"page": page, "size": size, **filters}
        return self._request("GET", self._url(""), params=params)

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a module."""
        payload: Dict[str, Any] = {"name": name, **kwargs}
        if description is not None:
            payload["description"] = description
        return self._request("POST", self._url(""), data=payload)

    def get(self, module_id: str) -> Dict[str, Any]:
        """Get a module by id."""
        return self._request("GET", self._url(f"/{module_id}"))

    def update(self, module_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a module."""
        return self._request("PUT", self._url(f"/{module_id}"), data=updates)

    def delete(self, module_id: str) -> None:
        """Delete a module."""
        self._request("DELETE", self._url(f"/{module_id}"))

    # ---- resources ----------------------------------------------------

    def add_resource(self, module_id: str, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Attach a resource (agent, workflow, tool, dataset) to the module."""
        return self._request("POST", self._url(f"/{module_id}/resources"), data=resource)

    def remove_resource(self, module_id: str, resource_id: str) -> None:
        """Detach a resource from the module."""
        self._request("DELETE", self._url(f"/{module_id}/resources/{resource_id}"))

    # ---- build & versions --------------------------------------------

    def build(self, module_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build (compile) a module so it can be installed elsewhere."""
        return self._request("POST", self._url(f"/{module_id}/build"), data=options or {})

    def build_progress(self, module_id: str) -> Any:
        """Open the SSE stream for build progress (returns the underlying ``Response``)."""
        url = self._url(f"/{module_id}/build/progress")
        return self._request("GET", url, stream=True)

    def list_versions(self, module_id: str) -> List[Dict[str, Any]]:
        """List versions of a module."""
        return self._request("GET", self._url(f"/{module_id}/versions"))

    def get_version(self, module_id: str, version: str) -> Dict[str, Any]:
        """Get a specific module version."""
        return self._request("GET", self._url(f"/{module_id}/versions/{version}"))

    def get_qa(self, module_id: str, version: str) -> Dict[str, Any]:
        """Get the QA bank attached to a module version."""
        return self._request("GET", self._url(f"/{module_id}/versions/{version}/qa"))

    def impact(self, module_id: str) -> Dict[str, Any]:
        """Return the impact report for a module."""
        return self._request("GET", self._url(f"/{module_id}/impact"))
