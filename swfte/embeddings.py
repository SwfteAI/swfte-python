"""
Embeddings API.
"""

from typing import Union, List
import requests
from .models import EmbeddingResponse
from .exceptions import APIError, AuthenticationError


class Embeddings:
    """Embeddings resource."""
    
    def __init__(self, client):
        self.client = client
    
    def create(
        self,
        model: str,
        input: Union[str, List[str]],
        encoding_format: str = "float",
        **kwargs
    ) -> EmbeddingResponse:
        """
        Create embeddings for the input text(s).
        
        Args:
            model: Model ID (e.g., "openai:text-embedding-3-large", "deployed:bge-large")
            input: Text or list of texts to embed
            encoding_format: Output format ("float" or "base64")
        
        Returns:
            EmbeddingResponse with embedding vectors
        
        Example:
            response = client.embeddings.create(
                model="openai:text-embedding-3-small",
                input="The quick brown fox jumps over the lazy dog"
            )
            print(len(response.data[0].embedding))  # Dimension of embedding
        """
        url = f"{self.client.base_url}/embeddings"
        
        payload = {
            "model": model,
            "input": input,
            "encoding_format": encoding_format,
        }
        payload.update(kwargs)
        
        headers = self.client._get_headers()
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=self.client.timeout,
        )
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code >= 400:
            raise APIError(f"API error: {response.status_code} - {response.text}")
        
        return EmbeddingResponse.from_dict(response.json())

