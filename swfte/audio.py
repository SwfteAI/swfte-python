"""
Audio API (transcription and text-to-speech).
"""

from typing import Optional, Literal
import requests
from .exceptions import APIError, AuthenticationError


class Transcriptions:
    """Audio transcription resource."""
    
    def __init__(self, client):
        self.client = client
    
    def create(
        self,
        model: str,
        file: bytes,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: Literal["json", "text", "srt", "vtt"] = "json",
        temperature: float = 0.0,
        **kwargs
    ) -> dict:
        """
        Transcribe audio to text.
        
        Args:
            model: Model ID (e.g., "openai:whisper-1", "deployed:whisper-large")
            file: Audio file bytes
            language: Language code (ISO-639-1)
            prompt: Optional prompt to guide transcription
            response_format: Output format
            temperature: Sampling temperature
        
        Returns:
            Transcription result
        
        Example:
            with open("audio.mp3", "rb") as f:
                result = client.audio.transcriptions.create(
                    model="openai:whisper-1",
                    file=f.read()
                )
            print(result["text"])
        """
        url = f"{self.client.base_url}/audio/transcriptions"
        
        # Include filename and content type for proper multipart handling
        files = {"file": ("audio.mp3", file, "audio/mpeg")}
        data = {
            "model": model,
            "response_format": response_format,
            "temperature": str(temperature),
        }
        
        if language:
            data["language"] = language
        if prompt:
            data["prompt"] = prompt
        
        data.update(kwargs)
        
        headers = self.client._get_headers()
        del headers["Content-Type"]
        
        response = requests.post(
            url,
            files=files,
            data=data,
            headers=headers,
            timeout=self.client.timeout * 2,
        )
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code >= 400:
            raise APIError(f"API error: {response.status_code} - {response.text}")
        
        if response_format == "json":
            return response.json()
        return {"text": response.text}


class Speech:
    """Text-to-speech resource."""
    
    def __init__(self, client):
        self.client = client
    
    def create(
        self,
        model: str,
        input: str,
        voice: str = "alloy",
        response_format: Literal["mp3", "opus", "aac", "flac", "wav"] = "mp3",
        speed: float = 1.0,
        **kwargs
    ) -> bytes:
        """
        Generate speech from text.
        
        Args:
            model: Model ID (e.g., "openai:tts-1", "deployed:xtts")
            input: Text to convert to speech
            voice: Voice to use
            response_format: Audio format
            speed: Speech speed (0.25 to 4.0)
        
        Returns:
            Audio file bytes
        
        Example:
            audio = client.audio.speech.create(
                model="openai:tts-1",
                input="Hello world!",
                voice="nova"
            )
            with open("output.mp3", "wb") as f:
                f.write(audio)
        """
        url = f"{self.client.base_url}/audio/speech"
        
        payload = {
            "model": model,
            "input": input,
            "voice": voice,
            "response_format": response_format,
            "speed": speed,
        }
        payload.update(kwargs)
        
        headers = self.client._get_headers()
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=self.client.timeout * 2,
        )
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code >= 400:
            raise APIError(f"API error: {response.status_code} - {response.text}")
        
        return response.content


class Audio:
    """Audio API resource."""
    
    def __init__(self, client):
        self.client = client
        self.transcriptions = Transcriptions(client)
        self.speech = Speech(client)

