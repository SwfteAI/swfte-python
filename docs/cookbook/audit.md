# Audit

Query and export the audit trail. Every action is recorded — see [Swfte security](https://www.swfte.com/security).

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# Workspace-wide event query (filterable)
events = client.audit.list_events(
    actor_id="user-ada",  # replace with your own
    action="agent.update",
    from_="2026-04-01T00:00:00Z",
    to="2026-05-01T00:00:00Z",
    page=0,
    size=50,
)

# Resource-scoped trail
agent_history = client.audit.resource_events("agent", "agent-sdr")  # replace with your own

# My events (the calling principal)
mine = client.audit.my_events(page=0, size=50)

# Export — returns raw bytes (CSV by default)
csv_bytes = client.audit.export(format="csv", from_="2026-04-01T00:00:00Z")
with open("audit-2026-04.csv", "wb") as fh:
    fh.write(csv_bytes)
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
