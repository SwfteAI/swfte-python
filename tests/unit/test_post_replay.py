"""Real loopback evidence for POST replay, success and redirect boundaries."""

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import requests

from swfte import SwfteClient
from swfte.exceptions import APIError


CASES = ["chat", "stream", "transcription", "speech", "file", "workflow", "workflow_execute",
         "image", "image_edit", "embedding"]
AUDIO = b"\x00\xff\x10audio"
MESSAGE = "hello caf\u00e9"


class Server:
    def __init__(self, body=None, disconnect=False, status=200, location=None):
        self.hits = []
        self.lock = threading.Lock()
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def handle_request(self):
                length = int(self.headers.get("Content-Length") or 0)
                data = self.rfile.read(length)
                with outer.lock:
                    outer.hits.append((self.command, self.path, dict(self.headers), data))
                if disconnect:
                    # The whole body was accepted, so execution could have happened.
                    self.close_connection = True
                    try:
                        self.connection.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    return
                payload = body if isinstance(body, bytes) else json.dumps(body or {}).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json" if not isinstance(body, bytes) else "application/octet-stream")
                self.send_header("Content-Length", str(len(payload)))
                if location is not None:
                    self.send_header("Location", location)
                self.end_headers()
                self.wfile.write(payload)

            do_GET = do_POST = handle_request

            def log_message(self, *args):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = "http://127.0.0.1:{}".format(self.httpd.server_port)
        self.thread = threading.Thread(target=lambda: self.httpd.serve_forever(poll_interval=0.01), daemon=True)
        self.thread.start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)
        assert not self.thread.is_alive(), "loopback server did not stop"


@pytest.fixture
def servers(monkeypatch):
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    made = []

    def make(**kwargs):
        server = Server(**kwargs)
        made.append(server)
        return server

    yield make
    for server in reversed(made):
        server.close()


def client(server, max_retries=3):
    return SwfteClient(api_key="post-replay-test-key", base_url=server.url,
                       api_base_url=server.url, workspace_id="ws-post", timeout=2,
                       max_retries=max_retries)


def invoke(case, sdk):
    if case == "chat":
        return sdk.chat.completions.create(model="m", messages=[{"role": "user", "content": MESSAGE}])
    if case == "stream":
        return list(sdk.chat.completions.create(model="m", messages=[{"role": "user", "content": MESSAGE}], stream=True))
    if case == "transcription":
        return sdk.audio.transcriptions.create(model="m", file=AUDIO)
    if case == "speech":
        return sdk.audio.speech.create(model="m", input=MESSAGE)
    if case == "file":
        return sdk.files.upload(("fixture.bin", AUDIO, "application/octet-stream"))
    if case == "workflow":
        return sdk.workflows.invoke("wf-post", {"input": MESSAGE})
    if case == "workflow_execute":
        return sdk.workflows.execute("wf-post", {"input": MESSAGE})
    if case == "image":
        return sdk.images.generate(model="m", prompt=MESSAGE)
    if case == "image_edit":
        return sdk.images.edit(model="m", image=AUDIO, mask=AUDIO, prompt=MESSAGE)
    if case == "embedding":
        return sdk.embeddings.create(model="m", input=MESSAGE)
    raise AssertionError("unknown fixture case")


