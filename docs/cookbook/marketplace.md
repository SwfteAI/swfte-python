# Marketplace

Browse, install and uninstall publications from the [Swfte marketplace](https://www.swfte.com/marketplace).

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# Browse
results = client.marketplace.browse(query="sales", category="agents", page=0, size=20)
for pub in results.get("content", []):
    print(pub["id"], pub["name"])

# Detail page
pub = client.marketplace.get("pub-sdr-pack")  # replace with your own
print(pub["description"], pub["price"])

# Install into the active workspace
installation = client.marketplace.install(
    "pub-sdr-pack",  # replace with your own
    options={"versionTag": "latest"},
)

# List installed publications
for inst in client.marketplace.list_installations().get("content", []):
    print(inst["id"], inst["publicationId"])

# Uninstall
client.marketplace.uninstall(installation["id"])
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
