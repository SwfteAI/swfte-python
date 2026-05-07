# Agents

Create, retrieve, update and delete production-grade [Swfte agents](https://www.swfte.com/products/agents), associate workflows, manage canvas metadata, and append session events.

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# Create
agent = client.agents.create(
    name="Sales Triage",
    description="Qualifies inbound leads",
    system_prompt="You are an SDR for an AI infrastructure company.",
    provider="OPENAI",
    model="gpt-4",
    temperature=0.3,
)

# List
for a in client.agents.list(page=1, size=20):
    print(a.id, a.agent_name)

# Get
agent = client.agents.get(agent.id)

# Update (PATCH)
agent = client.agents.patch(agent.id, description="Updated SDR")

# Associate a workflow (V2)
agent = client.agents.associate_workflow(agent.id, workflow_id="wf-123")  # replace with your own

# Update avatar
client.agents.update_avatar(agent.id, {"theme": "indigo", "imageUrl": "https://example.com/a.png"})

# Append a session event (e.g. an annotation to a live conversation)
import requests
url = f"{client.base_url.rstrip('/').replace('/v2/gateway', '')}/v2/agents/{agent.id}/session/events"
requests.post(url, headers=client._get_headers(), json={"type": "NOTE", "data": {"text": "follow up"}})

# Delete
client.agents.delete(agent.id)
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
