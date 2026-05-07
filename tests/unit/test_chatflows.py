"""Unit tests for ChatFlows V2 resource."""

from unittest.mock import patch


def _last_call(mock_req):
    return mock_req.call_args[1]


class TestChatFlows:
    def test_create(self, mock_client, response_factory):
        mock_response = response_factory({"id": "flow-1", "name": "Lead Q"})
        with patch("requests.request", return_value=mock_response) as mock_req:
            result = mock_client.chatflows.create({"name": "Lead Q", "fields": []})

            assert result["id"] == "flow-1"
            kw = _last_call(mock_req)
            assert kw["method"] == "POST"
            assert kw["url"].endswith("/v2/chatflows")
            assert kw["headers"]["Authorization"].startswith("Bearer ")
            assert kw["headers"]["X-Workspace-ID"] == "ws-test-12345"
            assert kw["json"] == {"name": "Lead Q", "fields": []}

    def test_get(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory({"id": "flow-1"})) as mock_req:
            mock_client.chatflows.get("flow-1")
            kw = _last_call(mock_req)
            assert kw["method"] == "GET"
            assert kw["url"].endswith("/v2/chatflows/flow-1")

    def test_validate_deploy_session(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory({"ok": True})) as mock_req:
            mock_client.chatflows.validate("flow-1")
            assert _last_call(mock_req)["url"].endswith("/v2/chatflows/flow-1/validate")
            mock_client.chatflows.deploy("flow-1", channel="WEB")
            assert _last_call(mock_req)["url"].endswith("/v2/chatflows/flow-1/deploy")
            assert _last_call(mock_req)["json"] == {"channel": "WEB"}
            mock_client.chatflows.start_session("flow-1", channel="WEB")
            assert _last_call(mock_req)["url"].endswith("/v2/chatflows/flow-1/sessions")

    def test_versions(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory([{"version": "v1"}])) as mock_req:
            mock_client.chatflows.list_versions("flow-1")
            assert _last_call(mock_req)["url"].endswith("/v2/chatflows/flow-1/versions")
            mock_client.chatflows.create_version("flow-1", notes="first")
            assert _last_call(mock_req)["json"] == {"notes": "first"}

    def test_publish(self, mock_client, response_factory):
        with patch("requests.request", return_value=response_factory({"published": True})) as mock_req:
            mock_client.chatflows.publish("flow-1", {"slug": "lead-q"})
            assert _last_call(mock_req)["url"].endswith("/v2/chatflows/flow-1/publish")
            assert _last_call(mock_req)["json"] == {"slug": "lead-q"}
