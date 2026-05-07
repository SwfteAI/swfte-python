# Modules

Bundle agents, workflows, tools and datasets into reusable, versioned [Swfte modules](https://www.swfte.com/marketplace).

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# Create
mod = client.modules.create(
    name="Sales Pack",
    description="SDR agent + HubSpot tools + product FAQ dataset",
)

# Attach resources
client.modules.add_resource(mod["id"], {"type": "AGENT", "id": "agent-sdr"})  # replace with your own
client.modules.add_resource(mod["id"], {"type": "DATASET", "id": "ds-faq"})  # replace with your own
client.modules.add_resource(mod["id"], {"type": "TOOL", "id": "tool-hubspot"})  # replace with your own

# Build (compile) so it can be installed elsewhere
client.modules.build(mod["id"], options={"includeQA": True})

# Stream build progress
resp = client.modules.build_progress(mod["id"])
for line in resp.iter_lines():
    if line:
        print(line.decode())

# Versions
versions = client.modules.list_versions(mod["id"])
v = versions[-1]
print(client.modules.get_version(mod["id"], v["version"]))
print(client.modules.get_qa(mod["id"], v["version"]))

# Impact report
print(client.modules.impact(mod["id"]))

# List + Get + Update + Remove
client.modules.list()
mod = client.modules.get(mod["id"])
client.modules.update(mod["id"], {"description": "SDR pack v2"})
client.modules.remove_resource(mod["id"], "tool-hubspot")  # replace with your own

# Delete
client.modules.delete(mod["id"])
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
