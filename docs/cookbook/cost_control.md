# Cost Control

Routing rules, usage caps and usage statistics — see [Swfte cost control](https://www.swfte.com/products/cost-control).

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# --- Routing rules ---------------------------------------------------------

# Create a rule that re-routes expensive prompts to a cheaper model
rule = client.cost_control.create_routing_rule({
    "name": "Cheap fallback for >2k tokens",
    "match": {"promptTokensGte": 2000},
    "action": {"replaceModel": "anthropic:claude-3-haiku"},
    "enabled": True,
})

print(client.cost_control.list_routing_rules())
print(client.cost_control.get_routing_rule(rule["id"]))

# Toggle on/off without deleting
client.cost_control.toggle_routing_rule(rule["id"], enabled=False)

# Update + delete
client.cost_control.update_routing_rule(rule["id"], {**rule, "name": "Cheap fallback v2"})
client.cost_control.delete_routing_rule(rule["id"])

# --- Usage caps ------------------------------------------------------------

# Workspace-level monthly cap
client.cost_control.set_workspace_cap({"period": "MONTH", "currency": "USD", "limit": 1000})

# Per-model cap
client.cost_control.set_model_cap("openai:gpt-4", {"period": "DAY", "limit": 50})

# List + delete
caps = client.cost_control.list_usage_caps()
for cap in caps:
    print(cap["id"], cap["scope"], cap["limit"])

# --- Stats + autoscaling ---------------------------------------------------

print(client.cost_control.usage_stats(window="7d"))
print(client.cost_control.scaling("deploy-llama-3"))  # replace with your own
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
