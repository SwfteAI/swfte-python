"""
Chat completions API.
"""

import json
from typing import List, Dict, Any, Optional, Union, Iterator
import requests
from .models import ChatCompletion, ChatCompletionChunk, Message
from .exceptions import APIError, RateLimitError, AuthenticationError


class Completions:
    """Chat completions resource."""
    
    def __init__(self, client):
        self.client = client
    
    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,
        top_p: float = 1.0,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        stop: Optional[Union[str, List[str]]] = None,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        user: Optional[str] = None,
        **kwargs
    ) -> Union[ChatCompletion, Iterator[ChatCompletionChunk]]:
        """
        Create a chat completion.
        
        Args:
            model: Model ID to use (e.g., "openai:gpt-4", "anthropic:claude-3-opus", "deployed:my-model")
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            stop: Stop sequences
            presence_penalty: Presence penalty (-2 to 2)
            frequency_penalty: Frequency penalty (-2 to 2)
            user: User identifier for tracking
        
        Returns:
            ChatCompletion object or iterator of ChatCompletionChunk if streaming
        
        Example:
            response = client.chat.completions.create(
                model="openai:gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"}
                ]
            )
            print(response.choices[0].message.content)
        """
        url = f"{self.client.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if stop:
            payload["stop"] = stop
        if user:
            payload["user"] = user
        
        # Add any additional kwargs
        payload.update(kwargs)
        
        headers = self.client._get_headers()
        
        if stream:
            return self._stream_response(url, payload, headers)
        else:
            return self._send_request(url, payload, headers)
    
    def _send_request(self, url: str, payload: dict, headers: dict) -> ChatCompletion:
        """Send a non-streaming request."""
        for attempt in range(self.client.max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.client.timeout,
                )
                
                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status_code >= 400:
                    raise APIError(f"API error: {response.status_code} - {response.text}")
                
                data = response.json()
                return ChatCompletion.from_dict(data)
                
            except requests.exceptions.Timeout:
                if attempt == self.client.max_retries - 1:
                    raise APIError("Request timed out")
            except requests.exceptions.RequestException as e:
                if attempt == self.client.max_retries - 1:
                    raise APIError(f"Request failed: {str(e)}")
    
    def _stream_response(self, url: str, payload: dict, headers: dict) -> Iterator[ChatCompletionChunk]:
        """Stream the response."""
        # Use the dedicated streaming endpoint
        stream_url = url.replace("/chat/completions", "/chat/completions/stream")

        response = requests.post(
            stream_url,
            json=payload,
            headers=headers,
            timeout=self.client.timeout,
            stream=True,
        )
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        elif response.status_code >= 400:
            raise APIError(f"API error: {response.status_code}")
        
        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                # Handle both "data:" and "data: " formats
                if line.startswith("data:"):
                    data = line[5:].lstrip()  # Remove "data:" and any leading whitespace
                    if data == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(data)
                        yield ChatCompletionChunk.from_dict(chunk_data)
                    except json.JSONDecodeError:
                        continue


class Chat:
    """Chat API resource."""
    
    def __init__(self, client):
        self.client = client
        self.completions = Completions(client)