def success_body(case):
    if case == "chat":
        return {"id": "chat-1", "model": "m", "choices": [
            {"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}]}
    if case == "stream":
        chunk = {"id": "stream-1", "model": "m", "choices": [
            {"index": 0, "delta": {"content": "ok"}}]}
        return ("data:" + json.dumps(chunk) + "\n\ndata: [DONE]\n\n").encode()
    if case == "speech":
        return AUDIO
    if case == "transcription":
        return {"text": "ok"}
    if case == "file":
        return {"id": "file-1"}
    if case in ("image", "image_edit"):
        return {"created": 1, "data": [{"url": "https://fixture.invalid/image"}]}
    if case == "embedding":
        return {"model": "m", "data": [{"index": 0, "embedding": [0.5, -0.2]}]}
    return {"executionId": "ex-1", "status": "PENDING"}


def assert_consumed_post(server, case):
    assert len(server.hits) == 1, "a consumed POST was replayed"
    method, path, headers, body = server.hits[0]
    assert method == "POST"
    assert headers["Authorization"] == "Bearer post-replay-test-key"
    assert next(v for k, v in headers.items() if k.lower() == "x-workspace-id") == "ws-post"
    assert int(headers["Content-Length"]) == len(body) > 0
    if case in ("transcription", "file", "image_edit"):
        assert "multipart/form-data; boundary=" in headers["Content-Type"]
        assert AUDIO in body
        if case == "image_edit":
            assert MESSAGE.encode() in body
            assert b'name="image"' in body and b'name="mask"' in body
    else:
        payload = json.loads(body)
        assert payload, "the server did not receive the actual JSON request"
        if case in ("chat", "stream"):
            assert payload["messages"][0]["content"] == MESSAGE
        elif case in ("speech", "embedding"):
            assert payload["input"] == MESSAGE
        elif case == "image":
            assert payload["prompt"] == MESSAGE
        else:
            assert payload == {"input": MESSAGE}
    assert path


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("max_retries", [0, 3])
def test_public_post_never_replays_after_server_consumes_body(servers, case, max_retries):
    server = servers(disconnect=True)
    with pytest.raises((APIError, requests.exceptions.ConnectionError)):
        invoke(case, client(server, max_retries))
    assert_consumed_post(server, case)


@pytest.mark.parametrize("case", CASES)
def test_public_post_normal_response_still_works(servers, case):
    server = servers(body=success_body(case))
    result = invoke(case, client(server))
    assert_consumed_post(server, case)
    if case == "chat":
        assert result.choices[0].message.content == "ok"
    elif case == "stream":
        assert len(result) == 1
        assert result[0].choices[0].delta.content == "ok"
    elif case == "speech":
        assert result == AUDIO
    elif case == "transcription":
        assert result == {"text": "ok"}
    elif case == "file":
        assert result["id"] == "file-1"
    elif case in ("image", "image_edit"):
        assert result.data[0].url == "https://fixture.invalid/image"
    elif case == "embedding":
        assert result.data[0].embedding == [0.5, -0.2]
    elif case == "workflow_execute":
        assert result.id == "ex-1"
    else:
        assert result.execution_id == "ex-1"


def test_connect_timeout_before_send_can_retry(servers, monkeypatch):
    server = servers(body=success_body("chat"))
    original = requests.post
    attempts = []

    def connect_then_send(*args, **kwargs):
        attempts.append(1)
        if len(attempts) == 1:
            raise requests.exceptions.ConnectTimeout("fixture failed before sending")
        return original(*args, **kwargs)

    monkeypatch.setattr(requests, "post", connect_then_send)
    try:
        result = invoke("chat", client(server))
    except APIError as exc:
        pytest.fail("a safe pre-send ConnectTimeout prevented the normal response: {}".format(exc))
    assert len(attempts) == 2
    assert result.choices[0].message.content == "ok"
    assert_consumed_post(server, "chat")


@pytest.mark.parametrize("max_retries", [0, 1, 3])
def test_connect_timeout_budget_is_bounded(servers, monkeypatch, max_retries):
    server = servers()
    attempts = []

    def cannot_connect(*args, **kwargs):
        attempts.append(1)
        raise requests.exceptions.ConnectTimeout("fixture failed before sending")

    monkeypatch.setattr(requests, "post", cannot_connect)
    with pytest.raises(APIError, match="connecting"):
        invoke("chat", client(server, max_retries))
    assert len(attempts) == max(1, max_retries), "pre-send ConnectTimeout exceeded its bounded attempts"
    assert server.hits == [], "ConnectTimeout fixture unexpectedly sent a body"


@pytest.mark.parametrize("failure", [requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout])
def test_generic_connection_and_read_errors_never_retry(servers, monkeypatch, failure):
    server = servers()
    attempts = []

    def fail(*args, **kwargs):
        attempts.append(1)
        raise failure("fixture response-side failure")

    monkeypatch.setattr(requests, "post", fail)
    with pytest.raises(APIError):
        invoke("chat", client(server))
    assert len(attempts) == 1, "generic response-side failure was retried"
    assert server.hits == []


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("status", [302, 307])
def test_public_post_redirects_never_reach_cross_origin_sink(servers, case, status):
    sink = servers(body=success_body(case))
    source = servers(status=status, body={"error": "fixture redirect"}, location=sink.url + "/sink")
    error = None
    try:
        invoke(case, client(source))
    except APIError as exc:
        error = exc
    assert sink.hits == [], "cross-origin redirect disclosed the request method, body or credential headers"
    assert_consumed_post(source, case)
    assert isinstance(error, APIError), "redirect must retain a typed HTTP response error"
    assert error.status_code == status
    assert error.body == {"error": "fixture redirect"}


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("status", [302, 307])
def test_central_api_redirect_preserves_status_without_disclosing_headers_or_body(servers, method, status):
    sink = servers(body={"ok": True})
    source = servers(status=status, body={"error": "fixture redirect"}, location=sink.url + "/sink")
    error = None
    try:
        client(source)._api_request(method, "/v2/fixture", json={"prompt": MESSAGE} if method == "POST" else None)
    except APIError as exc:
        error = exc
    assert sink.hits == [], "central transport forwarded credentials or body across origins"
    assert len(source.hits) == 1
    assert source.hits[0][0] == method
    assert source.hits[0][2]["Authorization"] == "Bearer post-replay-test-key"
    assert isinstance(error, APIError)
    assert error.status_code == status
    assert error.body == {"error": "fixture redirect"}
