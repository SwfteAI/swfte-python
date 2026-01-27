#!/usr/bin/env python3
"""
Comprehensive Gateway Test Script - Python SDK
Tests all modalities: Chat, Embeddings, Images, TTS, STT
Tests all providers: OpenAI, Anthropic, RunPod
"""
import os
import sys
import time

# Add SDK to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swfte import SwfteClient
from swfte.exceptions import APIError

# Configure client for local gateway
client = SwfteClient(
    api_key="test-api-key",
    base_url="http://localhost:3388/v2/gateway",
    workspace_id="test-workspace"
)

# ==================== PROPRIETARY PROVIDER TESTS ====================

def test_openai_chat():
    """Test OpenAI GPT-4o-mini chat completion"""
    print("\n=== Test: OpenAI Chat ===")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'Hello from OpenAI' in exactly 3 words"}],
        max_tokens=20,
        temperature=0.0
    )
    content = response.choices[0].message.content
    print(f"Response: {content}")
    assert content is not None
    print("PASSED: OpenAI Chat")
    return True


def test_anthropic_chat():
    """Test Anthropic Claude chat completion"""
    print("\n=== Test: Anthropic Chat ===")
    response = client.chat.completions.create(
        model="claude-3-haiku-20240307",
        messages=[{"role": "user", "content": "Say 'Hello from Claude' in exactly 3 words"}],
        max_tokens=20,
        temperature=0.0
    )
    content = response.choices[0].message.content
    print(f"Response: {content}")
    assert content is not None
    print("PASSED: Anthropic Chat")
    return True


def test_embeddings():
    """Test embeddings generation"""
    print("\n=== Test: Embeddings ===")
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input="Hello world"
    )
    embedding = response.data[0].embedding
    print(f"Embedding dimensions: {len(embedding)}")
    assert len(embedding) == 1536  # text-embedding-3-small returns 1536 dims
    print("PASSED: Embeddings")
    return True


def test_image_generation_dalle():
    """Test DALL-E image generation"""
    print("\n=== Test: DALL-E Image Generation ===")
    response = client.images.generate(
        model="dall-e-3",
        prompt="A simple blue square on white background",
        size="1024x1024",
        n=1
    )
    url = response.data[0].url
    print(f"Image URL: {url[:80]}...")
    assert url is not None and url.startswith("http")
    print("PASSED: DALL-E Image Generation")
    return True


def test_tts():
    """Test OpenAI text-to-speech"""
    print("\n=== Test: OpenAI Text-to-Speech ===")
    audio_data = client.audio.speech.create(
        model="tts-1",
        input="Hello, this is a test of OpenAI text to speech.",
        voice="alloy"
    )
    print(f"Audio size: {len(audio_data)} bytes")
    assert len(audio_data) > 0
    # Save to file for STT test
    with open("/tmp/test_speech_python.mp3", "wb") as f:
        f.write(audio_data)
    print("PASSED: OpenAI TTS (saved to /tmp/test_speech_python.mp3)")
    return True


def test_stt():
    """Test OpenAI speech-to-text"""
    print("\n=== Test: OpenAI Speech-to-Text ===")
    # Use audio from TTS test
    with open("/tmp/test_speech_python.mp3", "rb") as f:
        audio_data = f.read()

    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_data
    )
    text = result.get("text", "")
    print(f"Transcript: {text}")
    assert text is not None and len(text) > 0
    print("PASSED: OpenAI STT")
    return True


def test_streaming_chat():
    """Test streaming chat completion"""
    print("\n=== Test: Streaming Chat ===")
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Count from 1 to 5, one number per line"}],
        max_tokens=50,
        stream=True
    )
    content = ""
    print("Streaming: ", end="")
    for chunk in stream:
        if chunk.choices:
            choice = chunk.choices[0]
            # Handle both streaming (delta) and wrapped (message) formats
            if hasattr(choice, 'delta') and choice.delta and choice.delta.content:
                content += choice.delta.content
                print(choice.delta.content, end="", flush=True)
            elif hasattr(choice, 'message') and choice.message and choice.message.content:
                content += choice.message.content
                print(choice.message.content, end="", flush=True)
    print()
    assert len(content) > 0
    print("PASSED: Streaming Chat")
    return True


def test_error_handling():
    """Test error handling"""
    print("\n=== Test: Error Handling ===")
    try:
        client.chat.completions.create(
            model="invalid-model-xyz-12345",
            messages=[{"role": "user", "content": "Hello"}]
        )
        print("FAILED: Should have raised an exception")
        return False
    except APIError as e:
        print(f"Got expected APIError: {type(e).__name__}")
        print("PASSED: Error Handling")
        return True
    except Exception as e:
        print(f"Got exception (acceptable): {type(e).__name__}: {str(e)[:100]}")
        print("PASSED: Error Handling")
        return True


# ==================== RUNPOD TESTS ====================

