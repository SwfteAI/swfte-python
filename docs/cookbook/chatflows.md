# ChatFlows

Build, validate, deploy and run conversational forms with [Swfte ChatFlows](https://www.swfte.com/products/chatflows).

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# Browse builder primitives
print(client.chatflows.field_types())
print(client.chatflows.action_types())
print(client.chatflows.press_strategies())

# Create
flow = client.chatflows.create({
    "name": "Lead Qualification",
    "fields": [
        {"key": "name", "label": "Your name", "type": "TEXT"},
        {"key": "company", "label": "Company", "type": "TEXT"},
        {"key": "team_size", "label": "Team size", "type": "NUMBER"},
    ],
    "channel": "WEB",
})

# Validate, deploy, start a session, fetch stats
client.chatflows.validate(flow["id"])
client.chatflows.deploy(flow["id"], channel="WEB")
session = client.chatflows.start_session(flow["id"], channel="WEB", context={"utm_source": "blog"})
stats = client.chatflows.stats(flow["id"])
print(session["sessionId"], stats)

# Update + version
client.chatflows.update(flow["id"], {"name": "Lead Qualification v2"})
v = client.chatflows.create_version(flow["id"], notes="Tone tweaks")
client.chatflows.promote_version(flow["id"], v["version"])

# Publish
client.chatflows.publish(flow["id"], {"slug": "lead-qual"})
print(client.chatflows.get_published(flow["id"]))

# Cleanup
client.chatflows.undeploy(flow["id"])
client.chatflows.delete(flow["id"])
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
