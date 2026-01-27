"""
Comprehensive Gateway Integration Tests - Python SDK

This module provides comprehensive integration tests for all supported providers
and modalities through the Swfte unified gateway.

Supports:
- Proprietary providers: OpenAI, Anthropic, Google, Mistral, Cohere, DeepSeek
- Self-hosted: RunPod deployments (LLM, TTS, STT, Image)
- All modalities: Chat, Streaming, Embeddings, Images, TTS, STT

Usage:
    pytest tests/integration/test_gateway_comprehensive.py -v
    pytest tests/integration/test_gateway_comprehensive.py -v -k "openai"
    pytest tests/integration/test_gateway_comprehensive.py -v --provider=anthropic
"""

import pytest
import os
import time
import json
import base64
from typing import Optional, Dict, Any, List, Generator
from dataclasses import dataclass
from pathlib import Path


# ==================== FIXTURES ====================

@dataclass
class ProviderConfig:
    """Configuration for a provider test."""
    name: str
    chat_model: str
    embedding_model: Optional[str] = None
    image_model: Optional[str] = None
    tts_model: Optional[str] = None
    stt_model: Optional[str] = None
    supports_streaming: bool = True
    supports_function_calling: bool = False
    max_tokens_param: str = "max_tokens"  # Some providers use different param names
    skip_reason: Optional[str] = None


# Provider configurations
PROPRIETARY_PROVIDERS = {
    "openai": ProviderConfig(
        name="OpenAI",
        chat_model="gpt-4o-mini",
        embedding_model="text-embedding-3-small",
        image_model="dall-e-3",
        tts_model="tts-1",
        stt_model="whisper-1",
        supports_streaming=True,
        supports_function_calling=True,
    ),
    "anthropic": ProviderConfig(
        name="Anthropic",
        chat_model="claude-3-haiku-20240307",
        supports_streaming=True,
        supports_function_calling=True,
    ),
    "google": ProviderConfig(
        name="Google",
        chat_model="gemini-1.5-flash",
        embedding_model="text-embedding-004",
        supports_streaming=True,
        supports_function_calling=True,
    ),
    "mistral": ProviderConfig(
        name="Mistral",
        chat_model="mistral-small-latest",
        embedding_model="mistral-embed",
        supports_streaming=True,
    ),
    "cohere": ProviderConfig(
        name="Cohere",
        chat_model="command-r",
        embedding_model="embed-english-v3.0",
        supports_streaming=True,
    ),
    "deepseek": ProviderConfig(
        name="DeepSeek",
        chat_model="deepseek-chat",
        supports_streaming=True,
    ),
    "groq": ProviderConfig(
        name="Groq",
        chat_model="llama-3.1-8b-instant",
        supports_streaming=True,
    ),
}

SELF_HOSTED_PROVIDERS = {
    "runpod_qwen": ProviderConfig(
        name="RunPod Qwen 2.5",
        chat_model="deployed:{QWEN_DEPLOYMENT_ID}",
        supports_streaming=True,
    ),
    "runpod_llama": ProviderConfig(
        name="RunPod Llama",
        chat_model="deployed:{LLAMA_DEPLOYMENT_ID}",
        supports_streaming=True,
    ),
    "runpod_sdxl": ProviderConfig(
        name="RunPod SDXL",
        chat_model="",
        image_model="comfy:sdxl",
    ),
    "runpod_flux": ProviderConfig(
        name="RunPod FLUX",
        chat_model="",
        image_model="comfy:flux",
    ),
    "runpod_tts": ProviderConfig(
        name="RunPod XTTS",
        chat_model="",
        tts_model="deployed:{TTS_DEPLOYMENT_ID}",
    ),
    "runpod_stt": ProviderConfig(
        name="RunPod Whisper",
        chat_model="",
        stt_model="deployed:{STT_DEPLOYMENT_ID}",
    ),
}


