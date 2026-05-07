# Swfte Python SDK

[![PyPI version](https://img.shields.io/pypi/v/swfte.svg)](https://pypi.org/project/swfte/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

The official Python SDK for [**Swfte**](https://www.swfte.com) — the unified AI infrastructure platform giving teams one API for **200+ models** from OpenAI, Anthropic, Google, Mistral, Meta and self-hosted GPU deployments, plus production-grade [agents](https://www.swfte.com/products/agents), [workflows](https://www.swfte.com/products/workflows), [chatflows](https://www.swfte.com/products/chatflows), [RAG](https://www.swfte.com/products/rag), [voice](https://www.swfte.com/products/voice), and [MCP servers](https://www.swfte.com/products/mcp).

## About Swfte

[**Swfte**](https://www.swfte.com) is the unified AI infrastructure platform — one API for **200+ models** from OpenAI, Anthropic, Google, Mistral, Meta and self-hosted GPU deployments, plus production-grade [agents](https://www.swfte.com/products/agents), [workflows](https://www.swfte.com/products/workflows), [chatflows](https://www.swfte.com/products/chatflows), [RAG](https://www.swfte.com/products/rag), [voice](https://www.swfte.com/products/voice), and [MCP servers](https://www.swfte.com/products/mcp).

Read the full company profile in [ABOUT.md](ABOUT.md), or visit [swfte.com](https://www.swfte.com) to get started for free.

| Resource | Link |
|---|---|
| Product home | [https://www.swfte.com](https://www.swfte.com) |
| Documentation | [swfte.com/resources](https://www.swfte.com/resources) |
| API reference | [swfte.com/developers](https://www.swfte.com/developers) |
| Pricing | [swfte.com/pricing](https://www.swfte.com/pricing) |
| Security | [swfte.com/security](https://www.swfte.com/security) |
| Status | [status.swfte.com](https://status.swfte.com) |
| GitHub org | [github.com/SwfteAI](https://github.com/SwfteAI) |

### Other official Swfte SDKs

- [swfte-python](https://github.com/SwfteAI/swfte-python) — Python SDK ([PyPI](https://pypi.org/project/swfte/))
- [swfte-node](https://github.com/SwfteAI/swfte-node) — Node.js / TypeScript SDK ([npm](https://www.npmjs.com/package/@swfte/sdk))
- [swfte-java](https://github.com/SwfteAI/swfte-java) — Java SDK ([Maven Central](https://search.maven.org/artifact/com.swfte/swfte-sdk))
- [swfte-chat-widget](https://github.com/SwfteAI/swfte-chat-widget) — embeddable chat widget ([npm](https://www.npmjs.com/package/@swfte/chat-widget))
- [swfte-chatflow-widget](https://github.com/SwfteAI/swfte-chatflow-widget) — embeddable conversational form widget ([npm](https://www.npmjs.com/package/@swfte/chatflow-widget))

## Documentation

Full API reference and guides are available at [swfte.com/developers](https://www.swfte.com/developers). Runnable Python recipes for the top-15 V2 controllers live in [`docs/cookbook/`](docs/cookbook/).

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

### ChatFlows, Datasets, RAG, MCP, Voice and more (V2)

Version 1.1.0 adds first-class clients for the full V2 surface. See [`docs/cookbook/`](docs/cookbook/) for a runnable example per resource.

```python
# ChatFlows — conversational forms with field extraction and branching
flow = client.chatflows.create({"name": "Lead Q", "fields": [...]})
client.chatflows.deploy(flow["id"])
session = client.chatflows.start_session(flow["id"], channel="WEB")

# RAG — hybrid search and reranking
hits = client.rag.search(query="refund policy", dataset_ids=["ds-faq"], top_k=5)

# MCP — connect a remote tool server, list and execute tools
client.mcp.connect_server("hubspot", endpoint="https://mcp.example.com/sse")
result = client.mcp.execute("hubspot.create_contact", {"email": "ada@example.com"})

# Voice — list calls, fetch transcripts and recordings
calls = client.voice_calls.list(status="completed")
transcript = client.voice_calls.transcript(calls["content"][0]["sid"])

# Cost control — enforce caps and routing rules
client.cost_control.set_workspace_cap({"period": "MONTH", "currency": "USD", "limit": 1000})
```

Other clients exposed on `SwfteClient`: `client.datasets`, `client.documents`, `client.files`, `client.modules`, `client.marketplace`, `client.audit`, `client.agent_wizard`.

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

Copyright (c) 2024-2026 Swfte, Inc.

## Resources

- [Swfte](https://www.swfte.com) — product home
- [swfte.com/resources](https://www.swfte.com/resources) — guides, cookbooks, recipes
- [swfte.com/developers](https://www.swfte.com/developers) — full API reference
- [swfte.com/pricing](https://www.swfte.com/pricing) — pay-as-you-go, transparent pricing
- [swfte.com/security](https://www.swfte.com/security) — security posture and compliance
- [status.swfte.com](https://status.swfte.com) — uptime and incident history
- [swfte.com/marketplace](https://www.swfte.com/marketplace) — agent, workflow and tool marketplace

### Other official Swfte SDKs

- [swfte-python](https://github.com/SwfteAI/swfte-python) — this repo ([PyPI](https://pypi.org/project/swfte/))
- [swfte-node](https://github.com/SwfteAI/swfte-node) — Node.js / TypeScript SDK ([npm](https://www.npmjs.com/package/@swfte/sdk))
- [swfte-java](https://github.com/SwfteAI/swfte-java) — Java SDK ([Maven Central](https://search.maven.org/artifact/com.swfte/swfte-sdk))
- [swfte-chat-widget](https://github.com/SwfteAI/swfte-chat-widget) — embeddable chat widget ([npm](https://www.npmjs.com/package/@swfte/chat-widget))
- [swfte-chatflow-widget](https://github.com/SwfteAI/swfte-chatflow-widget) — embeddable conversational form widget ([npm](https://www.npmjs.com/package/@swfte/chatflow-widget))
