"""Pre-publish (1.2.0) behaviour tests. Each one fails on origin/main 5272646."""

import json
import threading
import time
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import requests

from swfte import SwfteClient
from swfte.agents import AgentChatResponse
from swfte.exceptions import APIError, AuthenticationError, InvalidRequestError, RateLimitError


class _Server:
    """Local HTTP server that records every request and answers from a script."""

    def __init__(self, status=200, body=None, delay=0.0):
        self.hits = []
        outer = self

        class H(BaseHTTPRequestHandler):
            def _do(self):
                length = int(self.headers.get("Content-Length") or 0)
                if length:
                    self.rfile.read(length)
                outer.hits.append((self.command, self.path))
                if delay:
                    time.sleep(delay)
                data = json.dumps(body if body is not None else {"error": "x"}).encode()
                try:
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            do_GET = do_POST = do_PUT = do_DELETE = _do

            def log_message(self, *a):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def server():
    made = []

    def make(**kw):
        s = _Server(**kw)
        made.append(s)
        return s

    yield make
    for s in made:
        s.close()


class TestAgentReplyParsingOrder:
    def test_content_wins_over_response(self):
        assert AgentChatResponse.from_dict({"content": "a", "response": "b"}).response == "a"

    def test_response_is_fallback_when_content_absent(self):
        assert AgentChatResponse.from_dict({"response": "b"}).response == "b"

    def test_empty_string_content_is_not_overridden(self):
        assert AgentChatResponse.from_dict({"content": "", "response": "b"}).response == ""

    def test_neither_gives_empty(self):
        assert AgentChatResponse.from_dict({}).response == ""


class TestChatCompletionsRetry:
    def test_read_timeout_is_not_retried(self, server):
        """A slow POST must hit the server once: retrying could bill it 3x."""
        s = server(status=200, body={}, delay=1.5)
        client = SwfteClient(api_key="k", base_url=s.url, timeout=0.3, max_retries=3)
        with pytest.raises(APIError):
            client.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
        assert len(s.hits) == 1

    def test_max_retries_zero_never_returns_none(self, server):
        s = server(status=500, body={"error": "boom"})
        client = SwfteClient(api_key="k", base_url=s.url, max_retries=0)
        with pytest.raises(APIError):
            client.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
        assert len(s.hits) == 1

    def test_403_is_authentication_error_after_one_request(self, server):
        s = server(status=403)
        client = SwfteClient(api_key="k", base_url=s.url, max_retries=3)
        with pytest.raises(AuthenticationError):
            client.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
        assert len(s.hits) == 1

    def test_connection_refused_raises_without_a_generic_connection_retry(self):
        # A generic ConnectionError cannot distinguish refusal from a failure
        # after the server accepted the body, so only ConnectTimeout is retried.
        client = SwfteClient(api_key="k", base_url="http://127.0.0.1:1", max_retries=2, timeout=1)
        with pytest.raises(APIError):
            client.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])


class TestV2ResourceTypedErrors:
    def test_403_from_v2_resource_is_authentication_error(self, server):
        s = server(status=403)
        client = SwfteClient(api_key="k", base_url=s.url + "/v2/gateway", api_base_url=s.url)
        with pytest.raises(AuthenticationError):
            client.agents.list()
        assert len(s.hits) == 1

    def test_401_from_v2_resource_is_authentication_error(self, server):
        s = server(status=401)
        client = SwfteClient(api_key="k", base_url=s.url + "/v2/gateway", api_base_url=s.url)
        with pytest.raises(AuthenticationError):
            client.datasets.list()

    def test_429_from_v2_resource_is_rate_limit_error(self, server):
        s = server(status=429)
        client = SwfteClient(api_key="k", base_url=s.url + "/v2/gateway", api_base_url=s.url)
        with pytest.raises(RateLimitError):
            client.agents.list()

    def test_404_is_still_http_error(self, server):
        s = server(status=404)
        client = SwfteClient(api_key="k", base_url=s.url + "/v2/gateway", api_base_url=s.url)
        with pytest.raises(requests.HTTPError):
            client.agents.get("nope")


class TestCleartextBaseUrlRejected:
    """Same rule as swfte-node assertSecureUrl: https anywhere, http only for loopback."""

    def test_http_non_loopback_base_url_raises(self, monkeypatch):
        monkeypatch.delenv("SWFTE_API_BASE_URL", raising=False)
        with pytest.raises(InvalidRequestError, match="base_url must use https"):
            SwfteClient(api_key="k", base_url="http://api.example.test/agents/v2/gateway")

    def test_http_non_loopback_api_base_url_raises(self, monkeypatch):
        monkeypatch.delenv("SWFTE_API_BASE_URL", raising=False)
        with pytest.raises(InvalidRequestError, match="api_base_url must use https"):
            SwfteClient(api_key="k", api_base_url="http://api.example.test/agents")

    def test_http_non_loopback_env_api_base_url_raises(self, monkeypatch):
        monkeypatch.setenv("SWFTE_API_BASE_URL", "http://api.example.test/agents")
        with pytest.raises(InvalidRequestError, match="api_base_url must use https"):
            SwfteClient(api_key="k")

    def test_lookalike_hosts_and_other_schemes_raise(self, monkeypatch):
        monkeypatch.delenv("SWFTE_API_BASE_URL", raising=False)
        for url in (
            "http://localhost.evil.test/v2/gateway",
            "http://127.0.0.1.evil.test",
            "http://notlocalhost:8080",
            "ftp://example.test",
            "ws://localhost:8080",
        ):
            with pytest.raises(InvalidRequestError, match="must use https"):
                SwfteClient(api_key="k", base_url=url)

    def test_unparseable_url_raises(self, monkeypatch):
        monkeypatch.delenv("SWFTE_API_BASE_URL", raising=False)
        for url in ("not url", "api.example.test/v2/gateway", ""):
            with pytest.raises(InvalidRequestError, match="base_url is not a valid URL"):
                SwfteClient(api_key="k", base_url=url)

    def test_message_names_scheme_and_host_only(self, monkeypatch):
        monkeypatch.delenv("SWFTE_API_BASE_URL", raising=False)
        with pytest.raises(InvalidRequestError) as raised:
            SwfteClient(
                api_key="sk-swfte-cleartext-key",
                base_url="http://user:hunter2@api.example.test:8080/v2/gateway?token=abc",
            )
        message = str(raised.value)
        assert "http://api.example.test:8080" in message
        for secret in ("hunter2", "user", "token", "abc", "sk-swfte-cleartext-key", "/v2/gateway"):
            assert secret not in message

    def test_https_and_loopback_http_construct_without_warning(self, monkeypatch):
        monkeypatch.delenv("SWFTE_API_BASE_URL", raising=False)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            SwfteClient(api_key="k")
            SwfteClient(api_key="k", base_url="https://api.example.test/agents/v2/gateway")
            for host in ("localhost", "127.0.0.1", "[::1]", "LOCALHOST"):
                client = SwfteClient(api_key="k", base_url=f"http://{host}:8080/agents/v2/gateway")
                assert client.api_base_url == f"http://{host}:8080/agents"
            SwfteClient(api_key="k", api_base_url="http://localhost:8080")


class TestUserAgentVersion:
    def test_user_agent_matches_package_version(self):
        import swfte

        ua = SwfteClient(api_key="k")._get_headers()["User-Agent"]
        assert ua == f"swfte-python/{swfte.__version__}"
