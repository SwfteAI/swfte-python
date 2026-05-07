# Files

Upload, list, download and clean up workspace files. Files can back avatars, datasets, training corpora and ChatFlow attachments — see the [Swfte platform overview](https://www.swfte.com).

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# Discover upload constraints
print(client.files.config())

# Upload a single file
with open("brochure.pdf", "rb") as fh:
    f = client.files.upload(
        ("brochure.pdf", fh, "application/pdf"),
        usage="DATASET",
        metadata={"team": "marketing"},
    )

# Upload a batch
with open("a.png", "rb") as a, open("b.png", "rb") as b:
    batch = client.files.upload_batch(
        [("a.png", a, "image/png"), ("b.png", b, "image/png")],
        usage="AVATAR",
    )

# List + Get metadata
for fobj in client.files.list(page=0, size=20).get("content", []):
    print(fobj["id"], fobj["name"])
meta = client.files.get(f["id"])

# Download (raw bytes) + preview
raw = client.files.download(f["id"])
preview = client.files.preview(f["id"])

# Update usage label
client.files.update_usage(f["id"], usage="DATASET")

# Cleanup orphaned files
print(client.files.cleanup())

# Delete
client.files.delete(f["id"])
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
