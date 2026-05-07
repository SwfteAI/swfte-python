"""
RAG V2 resource client.

Hybrid search, reranking, embedding/reranker model catalogues, retrieval
strategies, BM25 vocabulary management. See https://www.swfte.com/products/rag.
"""

from typing import Any, Dict, List, Optional

from ._base import V2Resource


class Rag(V2Resource):
    """Client for ``/v2/rag``."""

    _path_prefix = "/v2/rag"

    def search(
        self,
        query: str,
        dataset_ids: Optional[List[str]] = None,
        strategy: Optional[str] = None,
        top_k: int = 10,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Run a hybrid retrieval against one or more datasets."""
        payload: Dict[str, Any] = {"query": query, "topK": top_k, **kwargs}
        if dataset_ids is not None:
            payload["datasetIds"] = dataset_ids
        if strategy is not None:
            payload["strategy"] = strategy
        return self._request("POST", self._url("/search"), data=payload)

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        model: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Rerank a candidate list with a cross-encoder."""
        payload: Dict[str, Any] = {"query": query, "documents": documents}
        if model is not None:
            payload["model"] = model
        if top_k is not None:
            payload["topK"] = top_k
        return self._request("POST", self._url("/rerank"), data=payload)

    def embedding_models(self) -> List[Dict[str, Any]]:
        """List available embedding models."""
        return self._request("GET", self._url("/models/embeddings"))

    def reranker_models(self) -> List[Dict[str, Any]]:
        """List available reranker models."""
        return self._request("GET", self._url("/models/rerankers"))

    def strategies(self) -> List[Dict[str, Any]]:
        """List supported retrieval strategies."""
        return self._request("GET", self._url("/strategies"))

    def config(self) -> Dict[str, Any]:
        """Return the workspace's RAG configuration."""
        return self._request("GET", self._url("/config"))

    def build_vocabulary(self, dataset_id: Optional[str] = None) -> Dict[str, Any]:
        """Trigger a (re)build of the BM25 vocabulary for a dataset or workspace."""
        body = {"datasetId": dataset_id} if dataset_id else {}
        return self._request("POST", self._url("/vocabulary/build"), data=body)

    def vocabulary_stats(self, dataset_id: Optional[str] = None) -> Dict[str, Any]:
        """Return vocabulary statistics."""
        params = {"datasetId": dataset_id} if dataset_id else None
        return self._request("GET", self._url("/vocabulary/stats"), params=params)
