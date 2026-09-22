"""
agents.chat, workflows.invoke / get_execution_status / invoke_and_wait, catalog.*

Mocks ``requests.request`` and asserts the exact method, URL (agents-service
root, not the gateway), body and query of every call, plus error mapping and
polling termination.
"""

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from swfte import SwfteClient
from swfte.exceptions import (
    APIError,
    AuthenticationError,
    InvalidRequestError,
    RateLimitError,
    WorkflowExecutionError,
    WorkflowTimeoutError,
)
from swfte.workflows import classify_execution_status

API = "https://api.swfte.com/agents"


def resp(body=None, status=200):
    r = MagicMock()
    r.status_code = status
    r.text = json.dumps(body) if body is not None else ""
    r.json.return_value = body
    return r


def status_body(status, **extra):
    return {
        "execution": {"executionId": "ex_1", "workflowId": "wf_1", "status": status, **extra},
        "nodeExecutions": [],
        "progress": 50 if status == "RUNNING" else 100,
    }


def kw(mock_req, idx=-1):
    return mock_req.call_args_list[idx][1]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("SWFTE_API_BASE_URL", raising=False)
    return SwfteClient(api_key="pat_abc", workspace_id="ws_9")


class TestBaseUrl:
    def test_derived_from_default_gateway(self, client):
        assert client.base_url == "https://api.swfte.com/agents/v2/gateway"
        assert client.api_base_url == API

    def test_strips_v1_gateway(self, monkeypatch):
        monkeypatch.delenv("SWFTE_API_BASE_URL", raising=False)
        c = SwfteClient(api_key="k", base_url="http://localhost:8080/v1/gateway/")
        assert c.api_base_url == "http://localhost:8080"

    def test_explicit_wins(self, monkeypatch):
        monkeypatch.setenv("SWFTE_API_BASE_URL", "https://env.test/agents")
        c = SwfteClient(api_key="k", api_base_url="http://local:1/")
        assert c.api_base_url == "http://local:1"

    def test_env(self, monkeypatch):
        monkeypatch.setenv("SWFTE_API_BASE_URL", "https://env.test/agents/")
        assert SwfteClient(api_key="k").api_base_url == "https://env.test/agents"

    def test_existing_resources_follow_api_base_url(self, monkeypatch):
        monkeypatch.delenv("SWFTE_API_BASE_URL", raising=False)
        c = SwfteClient(api_key="k", api_base_url="http://local:1")
        with patch("requests.request", return_value=MagicMock(content=b"")) as m:
            m.return_value.raise_for_status.return_value = None
            c.workflows.delete("wf_1")
        assert kw(m)["url"] == "http://local:1/v2/workflows/wf_1"


class TestAgentChat:
    def test_posts_message_to_chat_path(self, client):
        with patch("requests.request", return_value=resp({"response": "Hi", "conversationId": "c1"})) as m:
            reply = client.agents.chat("ag_1", "Hello", user_id="user-42")
        k = kw(m)
        assert m.call_count == 1
        assert k["method"] == "POST"
        assert k["url"] == f"{API}/v1/agents/ag_1/chat/user-42"
        assert k["json"] == {"message": "Hello"}
        assert k["params"] is None
        assert k["headers"]["Authorization"] == "Bearer pat_abc"
        assert k["headers"]["X-Workspace-ID"] == "ws_9"
        assert reply.response == "Hi"
        assert reply.conversation_id == "c1"

    def test_default_user_and_conversation_id(self, client):
        with patch("requests.request", return_value=resp({"response": "again"})) as m:
            client.agents.chat("ag_1", "More", conversation_id="c1")
        assert kw(m)["url"] == f"{API}/v1/agents/ag_1/chat/sdk-user"
        assert kw(m)["json"] == {"message": "More", "conversationId": "c1"}

    def test_content_normalised_to_response(self, client):
        with patch("requests.request", return_value=resp({"content": "from content", "model": "m"})):
            reply = client.agents.chat("ag_1", "x")
        assert reply.response == "from content"
        assert reply.model == "m"
        assert reply.raw["content"] == "from content"

    def test_path_segments_encoded(self, client):
        with patch("requests.request", return_value=resp({"response": "ok"})) as m:
            client.agents.chat("ag/1", "x", user_id="a b@c")
        assert kw(m)["url"] == f"{API}/v1/agents/ag%2F1/chat/a%20b%40c"

    def test_error_mapping_and_no_retry(self, client):
        with patch("requests.request", return_value=resp({"error": "AGENT_EXECUTION_FAILED"}, 503)) as m:
            with pytest.raises(APIError) as ei:
                client.agents.chat("ag_1", "x")
        assert m.call_count == 1
        assert ei.value.status_code == 503
        assert ei.value.body == {"error": "AGENT_EXECUTION_FAILED"}
        with patch("requests.request", return_value=resp({}, 401)):
            with pytest.raises(AuthenticationError):
                client.agents.chat("ag_1", "x")
        with patch("requests.request", return_value=resp({}, 429)):
            with pytest.raises(RateLimitError):
                client.agents.chat("ag_1", "x")

    def test_empty_message_rejected_locally(self, client):
        with patch("requests.request") as m:
            with pytest.raises(InvalidRequestError):
                client.agents.chat("ag_1", "")
        m.assert_not_called()


