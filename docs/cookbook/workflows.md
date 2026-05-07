# Workflows

Author, version, validate and execute durable DAGs with [Swfte Workflows](https://www.swfte.com/products/workflows).

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# Create
workflow = client.workflows.create(
    name="Content Pipeline",
    description="Summarise + translate",
    nodes=[
        {"id": "start", "type": "TRIGGER", "config": {"triggerType": "MANUAL"}},
        {"id": "summarise", "type": "LLM", "config": {"model": "openai:gpt-4", "prompt": "Summarise: {{input}}"}},
        {"id": "translate", "type": "LLM", "config": {"model": "anthropic:claude-3-haiku", "prompt": "Translate to French: {{summarise.output}}"}},
        {"id": "end", "type": "END", "config": {}},
    ],
    edges=[
        {"id": "e1", "source": "start", "target": "summarise"},
        {"id": "e2", "source": "summarise", "target": "translate"},
        {"id": "e3", "source": "translate", "target": "end"},
    ],
)

# Validate the JSON without persisting (POST /v2/workflows/validate)
client.workflows.validate({"nodes": [], "edges": []})

# List + Get
for wf in client.workflows.list():
    print(wf.id, wf.name)
wf = client.workflows.get(workflow.id)

# Execute
execution = client.workflows.execute(workflow.id, {"input": "Long article body..."})
status = client.workflows.get_execution_status(execution.execution_id)
print(status)

# Clone, export
cloned = client.workflows.clone(workflow.id, name="Content Pipeline (copy)")
exported_json = client.workflows.export(workflow.id)

# Delete
client.workflows.delete(workflow.id)
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