@pytest.fixture(scope="session")
def swfte_client():
    """Create a SwfteClient for integration tests."""
    from swfte import SwfteClient

    api_key = os.environ.get("SWFTE_API_KEY")
    if not api_key:
        pytest.skip("SWFTE_API_KEY environment variable not set")

    base_url = os.environ.get("SWFTE_BASE_URL", "http://localhost:3388/v2/gateway")
    workspace_id = os.environ.get("SWFTE_WORKSPACE_ID", "test-workspace")

    return SwfteClient(
        api_key=api_key,
        base_url=base_url,
        workspace_id=workspace_id,
        timeout=120,
        max_retries=2,
    )


@pytest.fixture(scope="session")
def test_results_dir():
    """Create and return a directory for test results."""
    results_dir = Path(__file__).parent.parent.parent.parent.parent / "scripts" / "comprehensive-model-tests" / "test-results" / "python"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


@pytest.fixture(scope="session")
def audio_test_file(swfte_client, test_results_dir):
    """Generate an audio file for STT tests using TTS."""
    audio_path = test_results_dir / "test_audio.mp3"

    # If file already exists and is recent, reuse it
    if audio_path.exists() and (time.time() - audio_path.stat().st_mtime) < 3600:
        return audio_path

    try:
        audio_data = swfte_client.audio.speech.create(
            model="tts-1",
            input="Hello, this is a test of speech synthesis for the comprehensive gateway tests.",
            voice="alloy",
        )

        with open(audio_path, "wb") as f:
            f.write(audio_data)

        return audio_path
    except Exception as e:
        pytest.skip(f"Could not generate audio for STT tests: {e}")


@pytest.fixture(scope="session")
def deployment_ids():
    """Get deployment IDs from environment."""
    return {
        "qwen": os.environ.get("QWEN_DEPLOYMENT_ID"),
        "llama": os.environ.get("LLAMA_DEPLOYMENT_ID"),
        "tts": os.environ.get("TTS_DEPLOYMENT_ID"),
        "stt": os.environ.get("STT_DEPLOYMENT_ID"),
        "sdxl": os.environ.get("SDXL_DEPLOYMENT_ID"),
        "flux": os.environ.get("FLUX_DEPLOYMENT_ID"),
    }


# ==================== TEST RESULT TRACKING ====================

@dataclass
class TestResult:
    """Result of a single test."""
    provider: str
    test_name: str
    passed: bool
    latency_ms: float
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ResultCollector:
    """Collects test results for reporting."""

    def __init__(self):
        self.results: List[TestResult] = []

    def add(self, result: TestResult):
        self.results.append(result)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "results": [
                {
                    "provider": r.provider,
                    "test": r.test_name,
                    "passed": r.passed,
                    "latency_ms": r.latency_ms,
                    "error": r.error,
                    "metadata": r.metadata,
                }
                for r in self.results
            ]
        }

    def save(self, path: Path):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


@pytest.fixture(scope="session")
def result_collector():
    """Shared result collector for all tests."""
    return ResultCollector()


@pytest.fixture(scope="session", autouse=True)
def save_results(result_collector, test_results_dir):
    """Save results at the end of the test session."""
    yield
    result_collector.save(test_results_dir / "results.json")


# ==================== PROPRIETARY PROVIDER TESTS ====================

