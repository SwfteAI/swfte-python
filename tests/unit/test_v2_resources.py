"""
Unit tests for the new V2 resource clients.

We mock ``requests.request`` and assert URL, method, headers and (where
relevant) the JSON body.
"""

from unittest.mock import patch


def _kw(mock_req, idx=-1):
    return mock_req.call_args_list[idx][1]


class TestDatasets:
    def test_list_create_get_update_delete(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory({"content": []})) as mock_req:
            mock_client.datasets.list(page=0, size=20)
            kw = _kw(mock_req)
            assert kw["method"] == "GET"
            assert kw["url"].endswith("/api/v2/datasets")
            assert kw["params"]["page"] == 0

            mock_client.datasets.create(name="X", description="d", embedding_model="m")
            kw = _kw(mock_req)
            assert kw["method"] == "POST"
            assert kw["json"]["name"] == "X"
            assert kw["json"]["embeddingModel"] == "m"

            mock_client.datasets.get("ds-1")
            assert _kw(mock_req)["url"].endswith("/api/v2/datasets/ds-1")

            mock_client.datasets.set_api_access("ds-1", "enable")
            assert _kw(mock_req)["url"].endswith("/api/v2/datasets/ds-1/api-access/enable")

            mock_client.datasets.delete("ds-1")
            assert _kw(mock_req)["method"] == "DELETE"


class TestDocuments:
    def test_paths(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory({})) as mock_req:
            mock_client.documents.create("ds-1", [{"name": "a"}])
            kw = _kw(mock_req)
            assert kw["url"].endswith("/api/v2/datasets/ds-1/documents")
            assert kw["json"] == {"documents": [{"name": "a"}]}

            mock_client.documents.segments("ds-1", "doc-1")
            assert _kw(mock_req)["url"].endswith("/api/v2/datasets/ds-1/documents/doc-1/segments")

            mock_client.documents.batch_status("ds-1", "b-7")
            assert _kw(mock_req)["url"].endswith("/api/v2/datasets/ds-1/documents/batch/b-7/status")


class TestFiles:
    def test_paths_and_headers(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory({})) as mock_req:
            mock_client.files.config()
            assert _kw(mock_req)["url"].endswith("/api/v2/files/config")

            mock_client.files.list(page=0, size=20)
            assert _kw(mock_req)["url"].endswith("/api/v2/files")

            mock_client.files.delete("f-1")
            assert _kw(mock_req)["method"] == "DELETE"

            mock_client.files.update_usage("f-1", "DATASET")
            assert _kw(mock_req)["json"] == {"usage": "DATASET"}


class TestRag:
    def test_search_rerank_strategies(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory({"results": []})) as mock_req:
            mock_client.rag.search("hi", dataset_ids=["a", "b"], strategy="HYBRID", top_k=5)
            kw = _kw(mock_req)
            assert kw["method"] == "POST"
            assert kw["url"].endswith("/v2/rag/search")
            assert kw["json"]["query"] == "hi"
            assert kw["json"]["datasetIds"] == ["a", "b"]
            assert kw["json"]["strategy"] == "HYBRID"
            assert kw["json"]["topK"] == 5

            mock_client.rag.rerank("hi", [{"id": "x"}], model="cohere:rerank")
            kw = _kw(mock_req)
            assert kw["url"].endswith("/v2/rag/rerank")
            assert kw["json"]["model"] == "cohere:rerank"

            mock_client.rag.strategies()
            assert _kw(mock_req)["url"].endswith("/v2/rag/strategies")


class TestMcp:
    def test_connect_list_execute(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory([])) as mock_req:
            mock_client.mcp.connect_server("hubspot", "https://x", auth={"type": "bearer", "token": "t"})
            kw = _kw(mock_req)
            assert kw["url"].endswith("/api/v2/mcp/servers/connect")
            assert kw["json"]["providerId"] == "hubspot"

            mock_client.mcp.list_tools()
            assert _kw(mock_req)["url"].endswith("/api/v2/mcp/tools")

            mock_client.mcp.execute("tool-1", {"x": 1})
            kw = _kw(mock_req)
            assert kw["url"].endswith("/api/v2/mcp/tools/tool-1/execute")
            assert kw["json"] == {"arguments": {"x": 1}}


class TestModules:
    def test_basic(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory({"id": "m-1"})) as mock_req:
            mock_client.modules.create(name="Pack")
            assert _kw(mock_req)["json"]["name"] == "Pack"

            mock_client.modules.add_resource("m-1", {"type": "AGENT", "id": "a-1"})
            assert _kw(mock_req)["url"].endswith("/v2/modules/m-1/resources")

            mock_client.modules.build("m-1")
            assert _kw(mock_req)["url"].endswith("/v2/modules/m-1/build")

            mock_client.modules.impact("m-1")
            assert _kw(mock_req)["url"].endswith("/v2/modules/m-1/impact")


