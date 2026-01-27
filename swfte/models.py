"""
Data models for the Swfte SDK.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import requests
from .exceptions import APIError, AuthenticationError


@dataclass
class Message:
    """A chat message."""
    role: str
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            role=data.get("role", ""),
            content=data.get("content", ""),
            name=data.get("name"),
            function_call=data.get("function_call"),
            tool_calls=data.get("tool_calls"),
        )


@dataclass
class Choice:
    """A completion choice."""
    index: int
    message: Message
    finish_reason: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "Choice":
        return cls(
            index=data.get("index", 0),
            message=Message.from_dict(data.get("message", {})),
            finish_reason=data.get("finish_reason"),
        )


@dataclass
class DeltaMessage:
    """A delta message in streaming response."""
    role: Optional[str] = None
    content: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "DeltaMessage":
        return cls(
            role=data.get("role"),
            content=data.get("content"),
            function_call=data.get("function_call"),
            tool_calls=data.get("tool_calls"),
        )


@dataclass
class StreamChoice:
    """A streaming completion choice."""
    index: int
    delta: DeltaMessage
    finish_reason: Optional[str] = None
    message: Optional[Message] = None  # For wrapped non-streaming responses

    @classmethod
    def from_dict(cls, data: dict) -> "StreamChoice":
        # Handle both delta (streaming) and message (wrapped) formats
        delta = DeltaMessage.from_dict(data.get("delta", {})) if "delta" in data else DeltaMessage()
        message = Message.from_dict(data.get("message", {})) if "message" in data else None
        return cls(
            index=data.get("index", 0),
            delta=delta,
            finish_reason=data.get("finish_reason") or data.get("finishReason"),
            message=message,
        )


@dataclass
class Usage:
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    @classmethod
    def from_dict(cls, data: dict) -> "Usage":
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
        )


@dataclass
class ChatCompletion:
    """A chat completion response."""
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "ChatCompletion":
        return cls(
            id=data.get("id", ""),
            object=data.get("object", "chat.completion"),
            created=data.get("created", 0),
            model=data.get("model", ""),
            choices=[Choice.from_dict(c) for c in data.get("choices", [])],
            usage=Usage.from_dict(data["usage"]) if data.get("usage") else None,
        )


@dataclass
class ChatCompletionChunk:
    """A streaming chat completion chunk."""
    id: str
    object: str
    created: int
    model: str
    choices: List[StreamChoice]
    
    @classmethod
    def from_dict(cls, data: dict) -> "ChatCompletionChunk":
        return cls(
            id=data.get("id", ""),
            object=data.get("object", "chat.completion.chunk"),
            created=data.get("created", 0),
            model=data.get("model", ""),
            choices=[StreamChoice.from_dict(c) for c in data.get("choices", [])],
        )


@dataclass
class ImageData:
    """Generated image data."""
    url: Optional[str] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "ImageData":
        return cls(
            url=data.get("url"),
            b64_json=data.get("b64_json"),
            revised_prompt=data.get("revised_prompt"),
        )


@dataclass
class ImageGenerationResponse:
    """Image generation response."""
    created: int
    data: List[ImageData]
    
    @classmethod
    def from_dict(cls, data: dict) -> "ImageGenerationResponse":
        return cls(
            created=data.get("created", 0),
            data=[ImageData.from_dict(d) for d in data.get("data", [])],
        )


@dataclass
class Embedding:
    """An embedding vector."""
    object: str
    index: int
    embedding: List[float]
    
    @classmethod
    def from_dict(cls, data: dict) -> "Embedding":
        return cls(
            object=data.get("object", "embedding"),
            index=data.get("index", 0),
            embedding=data.get("embedding", []),
        )


@dataclass
class EmbeddingUsage:
    """Embedding usage statistics."""
    prompt_tokens: int
    total_tokens: int
    
    @classmethod
    def from_dict(cls, data: dict) -> "EmbeddingUsage":
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
        )


@dataclass
class EmbeddingResponse:
    """Embedding response."""
    object: str
    model: str
    data: List[Embedding]
    usage: EmbeddingUsage
    
    @classmethod
    def from_dict(cls, data: dict) -> "EmbeddingResponse":
        return cls(
            object=data.get("object", "list"),
            model=data.get("model", ""),
            data=[Embedding.from_dict(d) for d in data.get("data", [])],
            usage=EmbeddingUsage.from_dict(data.get("usage", {})),
        )


@dataclass
class Model:
    """A model."""
    id: str
    object: str
    created: int
    owned_by: str
    
    @classmethod
    def from_dict(cls, data: dict) -> "Model":
        return cls(
            id=data.get("id", ""),
            object=data.get("object", "model"),
            created=data.get("created", 0),
            owned_by=data.get("owned_by", ""),
        )


class Models:
    """Models listing resource."""
    
    def __init__(self, client):
        self.client = client
    
    def list(self) -> List[Model]:
        """
        List available models.
        
        Returns:
            List of Model objects
        
        Example:
            models = client.models.list()
            for model in models:
                print(f"{model.id} - {model.owned_by}")
        """
        url = f"{self.client.base_url}/models"
        headers = self.client._get_headers()
        
        response = requests.get(url, headers=headers, timeout=self.client.timeout)
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code >= 400:
            raise APIError(f"API error: {response.status_code} - {response.text}")
        
        data = response.json()
        return [Model.from_dict(m) for m in data.get("models", data.get("data", []))]
    
    def retrieve(self, model_id: str) -> Model:
        """
        Retrieve a specific model.
        
        Args:
            model_id: The model ID
        
        Returns:
            Model object
        """
        url = f"{self.client.base_url}/models/{model_id}"
        headers = self.client._get_headers()
        
        response = requests.get(url, headers=headers, timeout=self.client.timeout)
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code >= 400:
            raise APIError(f"API error: {response.status_code} - {response.text}")
        
        return Model.from_dict(response.json())

