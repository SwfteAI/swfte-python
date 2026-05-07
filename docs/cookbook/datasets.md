# Datasets

Group documents for retrieval-augmented generation — see [Swfte RAG](https://www.swfte.com/products/rag).

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# Create
ds = client.datasets.create(
    name="Product FAQ",
    description="Customer-facing FAQ entries",
    embedding_model="openai:text-embedding-3-small",
    retrieval_strategy="HYBRID",
)

# List
for d in client.datasets.list(page=0, size=20).get("content", []):
    print(d["id"], d["name"])

# Get + update
ds = client.datasets.get(ds["id"])
client.datasets.update(ds["id"], {"description": "FAQ — updated"})

# Check usage before deletion
print(client.datasets.use_check(ds["id"]))

# Toggle public API access
client.datasets.set_api_access(ds["id"], "enable")

# Delete
client.datasets.delete(ds["id"])
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