class TestProprietaryProviders:
    """Tests for proprietary AI provider integrations."""

    @pytest.mark.parametrize("provider_key,config", list(PROPRIETARY_PROVIDERS.items()))
    def test_chat_completion(self, swfte_client, result_collector, provider_key, config):
        """Test basic chat completion for each provider."""
        if config.skip_reason:
            pytest.skip(config.skip_reason)

        start_time = time.time()
        error = None

        try:
            response = swfte_client.chat.completions.create(
                model=config.chat_model,
                messages=[
                    {"role": "user", "content": f"Say 'Hello from {config.name}' in exactly 4 words."}
                ],
                max_tokens=30,
                temperature=0.0,
            )

            content = response.choices[0].message.content
            assert content is not None, "No content in response"
            assert len(content) > 0, "Empty content"

            passed = True
            metadata = {
                "model": config.chat_model,
                "content_length": len(content),
                "usage": response.usage._asdict() if hasattr(response.usage, "_asdict") else None,
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider=provider_key,
            test_name="chat_completion",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"{config.name} chat completion failed: {error}")

    @pytest.mark.parametrize("provider_key,config", [
        (k, v) for k, v in PROPRIETARY_PROVIDERS.items() if v.supports_streaming
    ])
    def test_streaming_chat(self, swfte_client, result_collector, provider_key, config):
        """Test streaming chat completion for providers that support it."""
        if config.skip_reason:
            pytest.skip(config.skip_reason)

        start_time = time.time()
        error = None

        try:
            chunks = []
            full_content = ""

            stream = swfte_client.chat.completions.create(
                model=config.chat_model,
                messages=[
                    {"role": "user", "content": "Count from 1 to 5, one number per line."}
                ],
                max_tokens=50,
                stream=True,
            )

            for chunk in stream:
                chunks.append(chunk)
                if chunk.choices and chunk.choices[0].delta:
                    delta_content = chunk.choices[0].delta.content
                    if delta_content:
                        full_content += delta_content

            assert len(chunks) > 1, "Expected multiple chunks"
            assert len(full_content) > 0, "No content from stream"

            passed = True
            metadata = {
                "model": config.chat_model,
                "chunk_count": len(chunks),
                "content_length": len(full_content),
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider=provider_key,
            test_name="streaming_chat",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"{config.name} streaming failed: {error}")

    @pytest.mark.parametrize("provider_key,config", [
        (k, v) for k, v in PROPRIETARY_PROVIDERS.items() if v.embedding_model
    ])
    def test_embeddings(self, swfte_client, result_collector, provider_key, config):
        """Test embedding generation for providers that support it."""
        if config.skip_reason:
            pytest.skip(config.skip_reason)

        start_time = time.time()
        error = None

        try:
            response = swfte_client.embeddings.create(
                model=config.embedding_model,
                input="Hello, world! This is a test of embedding generation.",
            )

            embedding = response.data[0].embedding
            assert isinstance(embedding, list), "Embedding should be a list"
            assert len(embedding) > 0, "Embedding should not be empty"
            assert all(isinstance(x, (int, float)) for x in embedding), "Embedding values should be numbers"

            passed = True
            metadata = {
                "model": config.embedding_model,
                "dimensions": len(embedding),
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider=provider_key,
            test_name="embeddings",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"{config.name} embeddings failed: {error}")


class TestOpenAISpecific:
    """Tests specific to OpenAI capabilities."""

    def test_image_generation_dalle3(self, swfte_client, result_collector, test_results_dir):
        """Test DALL-E 3 image generation."""
        config = PROPRIETARY_PROVIDERS["openai"]
        start_time = time.time()
        error = None

        try:
            response = swfte_client.images.generate(
                model="dall-e-3",
                prompt="A simple blue square on a white background, minimalist style",
                size="1024x1024",
                n=1,
            )

            assert response.data is not None, "No data in response"
            assert len(response.data) > 0, "Empty data list"

            image_data = response.data[0]
            assert image_data.url or image_data.b64_json, "No URL or base64 data"

            passed = True
            metadata = {
                "model": "dall-e-3",
                "has_url": bool(image_data.url),
                "has_b64": bool(getattr(image_data, 'b64_json', None)),
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="openai",
            test_name="image_generation_dalle3",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"DALL-E 3 image generation failed: {error}")

    def test_text_to_speech(self, swfte_client, result_collector, test_results_dir):
        """Test OpenAI text-to-speech."""
        start_time = time.time()
        error = None

        try:
            audio_data = swfte_client.audio.speech.create(
                model="tts-1",
                input="Hello, this is a test of OpenAI text to speech synthesis.",
                voice="alloy",
            )

            assert audio_data is not None, "No audio data"
            assert len(audio_data) > 0, "Empty audio data"

            # Save for later use
            audio_path = test_results_dir / "openai_tts_test.mp3"
            with open(audio_path, "wb") as f:
                f.write(audio_data)

            passed = True
            metadata = {
                "model": "tts-1",
                "voice": "alloy",
                "audio_size_bytes": len(audio_data),
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="openai",
            test_name="text_to_speech",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"OpenAI TTS failed: {error}")

    def test_speech_to_text(self, swfte_client, result_collector, audio_test_file):
        """Test OpenAI speech-to-text (Whisper)."""
        start_time = time.time()
        error = None

        try:
            with open(audio_test_file, "rb") as f:
                audio_data = f.read()

            response = swfte_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_data,
            )

            assert response.text is not None, "No transcription text"
            assert len(response.text) > 0, "Empty transcription"

            passed = True
            metadata = {
                "model": "whisper-1",
                "transcript_length": len(response.text),
                "transcript_preview": response.text[:100] if len(response.text) > 100 else response.text,
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="openai",
            test_name="speech_to_text",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"OpenAI STT failed: {error}")

    def test_function_calling(self, swfte_client, result_collector):
        """Test OpenAI function calling capability."""
        start_time = time.time()
        error = None

        try:
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get the current weather in a given location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "The city and state, e.g. San Francisco, CA"
                                },
                                "unit": {
                                    "type": "string",
                                    "enum": ["celsius", "fahrenheit"],
                                    "description": "Temperature unit"
                                }
                            },
                            "required": ["location"]
                        }
                    }
                }
            ]

            response = swfte_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "What's the weather like in San Francisco?"}
                ],
                tools=tools,
                tool_choice="auto",
                max_tokens=100,
            )

            message = response.choices[0].message
            assert message.tool_calls or message.content, "No tool calls or content"

            passed = True
            metadata = {
                "model": "gpt-4o-mini",
                "has_tool_calls": bool(message.tool_calls),
                "tool_count": len(message.tool_calls) if message.tool_calls else 0,
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="openai",
            test_name="function_calling",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"OpenAI function calling failed: {error}")


