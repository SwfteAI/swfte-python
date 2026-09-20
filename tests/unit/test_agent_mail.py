"""
Unit tests for the Agent Mail V2 resource client.

We mock ``requests.request`` and assert URL, method, params, headers and the
JSON body. The interesting cases are the ones that are easy to regress:
opaque cursor paging (not page/size), an explicit ``None`` agentId meaning
"unbind", the locally-validated Idempotency-Key, and the no-retry guarantee
on send.
"""

import pytest
from unittest.mock import patch

from swfte.agent_mail import IDEMPOTENCY_KEY_PATTERN
from swfte.exceptions import InvalidRequestError


def _kw(mock_req, idx=-1):
    return mock_req.call_args_list[idx][1]


class TestAgentMailStatusAndMailboxes:
    def test_status(self, mock_client, response_factory):
        with patch(
            "requests.request", return_value=response_factory({"enabled": True})
        ) as mock_req:
            result = mock_client.agent_mail.status()
            kw = _kw(mock_req)
            assert result["enabled"] is True
            assert kw["method"] == "GET"
            assert kw["url"].endswith("/v2/workspace-mail/status")

    def test_mailboxes_uses_opaque_cursor_paging(self, mock_client, response_factory):
        with patch(
            "requests.request",
            return_value=response_factory({"items": [], "nextCursor": "c2"}),
        ) as mock_req:
            page = mock_client.agent_mail.mailboxes(limit=25, cursor="c1")
            kw = _kw(mock_req)
            assert page["nextCursor"] == "c2"
            assert kw["method"] == "GET"
            assert kw["url"].endswith("/v2/workspace-mail/mailboxes")
            assert kw["params"] == {"limit": 25, "cursor": "c1"}
            assert "page" not in kw["params"]
            assert "size" not in kw["params"]

    def test_mailboxes_filters_by_agent(self, mock_client, response_factory):
        with patch(
            "requests.request", return_value=response_factory({"items": []})
        ) as mock_req:
            mock_client.agent_mail.mailboxes(agent_id="agent-123")
            assert _kw(mock_req)["params"] == {"agentId": "agent-123"}

    def test_get(self, mock_client, response_factory):
        with patch(
            "requests.request", return_value=response_factory({"id": "mb-1"})
        ) as mock_req:
            mock_client.agent_mail.get("mb-1")
            kw = _kw(mock_req)
            assert kw["method"] == "GET"
            assert kw["url"].endswith("/v2/workspace-mail/mailboxes/mb-1")

    def test_create(self, mock_client, response_factory):
        with patch(
            "requests.request",
            return_value=response_factory({"id": "mb-1", "deactivatedAt": None}),
        ) as mock_req:
            mock_client.agent_mail.create(
                name="Support", local_part="support", agent_id="agent-123"
            )
            kw = _kw(mock_req)
            assert kw["method"] == "POST"
            assert kw["url"].endswith("/v2/workspace-mail/mailboxes")
            assert kw["json"] == {
                "name": "Support",
                "localPart": "support",
                "agentId": "agent-123",
            }


class TestAgentMailUpdate:
    def test_omitted_fields_are_not_sent(self, mock_client, response_factory):
        with patch(
            "requests.request", return_value=response_factory({"id": "mb-1"})
        ) as mock_req:
            mock_client.agent_mail.update("mb-1", name="Renamed")
            kw = _kw(mock_req)
            assert kw["method"] == "PATCH"
            assert kw["url"].endswith("/v2/workspace-mail/mailboxes/mb-1")
            assert kw["json"] == {"name": "Renamed"}

    def test_explicit_none_clears_the_agent_binding(self, mock_client, response_factory):
        with patch(
            "requests.request",
            return_value=response_factory({"id": "mb-1", "agentId": None}),
        ) as mock_req:
            mock_client.agent_mail.update("mb-1", agent_id=None)
            assert _kw(mock_req)["json"] == {"agentId": None}


class TestAgentMailRemove:
    def test_remove_deactivates(self, mock_client, response_factory):
        with patch(
            "requests.request",
            return_value=response_factory(
                {"id": "mb-1", "deactivatedAt": "2026-09-20T10:00:00Z"}
            ),
        ) as mock_req:
            mailbox = mock_client.agent_mail.remove("mb-1")
            kw = _kw(mock_req)
            assert kw["method"] == "DELETE"
            assert kw["url"].endswith("/v2/workspace-mail/mailboxes/mb-1")
            assert mailbox["deactivatedAt"] == "2026-09-20T10:00:00Z"


class TestAgentMailMessages:
    def test_messages_paging(self, mock_client, response_factory):
        with patch(
            "requests.request",
            return_value=response_factory({"items": [], "nextCursor": None}),
        ) as mock_req:
            mock_client.agent_mail.messages("mb-1", limit=10, cursor="m1")
            kw = _kw(mock_req)
            assert kw["method"] == "GET"
            assert kw["url"].endswith("/v2/workspace-mail/mailboxes/mb-1/messages")
            assert kw["params"] == {"limit": 10, "cursor": "m1"}


class TestAgentMailSend:
    def test_send_posts_body_and_idempotency_header(self, mock_client, response_factory):
        with patch(
            "requests.request",
            return_value=response_factory({"id": "msg-1", "status": "accepted"}),
        ) as mock_req:
            message = mock_client.agent_mail.send(
                "mb-1",
                to="ada@example.com",
                subject="Hello",
                text="Body",
                idempotency_key="send-key-0001",
            )
            kw = _kw(mock_req)
            assert kw["method"] == "POST"
            assert kw["url"].endswith("/v2/workspace-mail/mailboxes/mb-1/messages")
            assert kw["json"] == {
                "to": "ada@example.com",
                "subject": "Hello",
                "text": "Body",
            }
            assert kw["headers"]["Idempotency-Key"] == "send-key-0001"
            # "accepted" means the provider took the request, not that it was delivered.
            assert message["status"] == "accepted"

    @pytest.mark.parametrize(
        "bad_key",
        ["short", "", "has spaces here", "a" * 129, "bad/slash!key", None, 12345],
    )
    def test_send_rejects_bad_key_locally_without_any_network_call(
        self, mock_client, response_factory, bad_key
    ):
        with patch(
            "requests.request", return_value=response_factory({})
        ) as mock_req:
            with pytest.raises(InvalidRequestError, match="Idempotency-Key"):
                mock_client.agent_mail.send(
                    "mb-1",
                    to="a@b.com",
                    subject="s",
                    text="t",
                    idempotency_key=bad_key,
                )
            assert mock_req.call_count == 0

    def test_send_issues_exactly_one_request_and_never_retries(
        self, mock_client, response_factory
    ):
        failing = response_factory({"error": "boom"}, 503)
        with patch("requests.request", return_value=failing) as mock_req:
            with pytest.raises(Exception):
                mock_client.agent_mail.send(
                    "mb-1",
                    to="a@b.com",
                    subject="s",
                    text="t",
                    idempotency_key="send-key-0002",
                )
            assert mock_req.call_count == 1

    def test_idempotency_pattern_accepts_the_documented_alphabet(self):
        assert IDEMPOTENCY_KEY_PATTERN.match("abcDEF01")
        assert IDEMPOTENCY_KEY_PATTERN.match("a._:-Z999")
        assert IDEMPOTENCY_KEY_PATTERN.match("x" * 128)
        assert not IDEMPOTENCY_KEY_PATTERN.match("x" * 129)
        assert not IDEMPOTENCY_KEY_PATTERN.match("seven77")
