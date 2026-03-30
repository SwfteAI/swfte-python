# Swfte Python SDK

[![PyPI version](https://img.shields.io/pypi/v/swfte.svg)](https://pypi.org/project/swfte/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

The official Python client library for the [Swfte API](https://docs.swfte.com) -- a unified gateway to 200+ AI models from OpenAI, Anthropic, Google, and self-hosted infrastructure through a single interface.

## Documentation

Full API reference and guides are available at [docs.swfte.com](https://docs.swfte.com).

## Installation

```bash
pip install swfte
```

## Quick Start

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...")

response = client.chat.completions.create(
    model="openai:gpt-4",
    messages=[{"role": "user", "content": "Hello, world!"}],
)

print(response["choices"][0]["message"]["content"])
```

## Usage

### Chat Completions

```python
response = client.chat.completions.create(
    model="anthropic:claude-3-opus",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing in one sentence."},
    ],
    temperature=0.7,
    max_tokens=256,
)
```

### Streaming

```python
stream = client.chat.completions.create(
    model="openai:gpt-4",
    messages=[{"role": "user", "content": "Write a short poem."}],
    stream=True,
)

for chunk in stream:
    content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
    print(content, end="", flush=True)
```

### Agents

```python
# Create an agent
agent = client.agents.create(
    name="Research Assistant",
    system_prompt="You are a research assistant specializing in AI.",
    provider="OPENAI",
    model="gpt-4",
)

# List agents
agents = client.agents.list()

# Update an agent
client.agents.update(agent.id, description="Updated description")

# Delete an agent
client.agents.delete(agent.id)
```

### Workflows

```python
# Create a workflow
workflow = client.workflows.create(
    name="Content Pipeline",
    nodes=[
        {"id": "start", "type": "TRIGGER", "config": {"triggerType": "MANUAL"}},
        {"id": "llm", "type": "LLM", "config": {"model": "gpt-4", "prompt": "Summarize: {{input}}"}},
        {"id": "end", "type": "END", "config": {}},
    ],
    edges=[
        {"id": "e1", "source": "start", "target": "llm"},
        {"id": "e2", "source": "llm", "target": "end"},
    ],
)

# Execute a workflow
execution = client.workflows.execute(workflow.id, {"input": "Hello"})

# Check execution status
status = client.workflows.get_execution_status(execution.execution_id)
```

### GPU Model Deployments

```python
# Deploy a model to GPU infrastructure
deployment = client.deployments.create(
    model_name="meta-llama/Llama-3.2-8B-Instruct",
    model_type="chat",
)

# Wait for deployment to be ready
ready = client.deployments.wait_for_ready(deployment.id, timeout_ms=600000)
print(f"Endpoint: {ready.endpoint_url}")

# Clean up
client.deployments.delete(deployment.id)
```

### Images

```python
response = client.images.generate(
    model="openai:dall-e-3",
    prompt="A sunset over a mountain range, oil painting style",
    size="1024x1024",
    quality="hd",
)
```

### Embeddings

```python
response = client.embeddings.create(
    model="openai:text-embedding-3-small",
    input="The quick brown fox jumps over the lazy dog",
)
```

### Audio

```python
# Speech to text
transcript = client.audio.transcriptions.create(
    model="openai:whisper-1",
    file=open("recording.mp3", "rb").read(),
)

# Text to speech
audio_bytes = client.audio.speech.create(
    model="openai:tts-1",
    input="Hello, welcome to Swfte.",
    voice="alloy",
)
```

### Secrets

```python
# Store an API key securely
secret = client.secrets.create(
    name="my-api-key",
    secret_type="API_KEY",
    value="sk-...",
    environment="production",
)

# Validate a secret
is_valid = client.secrets.validate(secret.id)
```

### Conversations

```python
# Create a conversation
conversation = client.conversations.create(title="Support Chat")

# Add messages
client.conversations.add_message(conversation.id, role="user", content="Hello!")
client.conversations.add_message(conversation.id, role="assistant", content="Hi there!")

# Retrieve message history
messages = client.conversations.get_messages(conversation.id)
```

## Configuration

```python
client = SwfteClient(
    api_key="sk-swfte-...",           # Required. Also reads SWFTE_API_KEY env var.
    base_url="https://api.swfte.com/v2/gateway",  # Default
    timeout=60,                        # Request timeout in seconds
    max_retries=3,                     # Retry count for failed requests
    workspace_id="ws-...",             # Workspace scoping. Also reads SWFTE_WORKSPACE_ID.
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | `SWFTE_API_KEY` env | Your Swfte API key |
| `base_url` | `str` | `https://api.swfte.com/v2/gateway` | API base URL |
| `timeout` | `int` | `60` | Request timeout (seconds) |
| `max_retries` | `int` | `3` | Max retry attempts |
| `workspace_id` | `str` | `SWFTE_WORKSPACE_ID` env | Workspace ID |

## Error Handling

```python
from swfte import SwfteClient, AuthenticationError, RateLimitError, APIError

client = SwfteClient(api_key="sk-swfte-...")

try:
    response = client.chat.completions.create(
        model="openai:gpt-4",
        messages=[{"role": "user", "content": "Hello"}],
    )
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded, retry later")
except APIError as e:
    print(f"API error: {e}")
```

| Exception | Description |
|---|---|
| `SwfteError` | Base exception for all SDK errors |
| `AuthenticationError` | Invalid or missing API key |
| `RateLimitError` | Rate limit exceeded (HTTP 429) |
| `APIError` | General API error with status code |
| `InvalidRequestError` | Malformed request (HTTP 400) |

## Supported Providers

| Provider | Models | Qualifier Prefix |
|---|---|---|
| OpenAI | GPT-4, GPT-4o, o1, DALL-E, Whisper, TTS | `openai:` |
| Anthropic | Claude 3.5, Claude 3 Opus/Sonnet/Haiku | `anthropic:` |
| Google | Gemini 2.0, Gemini 1.5 Pro/Flash | `google:` |
| Self-hosted | Any model via RunPod/vLLM deployment | `runpod:` |

## Requirements

- Python 3.8 or later
- `requests` >= 2.28.0

## Contributing

We welcome contributions. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and our [Code of Conduct](CODE_OF_CONDUCT.md).

All contributors must sign the [Swfte CLA](https://cla.swfte.com) before their first pull request can be merged.

## Security

To report a vulnerability, please see [SECURITY.md](SECURITY.md). Do not open a public issue for security concerns.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

Copyright (c) 2025 Swfte, Inc.