# ==================== SELF-HOSTED TESTS ====================

class TestSelfHostedDeployments:
    """Tests for self-hosted RunPod deployments."""

    def test_runpod_qwen_chat(self, swfte_client, result_collector, deployment_ids):
        """Test RunPod Qwen 2.5 deployment."""
        deployment_id = deployment_ids.get("qwen")
        if not deployment_id:
            pytest.skip("QWEN_DEPLOYMENT_ID not set")

        start_time = time.time()
        error = None

        try:
            response = swfte_client.chat.completions.create(
                model=f"deployed:{deployment_id}",
                messages=[
                    {"role": "user", "content": "Explain machine learning in 2 sentences."}
                ],
                max_tokens=100,
                temperature=0.7,
            )

            content = response.choices[0].message.content
            assert content is not None, "No content"
            assert len(content) > 0, "Empty content"

            passed = True
            metadata = {
                "deployment_id": deployment_id,
                "content_length": len(content),
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="runpod_qwen",
            test_name="chat_completion",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"RunPod Qwen chat failed: {error}")

    def test_runpod_qwen_streaming(self, swfte_client, result_collector, deployment_ids):
        """Test RunPod Qwen streaming."""
        deployment_id = deployment_ids.get("qwen")
        if not deployment_id:
            pytest.skip("QWEN_DEPLOYMENT_ID not set")

        start_time = time.time()
        error = None

        try:
            chunks = []
            full_content = ""

            stream = swfte_client.chat.completions.create(
                model=f"deployed:{deployment_id}",
                messages=[
                    {"role": "user", "content": "Count from 1 to 5."}
                ],
                max_tokens=50,
                stream=True,
            )

            for chunk in stream:
                chunks.append(chunk)
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        full_content += delta

            assert len(chunks) > 1, "Expected multiple chunks"
            assert len(full_content) > 0, "No content"

            passed = True
            metadata = {
                "deployment_id": deployment_id,
                "chunk_count": len(chunks),
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="runpod_qwen",
            test_name="streaming",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"RunPod Qwen streaming failed: {error}")

    def test_runpod_llama_chat(self, swfte_client, result_collector, deployment_ids):
        """Test RunPod Llama deployment."""
        deployment_id = deployment_ids.get("llama")
        if not deployment_id:
            pytest.skip("LLAMA_DEPLOYMENT_ID not set")

        start_time = time.time()
        error = None

        try:
            response = swfte_client.chat.completions.create(
                model=f"deployed:{deployment_id}",
                messages=[
                    {"role": "user", "content": "What is Python? Answer in one sentence."}
                ],
                max_tokens=80,
                temperature=0.5,
            )

            content = response.choices[0].message.content
            assert content is not None, "No content"

            passed = True
            metadata = {
                "deployment_id": deployment_id,
                "content_length": len(content),
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="runpod_llama",
            test_name="chat_completion",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"RunPod Llama chat failed: {error}")

    def test_runpod_sdxl_image(self, swfte_client, result_collector, deployment_ids, test_results_dir):
        """Test RunPod ComfyUI SDXL image generation."""
        deployment_id = deployment_ids.get("sdxl")
        if not deployment_id:
            pytest.skip("SDXL_DEPLOYMENT_ID not set")

        start_time = time.time()
        error = None

        try:
            response = swfte_client.images.generate(
                model="comfy:sdxl",
                prompt="A futuristic city at sunset, cyberpunk style, highly detailed",
                size="1024x1024",
                n=1,
            )

            assert response.data, "No data"
            assert len(response.data) > 0, "Empty data"

            image_data = response.data[0]
            assert image_data.url or getattr(image_data, 'b64_json', None), "No image URL or data"

            passed = True
            metadata = {
                "model": "comfy:sdxl",
                "has_url": bool(image_data.url),
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="runpod_sdxl",
            test_name="image_generation",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"RunPod SDXL image generation failed: {error}")

    def test_runpod_tts(self, swfte_client, result_collector, deployment_ids, test_results_dir):
        """Test RunPod XTTS text-to-speech."""
        deployment_id = deployment_ids.get("tts")
        if not deployment_id:
            pytest.skip("TTS_DEPLOYMENT_ID not set")

        start_time = time.time()
        error = None

        try:
            audio_data = swfte_client.audio.speech.create(
                model=f"deployed:{deployment_id}",
                input="Hello from self-hosted text to speech on RunPod.",
                voice="default",
            )

            assert audio_data is not None, "No audio data"
            assert len(audio_data) > 0, "Empty audio"

            # Save for STT test
            audio_path = test_results_dir / "runpod_tts_test.mp3"
            with open(audio_path, "wb") as f:
                f.write(audio_data)

            passed = True
            metadata = {
                "deployment_id": deployment_id,
                "audio_size_bytes": len(audio_data),
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="runpod_tts",
            test_name="text_to_speech",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"RunPod TTS failed: {error}")

    def test_runpod_stt(self, swfte_client, result_collector, deployment_ids, test_results_dir, audio_test_file):
        """Test RunPod Whisper speech-to-text."""
        deployment_id = deployment_ids.get("stt")
        if not deployment_id:
            pytest.skip("STT_DEPLOYMENT_ID not set")

        # Prefer RunPod TTS audio if available
        runpod_audio = test_results_dir / "runpod_tts_test.mp3"
        audio_path = runpod_audio if runpod_audio.exists() else audio_test_file

        start_time = time.time()
        error = None

        try:
            with open(audio_path, "rb") as f:
                audio_data = f.read()

            response = swfte_client.audio.transcriptions.create(
                model=f"deployed:{deployment_id}",
                file=audio_data,
            )

            assert response.text is not None, "No transcript"
            assert len(response.text) > 0, "Empty transcript"

            passed = True
            metadata = {
                "deployment_id": deployment_id,
                "transcript_length": len(response.text),
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="runpod_stt",
            test_name="speech_to_text",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"RunPod STT failed: {error}")


