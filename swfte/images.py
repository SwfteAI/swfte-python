"""
Image generation API.
"""

from typing import Optional, List, Literal
import requests
from .models import ImageGenerationResponse
from .exceptions import APIError, AuthenticationError


class Images:
    """Image generation resource."""
    
    def __init__(self, client):
        self.client = client
    
    def generate(
        self,
        model: str,
        prompt: str,
        n: int = 1,
        size: str = "1024x1024",
        quality: Literal["standard", "hd"] = "standard",
        style: Literal["vivid", "natural"] = "vivid",
        response_format: Literal["url", "b64_json"] = "url",
        negative_prompt: Optional[str] = None,
        **kwargs
    ) -> ImageGenerationResponse:
        """
        Generate images from a text prompt.
        
        Args:
            model: Model ID (e.g., "openai:dall-e-3", "deployed:sdxl")
            prompt: Text description of the desired image(s)
            n: Number of images to generate (1-10)
            size: Image size ("256x256", "512x512", "1024x1024", "1024x1792", "1792x1024")
            quality: Image quality ("standard" or "hd")
            style: Image style ("vivid" or "natural")
            response_format: Response format ("url" or "b64_json")
            negative_prompt: What to avoid in the image (for some models)
        
        Returns:
            ImageGenerationResponse with generated image URLs or base64 data
        
        Example:
            response = client.images.generate(
                model="openai:dall-e-3",
                prompt="A sunset over mountains in watercolor style",
                size="1024x1024"
            )
            print(response.data[0].url)
        """
        url = f"{self.client.base_url}/images/generations"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "quality": quality,
            "style": style,
            "response_format": response_format,
        }
        
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        
        payload.update(kwargs)
        
        headers = self.client._get_headers()
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=self.client.timeout * 3,  # Image generation takes longer
        )
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code >= 400:
            raise APIError(f"API error: {response.status_code} - {response.text}")
        
        return ImageGenerationResponse.from_dict(response.json())
    
    def edit(
        self,
        model: str,
        image: bytes,
        prompt: str,
        mask: Optional[bytes] = None,
        n: int = 1,
        size: str = "1024x1024",
        **kwargs
    ) -> ImageGenerationResponse:
        """
        Edit an image using a prompt.
        
        Args:
            model: Model ID
            image: Image file bytes to edit
            prompt: Description of the edit
            mask: Optional mask image bytes
            n: Number of images to generate
            size: Output image size
        
        Returns:
            ImageGenerationResponse with edited images
        """
        url = f"{self.client.base_url}/images/edits"
        
        files = {"image": image}
        if mask:
            files["mask"] = mask
        
        data = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
        }
        data.update(kwargs)
        
        headers = self.client._get_headers()
        del headers["Content-Type"]  # Let requests set it for multipart
        
        response = requests.post(
            url,
            files=files,
            data=data,
            headers=headers,
            timeout=self.client.timeout * 3,
        )
        
        if response.status_code >= 400:
            raise APIError(f"API error: {response.status_code} - {response.text}")
        
        return ImageGenerationResponse.from_dict(response.json())