class TestWorkflowInvoke:
    def test_invoke_posts_inputs(self, client):
        with patch("requests.request", return_value=resp({"executionId": "ex_1", "status": "PENDING"}, 202)) as m:
            inv = client.workflows.invoke("wf_1", {"topic": "x", "n": 2})
        k = kw(m)
        assert k["method"] == "POST"
        assert k["url"] == f"{API}/v2/workflows/wf_1/invoke"
        assert k["json"] == {"topic": "x", "n": 2}
        assert inv.execution_id == "ex_1"
        assert inv.status == "PENDING"

    def test_invoke_defaults_to_empty_body(self, client):
        with patch("requests.request", return_value=resp({"executionId": "ex_1"}, 202)) as m:
            client.workflows.invoke("wf_1")
        assert kw(m)["json"] == {}

    def test_invoke_409_not_retried(self, client):
        with patch("requests.request", return_value=resp({"error": "PUBLISHED_SNAPSHOT_UNAVAILABLE"}, 409)) as m:
            with pytest.raises(APIError) as ei:
                client.workflows.invoke("wf_1", {})
        assert ei.value.status_code == 409
        assert m.call_count == 1

    def test_invoke_without_execution_id(self, client):
        with patch("requests.request", return_value=resp({"status": "PENDING"}, 202)):
            with pytest.raises(APIError):
                client.workflows.invoke("wf_1")

    def test_get_execution_status_lifts_nested_record(self, client):
        body = status_body("success", outputData={"answer": 42})
        with patch("requests.request", return_value=resp(body)) as m:
            st = client.workflows.get_execution_status("ex_1")
        k = kw(m)
        assert k["method"] == "GET"
        assert k["url"] == f"{API}/v2/workflows/executions/ex_1/status"
        assert k["json"] is None
        assert st.status_raw == "SUCCESS"
        assert st.succeeded and st.is_terminal
        assert st.id == "ex_1"
        assert st.workflow_id == "wf_1"
        assert st.outputs == {"answer": 42}
        assert st.progress == 100

    def test_classify(self):
        for s in ("SUCCESS", "SUCCEEDED", "COMPLETED", "succeeded"):
            assert classify_execution_status(s) == "succeeded"
        for s in ("FAILED", "TIMEOUT", "ERROR"):
            assert classify_execution_status(s) == "failed"
        for s in ("CANCELLED", "CANCELED"):
            assert classify_execution_status(s) == "cancelled"
        for s in ("PENDING", "RUNNING", "PAUSED", "", None):
            assert classify_execution_status(s) == "running"

    def test_invoke_and_wait_until_succeeded(self, client):
        responses = [
            resp({"executionId": "ex_1"}, 202),
            resp(status_body("PENDING")),
            resp(status_body("RUNNING")),
            resp(status_body("SUCCEEDED", outputData={"ok": True})),
        ]
        with patch("requests.request", side_effect=responses) as m:
            done = client.workflows.invoke_and_wait("wf_1", {"a": 1}, timeout=5, poll_interval=0.001)
        assert done.status_raw == "SUCCEEDED"
        assert done.outputs == {"ok": True}
        assert m.call_count == 4
        assert kw(m, 0)["url"] == f"{API}/v2/workflows/wf_1/invoke"
        assert kw(m, 0)["json"] == {"a": 1}
        for i in (1, 2, 3):
            assert kw(m, i)["method"] == "GET"
            assert kw(m, i)["url"] == f"{API}/v2/workflows/executions/ex_1/status"

    def test_invoke_and_wait_failed(self, client):
        responses = [
            resp({"executionId": "ex_1"}, 202),
            resp(status_body("FAILED", errorInfo={"message": "node llm_1 exploded"})),
        ]
        with patch("requests.request", side_effect=responses) as m:
            with pytest.raises(WorkflowExecutionError) as ei:
                client.workflows.invoke_and_wait("wf_1", poll_interval=0.001)
        assert ei.value.status == "FAILED"
        assert ei.value.execution_id == "ex_1"
        assert "node llm_1 exploded" in str(ei.value)
        assert isinstance(ei.value, RuntimeError)
        assert m.call_count == 2

    def test_invoke_and_wait_canceled(self, client):
        responses = [resp({"executionId": "ex_1"}, 202), resp(status_body("CANCELED"))]
        with patch("requests.request", side_effect=responses):
            with pytest.raises(WorkflowExecutionError) as ei:
                client.workflows.invoke_and_wait("wf_1", poll_interval=0.001)
        assert ei.value.status == "CANCELED"

    def test_invoke_and_wait_times_out(self, client):
        def fake(**kwargs):
            if kwargs["url"].endswith("/invoke"):
                return resp({"executionId": "ex_1"}, 202)
            return resp(status_body("RUNNING"))

        started = time.monotonic()
        with patch("requests.request", side_effect=fake) as m:
            with pytest.raises(WorkflowTimeoutError) as ei:
                client.workflows.invoke_and_wait("wf_1", timeout=0.06, poll_interval=0.01)
        assert time.monotonic() - started < 2
        assert ei.value.execution_id == "ex_1"
        assert isinstance(ei.value, TimeoutError)
        assert 2 <= m.call_count < 20

    def test_timeout_zero_still_polls_once(self, client):
        responses = [resp({"executionId": "ex_1"}, 202), resp(status_body("SUCCESS"))]
        with patch("requests.request", side_effect=responses):
            done = client.workflows.invoke_and_wait("wf_1", timeout=0)
        assert done.succeeded

    def test_status_error_propagates(self, client):
        responses = [resp({"executionId": "ex_1"}, 202), resp({"error": "nope"}, 404)]
        with patch("requests.request", side_effect=responses):
            with pytest.raises(APIError) as ei:
                client.workflows.invoke_and_wait("wf_1", poll_interval=0.001)
        assert ei.value.status_code == 404

    def test_wait_for_completion_accepts_success(self, client):
        with patch("requests.request", return_value=resp(status_body("SUCCESS"))):
            done = client.workflows.wait_for_completion("ex_1", timeout=1, poll_interval=0)
        assert done.succeeded

    def test_execute_still_uses_draft_path(self, client):
        r = MagicMock(content=b'{"executionId": "ex_2"}')
        r.json.return_value = {"executionId": "ex_2"}
        with patch("requests.request", return_value=r) as m:
            client.workflows.execute("wf_1", {"a": 1})
        assert kw(m)["url"] == f"{API}/v2/workflows/wf_1/execute"


