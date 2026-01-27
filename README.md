# Swfte Python SDK

[![PyPI Version](https://img.shields.io/pypi/v/swfte-sdk.svg)](https://pypi.org/project/swfte-sdk/)
[![Python Versions](https://img.shields.io/pypi/pyversions/swfte-sdk.svg)](https://pypi.org/project/swfte-sdk/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Build Status](https://img.shields.io/github/actions/workflow/status/swfte/agents-service/python-sdk.yml?branch=main)](https://github.com/swfte/agents-service/actions)
[![Coverage](https://img.shields.io/codecov/c/github/swfte/agents-service)](https://codecov.io/gh/swfte/agents-service)
[![Downloads](https://img.shields.io/pypi/dm/swfte-sdk.svg)](https://pypi.org/project/swfte-sdk/)

The official Python SDK for the Swfte AI Gateway - unified access to all AI providers through a single API.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Features](#features)
- [Supported Models](#supported-models)
- [Examples](#examples)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Installation

```bash
pip install swfte-sdk
```

Or with Poetry:

```bash
poetry add swfte-sdk
```

## Quick Start

```python
from swfte import SwfteClient

# Initialize the client
client = SwfteClient(api_key="sk-swfte-...")

# Chat completion
response = client.chat.completions.create(
    model="openai:gpt-4",  # or "anthropic:claude-3-opus", "deployed:my-model"
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)
print(response.choices[0].message.content)
```

## Features

| Feature | Description |
|---------|-------------|
| **Unified API** | Access OpenAI, Anthropic, Google Gemini, and self-hosted models through one API |
| **OpenAI Compatible** | Drop-in replacement for the OpenAI Python SDK |
| **Streaming Support** | Real-time streaming responses |
| **Automatic Retries** | Built-in retry logic for transient failures |
| **Type Hints** | Full type annotations for better IDE support |
| **Async Support** | Native async/await support for high-performance applications |
| **Rate Limiting** | Automatic rate limit handling with exponential backoff |

## Supported Models

### External Providers

| Provider | Models | Capabilities |
|----------|--------|--------------|
| **OpenAI** | `openai:gpt-4`, `openai:gpt-4-turbo`, `openai:gpt-3.5-turbo`, `openai:dall-e-3`, `openai:whisper-1`, `openai:tts-1` | Chat, Images, Audio, Embeddings |
| **Anthropic** | `anthropic:claude-3-opus`, `anthropic:claude-3-sonnet`, `anthropic:claude-3-haiku` | Chat |
| **Google** | `google:gemini-pro`, `google:gemini-pro-vision` | Chat, Vision |

### Self-Hosted (via RunPod)

| Model | Use Case |
|-------|----------|
| `deployed:llama-3-8b` | Text generation |
| `deployed:sdxl` | Image generation |
| `deployed:whisper-large` | Audio transcription |

## Examples

### Streaming

```python
for chunk in client.chat.completions.create(
    model="openai:gpt-4",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
):
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Image Generation

```python
response = client.images.generate(
    model="openai:dall-e-3",
    prompt="A sunset over mountains in watercolor style",
    size="1024x1024"
)
print(response.data[0].url)
```

### Embeddings

```python
response = client.embeddings.create(
    model="openai:text-embedding-3-small",
    input="The quick brown fox jumps over the lazy dog"
)
print(f"Embedding dimension: {len(response.data[0].embedding)}")
```

### Audio Transcription

```python
with open("audio.mp3", "rb") as f:
    result = client.audio.transcriptions.create(
        model="openai:whisper-1",
        file=f.read()
    )
print(result["text"])
```

### Text-to-Speech

```python
audio = client.audio.speech.create(
    model="openai:tts-1",
    input="Hello world!",
    voice="nova"
)
with open("output.mp3", "wb") as f:
    f.write(audio)
```

### List Models

```python
models = client.models.list()
for model in models:
    print(f"{model.id} - {model.owned_by}")
```

## Configuration

```python
client = SwfteClient(
    api_key="sk-swfte-...",           # Required
    base_url="https://api.swfte.com",  # Optional: custom endpoint
    timeout=60,                        # Optional: request timeout
    max_retries=3,                     # Optional: retry attempts
    workspace_id="ws-123"              # Optional: workspace ID
)
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `SWFTE_API_KEY` | Default API key |
| `SWFTE_WORKSPACE_ID` | Default workspace ID |
| `SWFTE_BASE_URL` | Custom API base URL |

## Error Handling

```python
from swfte import SwfteClient, AuthenticationError, RateLimitError, APIError

client = SwfteClient(api_key="sk-swfte-...")

try:
    response = client.chat.completions.create(
        model="openai:gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded, please try again later")
except APIError as e:
    print(f"API error: {e}")
```

## Documentation

- [API Reference](https://docs.swfte.com/python-sdk)
- [Migration Guide](https://docs.swfte.com/python-sdk/migration)
- [Examples](https://github.com/swfte/agents-service/tree/main/sdks/python/examples)
- [Changelog](CHANGELOG.md)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

Built with love by the [Swfte](https://swfte.com) team.
