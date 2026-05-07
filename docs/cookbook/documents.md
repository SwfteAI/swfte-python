# Documents

Upload, process and inspect documents inside a [Swfte dataset](https://www.swfte.com/products/rag).

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

dataset_id = "ds-faq"  # replace with your own

# Create one or many documents
created = client.documents.create(
    dataset_id,
    [
        {"name": "billing-faq.md", "content": "## Refunds\nWe refund within 14 days."},
        {"name": "security.md", "content": "## Data residency\nEU-only by default."},
    ],
)

# List
listing = client.documents.list(dataset_id, page=0, size=50)
print(listing)

# Get + segments
doc_id = created["documents"][0]["id"]
doc = client.documents.get(dataset_id, doc_id)
segments = client.documents.segments(dataset_id, doc_id)

# Update + retry processing
client.documents.update(dataset_id, doc_id, {"name": "billing-faq-v2.md"})
client.documents.retry(dataset_id, doc_id)

# Pause / resume
client.documents.pause(dataset_id, doc_id)
client.documents.resume(dataset_id, doc_id)

# Batch update + status
batch = client.documents.batch_update(dataset_id, [{"id": doc_id, "metadata": {"team": "ops"}}])
print(client.documents.batch_status(dataset_id, batch["batchId"]))

# Aggregated processing status for the whole dataset
print(client.documents.processing_status(dataset_id))

# Delete
client.documents.delete(dataset_id, doc_id)
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