class TestCatalog:
    def test_search_query(self, client):
        body = {"items": [{"catalogRef": "workflow:wf_1"}], "nextCursor": "c2", "degraded": ["jev_rerank"]}
        with patch("requests.request", return_value=resp(body)) as m:
            res = client.catalog.search(
                q="invoice triage",
                kinds=["workflow", "agent"],
                scope="all",
                min_evidence="corroborated",
                limit=5,
            )
        k = kw(m)
        assert k["method"] == "GET"
        assert k["url"] == f"{API}/v2/catalog/search"
        assert k["json"] is None
        assert k["params"] == {
            "q": "invoice triage",
            "kinds": "workflow,agent",
            "scope": "all",
            "minEvidence": "corroborated",
            "limit": 5,
        }
        assert res == body

    def test_search_defaults(self, client):
        with patch("requests.request", return_value=resp({})) as m:
            res = client.catalog.search()
        assert kw(m)["params"] is None
        assert res == {"items": [], "nextCursor": None, "degraded": []}

    def test_get_and_contract(self, client):
        with patch("requests.request", return_value=resp({"catalogRef": "mcp-server:m 1"})) as m:
            client.catalog.get("mcp-server", "m 1")
            assert kw(m)["url"] == f"{API}/v2/catalog/mcp-server/m%201"
            assert kw(m)["method"] == "GET"
            client.catalog.contract("workflow", "wf_1")
            assert kw(m)["url"] == f"{API}/v2/catalog/workflow/wf_1/contract"
            assert kw(m)["headers"]["X-Workspace-ID"] == "ws_9"

    def test_not_found(self, client):
        with patch("requests.request", return_value=resp({"error": "not found"}, 404)):
            with pytest.raises(APIError) as ei:
                client.catalog.get("workflow", "nope")
        assert ei.value.status_code == 404
