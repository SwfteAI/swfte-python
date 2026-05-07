"""
Datasets V2 resource client.

Datasets group documents for retrieval-augmented generation. See
https://www.swfte.com/products/rag for product context.
"""

from typing import Any, Dict, Optional

from ._base import V2Resource


class Datasets(V2Resource):
    """Client for ``/api/v2/datasets``."""

    _path_prefix = "/api/v2/datasets"

    def list(self, page: int = 0, size: int = 20, **filters: Any) -> Dict[str, Any]:
        """List datasets in the workspace."""
        params: Dict[str, Any] = {"page": page, "size": size, **filters}
        return self._request("GET", self._url(""), params=params)

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        embedding_model: Optional[str] = None,
        retrieval_strategy: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a dataset."""
        payload: Dict[str, Any] = {"name": name, **kwargs}
        if description is not None:
            payload["description"] = description
        if embedding_model is not None:
            payload["embeddingModel"] = embedding_model
        if retrieval_strategy is not None:
            payload["retrievalStrategy"] = retrieval_strategy
        return self._request("POST", self._url(""), data=payload)

    def get(self, dataset_id: str) -> Dict[str, Any]:
        """Get a dataset by id."""
        return self._request("GET", self._url(f"/{dataset_id}"))

    def update(self, dataset_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a dataset."""
        return self._request("PUT", self._url(f"/{dataset_id}"), data=updates)

    def delete(self, dataset_id: str) -> None:
        """Delete a dataset."""
        self._request("DELETE", self._url(f"/{dataset_id}"))

    def use_check(self, dataset_id: str) -> Dict[str, Any]:
        """Check what is using this dataset before deletion."""
        return self._request("GET", self._url(f"/{dataset_id}/use-check"))

    def set_api_access(self, dataset_id: str, status: str) -> Dict[str, Any]:
        """Toggle API access for the dataset (status is typically ``enable`` or ``disable``)."""
        return self._request("POST", self._url(f"/{dataset_id}/api-access/{status}"))