# ==================== ERROR HANDLING TESTS ====================

class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_invalid_model(self, swfte_client, result_collector):
        """Test error handling for invalid model."""
        start_time = time.time()

        try:
            swfte_client.chat.completions.create(
                model="invalid-model-xyz-12345",
                messages=[{"role": "user", "content": "Hello"}],
            )
            passed = False
            error = "Expected exception not raised"
        except Exception as e:
            passed = True
            error = None
            metadata = {"exception_type": type(e).__name__}

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="error_handling",
            test_name="invalid_model",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata if passed else None,
        ))

        if not passed:
            pytest.fail("Invalid model should raise exception")

    def test_empty_messages(self, swfte_client, result_collector):
        """Test error handling for empty messages."""
        start_time = time.time()

        try:
            swfte_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[],
            )
            passed = False
            error = "Expected exception not raised"
        except Exception as e:
            passed = True
            error = None
            metadata = {"exception_type": type(e).__name__}

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="error_handling",
            test_name="empty_messages",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata if passed else None,
        ))

        if not passed:
            pytest.fail("Empty messages should raise exception")

    def test_rate_limit_handling(self, swfte_client, result_collector):
        """Test that rate limiting is properly handled."""
        # This is a soft test - we just verify the client handles responses properly
        start_time = time.time()

        try:
            # Make a simple request
            response = swfte_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )

            # If we got here, rate limiting either didn't happen or was handled
            passed = True
            error = None
            metadata = {"message": "Request completed successfully"}
        except Exception as e:
            # Rate limit errors should be specific exceptions
            passed = "rate" in str(e).lower() or "limit" in str(e).lower()
            error = str(e) if not passed else None
            metadata = {
                "exception_type": type(e).__name__,
                "is_rate_limit": "rate" in str(e).lower() or "limit" in str(e).lower(),
            }

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="error_handling",
            test_name="rate_limit_handling",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))


