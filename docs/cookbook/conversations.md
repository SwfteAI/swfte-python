# Conversations

Initiate outbound (or capture inbound) conversations across web, voice and messaging — see [Swfte voice & chat](https://www.swfte.com/products/voice).

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# Create / initiate
conv = client.conversations.create(
    title="Onboarding chat",
    agent_id="agent-onboarding",  # replace with your own
    model="openai:gpt-4",
    system_prompt="You are an onboarding specialist.",
)

# Add messages (V1 history surface)
client.conversations.add_message(conv.id, role="user", content="Hi, I just signed up")
client.conversations.add_message(conv.id, role="assistant", content="Welcome! What's your use-case?")

# List + Get
for c in client.conversations.list(page=0, size=20):
    print(c.id, c.title)
conv = client.conversations.get(conv.id)

# Get the message page
page = client.conversations.get_messages(conv.id, limit=50)
for m in page.messages:
    print(m.role, m.content)

# Clear / delete
client.conversations.clear_messages(conv.id)
client.conversations.delete(conv.id)
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
