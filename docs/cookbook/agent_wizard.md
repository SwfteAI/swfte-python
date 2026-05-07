# Agent Wizard

Generate, refine and persist agents from plain-English prompts via the [Swfte agent wizard](https://www.swfte.com/products/agents).

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# 1. Browse what's available
print(client.agent_wizard.agent_types())
print(client.agent_wizard.providers())
print(client.agent_wizard.templates())

# 2. Generate a draft from a natural-language prompt
draft = client.agent_wizard.generate(
    prompt="An SDR that qualifies inbound B2B SaaS leads on a 5-question script",
    agent_type="conversational",
    provider="OPENAI",
)

# 3. Review + refine until happy
review = client.agent_wizard.review(draft)
draft = client.agent_wizard.refine(draft, feedback="Make the tone less salesy")

# 4. Persist
agent = client.agent_wizard.create(draft)

# 5. Wire MCP tools and knowledge bases
client.agent_wizard.link_tools(agent["id"], tool_ids=["tool-hubspot-create-contact"])  # replace with your own
client.agent_wizard.link_knowledge(agent["id"], dataset_ids=["ds-pricing", "ds-faq"])  # replace with your own

# Alternative: shortcut path that skips the review step
quick_agent = client.agent_wizard.quick(prompt="A polite support triage assistant")

# Alternative: spawn from a template
from_template = client.agent_wizard.from_template(
    "support-triage",
    overrides={"name": "Tier-1 Support"},
)
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