# Set these after deploying models on RunPod
QWEN_DEPLOYMENT_ID = os.environ.get("QWEN_DEPLOYMENT_ID", "")
TTS_DEPLOYMENT_ID = os.environ.get("TTS_DEPLOYMENT_ID", "")
STT_DEPLOYMENT_ID = os.environ.get("STT_DEPLOYMENT_ID", "")
COMFYUI_DEPLOYMENT_ID = os.environ.get("COMFYUI_DEPLOYMENT_ID", "")


def test_qwen_chat():
    """Test Qwen 2.5 on RunPod"""
    if not QWEN_DEPLOYMENT_ID:
        print("\n=== Test: Qwen 2.5 Chat (RunPod) - SKIPPED (no deployment ID) ===")
        return None

    print("\n=== Test: Qwen 2.5 Chat (RunPod) ===")
    response = client.chat.completions.create(
        model=f"deployed:{QWEN_DEPLOYMENT_ID}",
        messages=[{"role": "user", "content": "Explain machine learning in 2 sentences"}],
        max_tokens=100,
        temperature=0.7
    )
    content = response.choices[0].message.content
    print(f"Response: {content}")
    assert content is not None
    print("PASSED: Qwen 2.5 Chat")
    return True


def test_runpod_tts():
    """Test TTS on RunPod"""
    if not TTS_DEPLOYMENT_ID:
        print("\n=== Test: TTS (RunPod) - SKIPPED (no deployment ID) ===")
        return None

    print("\n=== Test: TTS (RunPod) ===")
    audio_data = client.audio.speech.create(
        model=f"deployed:{TTS_DEPLOYMENT_ID}",
        input="Hello from self-hosted text to speech on RunPod.",
        voice="alloy"
    )
    print(f"Audio size: {len(audio_data)} bytes")
    with open("/tmp/test_runpod_speech.mp3", "wb") as f:
        f.write(audio_data)
    assert len(audio_data) > 0
    print("PASSED: RunPod TTS")
    return True


def test_runpod_stt():
    """Test STT on RunPod"""
    if not STT_DEPLOYMENT_ID:
        print("\n=== Test: STT (RunPod) - SKIPPED (no deployment ID) ===")
        return None

    print("\n=== Test: STT (RunPod) ===")
    # Use audio from runpod TTS test or OpenAI TTS
    audio_file = "/tmp/test_runpod_speech.mp3" if os.path.exists("/tmp/test_runpod_speech.mp3") else "/tmp/test_speech_python.mp3"
    with open(audio_file, "rb") as f:
        audio_data = f.read()

    result = client.audio.transcriptions.create(
        model=f"deployed:{STT_DEPLOYMENT_ID}",
        file=audio_data
    )
    text = result.get("text", "")
    print(f"Transcript: {text}")
    assert text is not None
    print("PASSED: RunPod STT")
    return True


def test_comfyui_image():
    """Test ComfyUI SDXL image generation"""
    if not COMFYUI_DEPLOYMENT_ID:
        print("\n=== Test: ComfyUI SDXL Image (RunPod) - SKIPPED (no deployment ID) ===")
        return None

    print("\n=== Test: ComfyUI SDXL Image (RunPod) ===")
    response = client.images.generate(
        model=f"comfy:sdxl",
        prompt="A futuristic city skyline at sunset, cyberpunk style",
        size="1024x1024",
        n=1
    )
    url = response.data[0].url
    print(f"Image URL: {url[:80] if url else 'None'}...")
    assert url is not None
    print("PASSED: ComfyUI Image")
    return True


# ==================== MAIN ====================

if __name__ == "__main__":
    print("=" * 60)
    print("Comprehensive Gateway Test - Python SDK")
    print(f"Base URL: {client.base_url}")
    print(f"Workspace: {client.workspace_id}")
    print("=" * 60)

    # Proprietary provider tests
    proprietary_tests = [
        ("OpenAI Chat", test_openai_chat),
        ("Anthropic Chat", test_anthropic_chat),
        ("Embeddings", test_embeddings),
        ("DALL-E Image", test_image_generation_dalle),
        ("OpenAI TTS", test_tts),
        ("OpenAI STT", test_stt),
        ("Streaming Chat", test_streaming_chat),
        ("Error Handling", test_error_handling),
    ]

    # RunPod tests
    runpod_tests = [
        ("Qwen 2.5 Chat", test_qwen_chat),
        ("ComfyUI SDXL", test_comfyui_image),
        ("RunPod TTS", test_runpod_tts),
        ("RunPod STT", test_runpod_stt),
    ]

    all_tests = proprietary_tests + runpod_tests

    passed = 0
    failed = 0
    skipped = 0

    for name, test_fn in all_tests:
        try:
            result = test_fn()
            if result is True:
                passed += 1
            elif result is None:
                skipped += 1
            else:
                failed += 1
        except Exception as e:
            print(f"FAILED: {name}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)

    # Exit with error code if any tests failed
    sys.exit(1 if failed > 0 else 0)
