"""
Documents V2 resource client.

Documents are units of content stored inside a dataset. The server processes
each document into segments that are retrievable via the RAG API.
"""

from typing import Any, Dict, List, Optional

from ._base import V2Resource


class Documents(V2Resource):
    """Client for ``/api/v2/datasets/{datasetId}/documents``."""

    # _path_prefix is unused — paths always include the dataset id

    def _docs(self, dataset_id: str, suffix: str = "") -> str:
        return self._abs(f"/api/v2/datasets/{dataset_id}/documents{suffix}")

    def create(self, dataset_id: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create one or more documents in a dataset."""
        return self._request("POST", self._docs(dataset_id), data={"documents": documents})

    def list(
        self,
        dataset_id: str,
        page: int = 0,
        size: int = 20,
        **filters: Any,
    ) -> Dict[str, Any]:
        """List documents in a dataset."""
        params: Dict[str, Any] = {"page": page, "size": size, **filters}
        return self._request("GET", self._docs(dataset_id), params=params)

    def get(self, dataset_id: str, document_id: str) -> Dict[str, Any]:
        """Fetch a document."""
        return self._request("GET", self._docs(dataset_id, f"/{document_id}"))

    def update(
        self,
        dataset_id: str,
        document_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Replace a document."""
        return self._request("PUT", self._docs(dataset_id, f"/{document_id}"), data=updates)

    def delete(self, dataset_id: str, document_id: str) -> None:
        """Delete a document."""
        self._request("DELETE", self._docs(dataset_id, f"/{document_id}"))

    def segments(self, dataset_id: str, document_id: str) -> List[Dict[str, Any]]:
        """Return segments produced by document processing."""
        return self._request("GET", self._docs(dataset_id, f"/{document_id}/segments"))

    def retry(self, dataset_id: str, document_id: str) -> Dict[str, Any]:
        """Retry processing for a failed document."""
        return self._request("POST", self._docs(dataset_id, f"/{document_id}/retry"))

    def processing_status(self, dataset_id: str) -> Dict[str, Any]:
        """Aggregate processing status for the dataset."""
        return self._request("GET", self._docs(dataset_id, "/processing-status"))

    def pause(self, dataset_id: str, document_id: str) -> Dict[str, Any]:
        """Pause processing of a document."""
        return self._request("POST", self._docs(dataset_id, f"/{document_id}/pause"))

    def resume(self, dataset_id: str, document_id: str) -> Dict[str, Any]:
        """Resume processing of a document."""
        return self._request("POST", self._docs(dataset_id, f"/{document_id}/resume"))

    def batch_update(self, dataset_id: str, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply a batch of updates to multiple documents."""
        return self._request("PATCH", self._docs(dataset_id, "/batch"), data={"updates": batch})

    def batch_status(self, dataset_id: str, batch_id: str) -> Dict[str, Any]:
        """Check status of a batch update."""
        return self._request("GET", self._docs(dataset_id, f"/batch/{batch_id}/status"))