class TestMarketplace:
    def test_browse_install_uninstall(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory({"content": []})) as mock_req:
            mock_client.marketplace.browse(query="sales", category="agents")
            kw = _kw(mock_req)
            assert kw["url"].endswith("/v2/marketplace")
            assert kw["params"]["q"] == "sales"

            mock_client.marketplace.install("pub-1", {"versionTag": "latest"})
            assert _kw(mock_req)["url"].endswith("/v2/marketplace/pub-1/install")

            mock_client.marketplace.uninstall("inst-1")
            kw = _kw(mock_req)
            assert kw["method"] == "DELETE"
            assert kw["url"].endswith("/v2/marketplace/installations/inst-1")


class TestVoiceCalls:
    def test_paths(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory([])) as mock_req:
            mock_client.voice_calls.list(status="completed")
            kw = _kw(mock_req)
            assert kw["url"].endswith("/v2/voice/calls")
            assert kw["params"]["status"] == "completed"

            mock_client.voice_calls.transcript("CA-1")
            assert _kw(mock_req)["url"].endswith("/v2/voice/calls/CA-1/transcript")

            mock_client.voice_calls.calls_for_chatflow("flow-1")
            assert _kw(mock_req)["url"].endswith("/v2/chatflows/flow-1/calls")


class TestAudit:
    def test_list_export(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory({})) as mock_req:
            mock_client.audit.list_events(actor_id="u-1", action="agent.update", from_="2026-01-01", to="2026-02-01")
            kw = _kw(mock_req)
            assert kw["url"].endswith("/v2/audit/events")
            assert kw["params"]["actorId"] == "u-1"
            assert kw["params"]["from"] == "2026-01-01"

            mock_client.audit.resource_events("agent", "a-1")
            assert _kw(mock_req)["url"].endswith("/v2/audit/events/agent/a-1")

            mock_client.audit.export(format="csv")
            kw = _kw(mock_req)
            assert kw["url"].endswith("/v2/audit/export")
            assert kw["params"]["format"] == "csv"


class TestCostControl:
    def test_routing_rules_and_caps(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory({})) as mock_req:
            mock_client.cost_control.list_routing_rules()
            assert _kw(mock_req)["url"].endswith("/v2/cost-control/routing-rules")

            mock_client.cost_control.create_routing_rule({"name": "r1"})
            assert _kw(mock_req)["json"] == {"name": "r1"}

            mock_client.cost_control.toggle_routing_rule("r-1", enabled=False)
            kw = _kw(mock_req)
            assert kw["url"].endswith("/v2/cost-control/routing-rules/r-1/toggle")
            assert kw["json"] == {"enabled": False}

            mock_client.cost_control.set_workspace_cap({"period": "MONTH", "limit": 1000})
            assert _kw(mock_req)["url"].endswith("/v2/cost-control/usage-caps/workspace")

            mock_client.cost_control.set_model_cap("openai:gpt-4", {"period": "DAY", "limit": 50})
            assert _kw(mock_req)["url"].endswith("/v2/cost-control/usage-caps/model/openai:gpt-4")

            mock_client.cost_control.scaling("deploy-1")
            assert _kw(mock_req)["url"].endswith("/v2/cost-control/scaling/deploy-1")


class TestAgentWizard:
    def test_generate_review_create(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory({"id": "draft-1"})) as mock_req:
            mock_client.agent_wizard.generate(prompt="An SDR", agent_type="conversational", provider="OPENAI")
            kw = _kw(mock_req)
            assert kw["url"].endswith("/v2/agents/wizard/generate")
            assert kw["json"]["prompt"] == "An SDR"
            assert kw["json"]["agentType"] == "conversational"

            mock_client.agent_wizard.review({"id": "d"})
            assert _kw(mock_req)["url"].endswith("/v2/agents/wizard/review")

            mock_client.agent_wizard.refine({"id": "d"}, feedback="be brief")
            assert _kw(mock_req)["json"]["feedback"] == "be brief"

            mock_client.agent_wizard.link_tools("a-1", ["t-1", "t-2"])
            kw = _kw(mock_req)
            assert kw["json"] == {"agentId": "a-1", "toolIds": ["t-1", "t-2"]}

            mock_client.agent_wizard.from_template("support-triage", {"name": "Tier 1"})
            assert _kw(mock_req)["url"].endswith("/v2/agents/wizard/from-template/support-triage")


class TestClientPropertiesExposed:
    def test_all_v2_props_present(self, mock_client):
        for name in (
            "chatflows",
            "datasets",
            "documents",
            "files",
            "rag",
            "mcp",
            "modules",
            "marketplace",
            "voice_calls",
            "audit",
            "cost_control",
            "agent_wizard",
        ):
            assert hasattr(mock_client, name), f"client missing .{name}"
            obj = getattr(mock_client, name)
            assert obj is not None
