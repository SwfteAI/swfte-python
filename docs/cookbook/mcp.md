# MCP — Model Context Protocol

Connect remote MCP servers, list tools, execute (single or batch) and audit usage — see [Swfte MCP](https://www.swfte.com/products/mcp).

```python
from swfte import SwfteClient

client = SwfteClient(api_key="sk-swfte-...", workspace_id="ws-demo")  # replace with your own

# Connect a remote MCP server
server = client.mcp.connect_server(
    provider_id="hubspot",
    endpoint="https://mcp.example.com/hubspot/sse",
    auth={"type": "bearer", "token": "tok-..."},
)

# List connected servers + their tools
print(client.mcp.list_servers())
tools = client.mcp.list_tools()

# Inspect schema + execute a single tool
tool_id = tools[0]["id"]
print(client.mcp.tool_schema(tool_id))
result = client.mcp.execute(tool_id, arguments={"email": "ada@example.com"})

# Batch execute
batch = client.mcp.batch_execute([
    {"toolId": tool_id, "arguments": {"email": "ada@example.com"}},
    {"toolId": tool_id, "arguments": {"email": "linus@example.com"}},
])

# Health + analytics
print(client.mcp.health_check())
print(client.mcp.tool_status(tool_id))
print(client.mcp.analytics(window="24h"))

# Disconnect
client.mcp.disconnect_server(server["providerId"])
```

Full reference at [swfte.com/developers](https://www.swfte.com/developers).