# ==================== DEPLOYMENT MANAGEMENT TESTS ====================

class TestDeploymentManagement:
    """Tests for deployment management operations."""

    def test_list_models(self, swfte_client, result_collector):
        """Test listing available models."""
        start_time = time.time()
        error = None

        try:
            models = swfte_client.models.list()

            assert models is not None, "No models returned"
            assert isinstance(models, list) or hasattr(models, '__iter__'), "Models should be iterable"

            passed = True
            metadata = {
                "model_count": len(list(models)) if hasattr(models, '__len__') else "unknown",
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="gateway",
            test_name="list_models",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"List models failed: {error}")

    def test_list_deployments(self, swfte_client, result_collector):
        """Test listing deployments."""
        start_time = time.time()
        error = None

        try:
            deployments = swfte_client.deployments.list()

            # Deployments might be empty, that's OK
            assert deployments is not None, "No deployments response"

            passed = True
            metadata = {
                "deployment_count": len(deployments) if hasattr(deployments, '__len__') else "unknown",
            }
        except Exception as e:
            passed = False
            error = str(e)
            metadata = None

        latency = (time.time() - start_time) * 1000

        result_collector.add(TestResult(
            provider="gateway",
            test_name="list_deployments",
            passed=passed,
            latency_ms=latency,
            error=error,
            metadata=metadata,
        ))

        if not passed:
            pytest.fail(f"List deployments failed: {error}")


# ==================== PERFORMANCE TESTS ====================

class TestPerformance:
    """Performance and latency tests."""

    @pytest.mark.parametrize("provider_key,config", [
        ("openai", PROPRIETARY_PROVIDERS["openai"]),
        ("anthropic", PROPRIETARY_PROVIDERS["anthropic"]),
    ])
    def test_latency_baseline(self, swfte_client, result_collector, provider_key, config):
        """Measure baseline latency for quick responses."""
        latencies = []

        for i in range(3):
            start_time = time.time()

            try:
                response = swfte_client.chat.completions.create(
                    model=config.chat_model,
                    messages=[{"role": "user", "content": "Say 'OK'."}],
                    max_tokens=5,
                    temperature=0.0,
                )
                latency = (time.time() - start_time) * 1000
                latencies.append(latency)
            except Exception:
                pass

        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)

            result_collector.add(TestResult(
                provider=provider_key,
                test_name="latency_baseline",
                passed=True,
                latency_ms=avg_latency,
                metadata={
                    "samples": len(latencies),
                    "min_ms": min_latency,
                    "max_ms": max_latency,
                    "avg_ms": avg_latency,
                },
            ))
        else:
            result_collector.add(TestResult(
                provider=provider_key,
                test_name="latency_baseline",
                passed=False,
                latency_ms=0,
                error="All requests failed",
            ))
            pytest.fail("All latency test requests failed")


# ==================== CLI ENTRY POINT ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
