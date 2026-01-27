---
name: Bug Report
about: Report a bug to help us improve the Swfte Python SDK
title: '[BUG] '
labels: bug
assignees: ''
---

## Description

A clear and concise description of what the bug is.

## Environment

- **SDK Version**: (e.g., 1.0.0)
- **Python Version**: (e.g., 3.11.0)
- **Operating System**: (e.g., macOS 14.0, Ubuntu 22.04, Windows 11)
- **Installation Method**: (pip, poetry, conda)

## Steps to Reproduce

1. Initialize client with '...'
2. Call method '...'
3. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

A clear and concise description of what actually happened.

## Code Sample

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...")

# Minimal code to reproduce the issue
response = client.chat.completions.create(
    model="openai:gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Stack Trace

```
Paste the full error message and stack trace here
```

## Additional Context

Add any other context about the problem here (screenshots, logs, related issues, etc.).

## Possible Solution

(Optional) If you have suggestions on how to fix the bug.
