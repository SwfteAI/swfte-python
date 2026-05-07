"""
Files V2 resource client.

Upload, list, fetch, and clean up workspace files.
"""

from typing import Any, BinaryIO, Dict, List, Optional, Tuple, Union

from ._base import V2Resource

UploadFile = Union[BinaryIO, bytes, Tuple[str, BinaryIO], Tuple[str, BinaryIO, str]]


class Files(V2Resource):
    """Client for ``/api/v2/files``."""

    _path_prefix = "/api/v2/files"

    def config(self) -> Dict[str, Any]:
        """Return upload configuration (size limits, allowed mime types, etc.)."""
        return self._request("GET", self._url("/config"))

    def upload(
        self,
        file: UploadFile,
        usage: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Upload a single file as multipart/form-data."""
        files = {"file": file}
        data: Dict[str, Any] = {}
        if usage is not None:
            data["usage"] = usage
        if metadata is not None:
            import json as _json

            data["metadata"] = _json.dumps(metadata)
        return self._request("POST", self._url("/upload"), data=data, files=files)

    def upload_batch(
        self,
        files_to_upload: List[UploadFile],
        usage: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a batch of files."""
        files = [("files", f) for f in files_to_upload]
        data: Dict[str, Any] = {}
        if usage is not None:
            data["usage"] = usage
        return self._request("POST", self._url("/upload-batch"), data=data, files=files)

    def list(self, page: int = 0, size: int = 20, **filters: Any) -> Dict[str, Any]:
        """List files in the workspace."""
        params: Dict[str, Any] = {"page": page, "size": size, **filters}
        return self._request("GET", self._url(""), params=params)

    def get(self, file_id: str) -> Dict[str, Any]:
        """Get file metadata."""
        return self._request("GET", self._url(f"/{file_id}"))

    def download(self, file_id: str) -> bytes:
        """Download raw file bytes."""
        result = self._request("GET", self._url(f"/{file_id}/download"))
        return result if isinstance(result, (bytes, bytearray)) else result

    def preview(self, file_id: str) -> bytes:
        """Return a preview-formatted version of the file."""
        return self._request("GET", self._url(f"/{file_id}/preview"))

    def delete(self, file_id: str) -> None:
        """Delete a file."""
        self._request("DELETE", self._url(f"/{file_id}"))

    def update_usage(self, file_id: str, usage: str) -> Dict[str, Any]:
        """Update the recorded usage of a file (e.g. ``DATASET``, ``AVATAR``)."""
        return self._request("PUT", self._url(f"/{file_id}/usage"), data={"usage": usage})

    def cleanup(self) -> Dict[str, Any]:
        """Trigger cleanup of orphaned files."""
        return self._request("POST", self._url("/cleanup"))
