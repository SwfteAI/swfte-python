"""Behavioral error/representation controls with only synthetic credentials."""

import json
import linecache
import pickle
import traceback
from urllib.parse import quote

import pytest
import requests

from swfte import SwfteClient
from swfte.exceptions import (APIError, AuthenticationError, RateLimitError,
                              SwfteError, WorkflowExecutionError, WorkflowPausedError, WorkflowTimeoutError)

KEY = 'opaque-review-"-\\-/-space fixture'


def echo(key=KEY):
    return {"message": "backend refused " + key, "safe": "retry in Studio",
            "nested": {key: [key, 7, False, None]}}


def response(value, status=200, key=KEY):
    result = requests.Response()
    result.status_code = status
    result.url = "https://fixture.test/" + quote(key, safe="")
    result.reason = "safe reason"
    result._content = json.dumps(value).encode()
    result._content_consumed = True
    result.headers["Content-Type"] = "application/json"
    result.request = requests.Request("POST", result.url, headers={"Authorization": "Bearer " + key}).prepare()
    return result


def semantic_traceback(error):
    """Keep source and exception text; omit interpreter column decorations."""
    summary = traceback.TracebackException(type(error), error, error.__traceback__)
    pending = [summary]
    seen = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        current.stack = traceback.StackSummary.from_list([
            (frame.filename, frame.lineno, frame.name, frame.line)
            for frame in current.stack
        ])
        pending.extend(item for item in (current.__cause__, current.__context__)
                       if item is not None)
        pending.extend(getattr(current, "exceptions", None) or [])
    return "".join(summary.format())


def assert_private(error, key=KEY):
    diagnostic = "\n".join([str(error), repr(error), repr(vars(error)),
                             semantic_traceback(error)])
    for literal in [key, repr(key)[1:-1], json.dumps(key)[1:-1], quote(key, safe="")]:
        assert literal not in diagnostic
    assert error.__context__ is None
    if error.__cause__ is not None:
        assert_private(error.__cause__, key)


def test_traceback_normalization_still_rejects_semantic_credential_leaks(monkeypatch):
    marker = RuntimeError("semantic decoration\n    ~~~~^^^^")
    assert str(marker) in semantic_traceback(marker)
    with pytest.raises(AssertionError):
        assert_private(marker, "~")

    for key in ["~", KEY]:
        for literal in [key, repr(key)[1:-1], json.dumps(key)[1:-1], quote(key, safe="")]:
            message = RuntimeError("semantic message " + literal)
            assert literal in semantic_traceback(message)
            with pytest.raises(AssertionError):
                assert_private(message, key)

            cause = RuntimeError("semantic cause " + literal)
            outer = RuntimeError("safe outer message")
            outer.__cause__ = cause
            assert literal in semantic_traceback(outer)
            with pytest.raises(AssertionError):
                assert_private(outer, key)

            context = RuntimeError("semantic context " + literal)
            outer = RuntimeError("safe outer message")
            outer.__context__ = context
            assert literal in semantic_traceback(outer)
            with pytest.raises(AssertionError):
                assert_private(outer, key)

            filename = "<synthetic-credential-source>"
            source = 'raise RuntimeError("safe message")  # ' + literal + "\n"
            monkeypatch.setitem(linecache.cache, filename,
                                (len(source), None, [source], filename))
            try:
                exec(compile(source, filename, "exec"), {})
            except RuntimeError as captured:
                assert literal in semantic_traceback(captured)
                with pytest.raises(AssertionError):
                    assert_private(captured, key)
            else:
                pytest.fail("the synthetic source must raise")


def test_client_vars_repr_and_pickle_do_not_retain_credential():
    client = SwfteClient(api_key=KEY)
    client.chat  # Exercise resource backreferences as well as a bare client.
    assert KEY not in repr(client)
    assert KEY not in repr(vars(client))
    assert repr(KEY)[1:-1] not in repr(vars(client))
    assert "api_key" not in vars(client)
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        with pytest.raises(TypeError, match="cannot be pickled"):
            pickle.dumps(client, protocol=protocol)
    assert client.api_key == KEY
    assert client._get_headers()["Authorization"] == "Bearer " + KEY


def test_http_errors_preserve_types_and_safe_fields_without_raw_or_encoded_key(monkeypatch):
    for key in [KEY, "r5X", "~"]:
        for status in [401, 403, 429, 500]:
            result = response(echo(key), status, key)
            calls = []
            monkeypatch.setattr(requests, "request", lambda *a, **kw: calls.append(kw) or result)
            client = SwfteClient(api_key=key)
            kind = AuthenticationError if status in (401, 403) else RateLimitError if status == 429 else APIError
            with pytest.raises(kind) as caught:
                client._api_request("POST", "/v2/catalog/" + quote(key, safe=""))
            error = caught.value
            assert "backend refused" in str(error)
            assert "retry in Studio" in str(error)
            if status == 500:
                assert error.status_code == 500
                assert error.body["safe"] == "retry in Studio"
                assert error.body["nested"]["[REDACTED]"] == ["[REDACTED]", 7, False, None]
            assert len(calls) == 1
            assert_private(error, key)
            assert result.json()["nested"][key][0] == key, "the shared backend response must not be mutated"


def test_replacement_marker_never_reintroduces_literal_credential_value(monkeypatch):
    for key in ["E", "*"]:
        result = response({"echo": key, "safe": "keep detail"}, 500, key)
        monkeypatch.setattr(requests, "request", lambda *a, **kw: result)
        with pytest.raises(APIError) as caught:
            SwfteClient(api_key=key)._api_request("POST", "/fixture")
        error = caught.value
        assert error.status_code == 500
        assert error.body["echo"] == ("*" if key == "E" else "[REDACTED]")
        assert key not in error.body["echo"]
        assert error.body["safe"] == "keep detail"


def test_legacy_http_error_request_response_and_cause_are_safe(monkeypatch):
    result = response(echo(), 500)
    monkeypatch.setattr(requests, "request", lambda *a, **kw: result)
    with pytest.raises(requests.HTTPError) as caught:
        SwfteClient(api_key=KEY).agents.get(KEY)
    error = caught.value
    assert error.response.status_code == 500
    assert error.response.json()["safe"] == "retry in Studio"
    assert error.request.headers["Authorization"] == "Bearer [REDACTED]"
    assert_private(error)

    source = requests.ConnectionError("connection detail " + KEY, response=result)
    source.__cause__ = ValueError("cause detail " + KEY)
    monkeypatch.setattr(requests, "request", lambda *a, **kw: (_ for _ in ()).throw(source))
    with pytest.raises(requests.ConnectionError) as failed:
        SwfteClient(api_key=KEY)._api_request("POST", "/fixture")
    assert "connection detail" in str(failed.value)
    assert isinstance(failed.value.__cause__, ValueError)
    assert source.response is result and KEY in str(source)
    assert_private(failed.value)


def test_gateway_parser_and_plain_backend_failures_are_safe(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: response(echo(), 500))
    with pytest.raises(APIError) as caught:
        SwfteClient(api_key=KEY).chat.completions.create(model="fixture", messages=[])
    assert caught.value.status_code == 500
    assert "retry in Studio" in str(caught.value)
    assert_private(caught.value)

    source = response({}, 200)
    source.json = lambda: (_ for _ in ()).throw(ValueError("parser detail " + KEY))
    monkeypatch.setattr(requests, "post", lambda *a, **kw: source)
    with pytest.raises(ValueError) as parser:
        SwfteClient(api_key=KEY).embeddings.create(model="fixture", input="safe")
    assert "parser detail" in str(parser.value)
    assert_private(parser.value)


def test_redirect_failure_body_is_private_and_never_replayed(monkeypatch):
    calls = []
    monkeypatch.setattr(requests, "post", lambda *a, **kw: calls.append(kw) or response(echo(), 307))
    with pytest.raises(APIError) as caught:
        SwfteClient(api_key=KEY).chat.completions.create(model="fixture", messages=[])
    assert caught.value.status_code == 307
    assert caught.value.body["safe"] == "retry in Studio"
    assert len(calls) == 1 and calls[0]["allow_redirects"] is False
    assert_private(caught.value)


def test_gateway_legacy_v2_and_analytics_error_families_share_private_boundary(monkeypatch):
    from swfte.analytics.forecasting import UsageForecaster
    from swfte.analytics.custom import MetricsManager
    from swfte.analytics.enterprise import TeamAnalytics
    client = SwfteClient(api_key=KEY)
    calls = []
    def failed(*args, **kwargs):
        calls.append(kwargs)
        return response(echo(), 500)
    for method in ["request", "post", "get"]:
        monkeypatch.setattr(requests, method, failed)
    methods = [
        lambda: client.images.generate(model="fixture", prompt="safe"),
        lambda: client.audio.transcriptions.create(model="fixture", file=b"safe"),
        lambda: client.audio.speech.create(model="fixture", input="safe"),
        lambda: client.models.list(),
        lambda: client.secrets.get(KEY),
        lambda: client.conversations.get(KEY),
        lambda: client.deployments.get(KEY),
        lambda: client.chatflows.get(KEY),
        lambda: client.analytics.prompts.summary(KEY),
        lambda: UsageForecaster(client).predict_usage(workspace_id=KEY),
        lambda: MetricsManager(client).get(KEY),
        lambda: client.analytics.alerts.get_rule(KEY),
        lambda: TeamAnalytics(client).summary(KEY),
        lambda: client.analytics.realtime.list_subscriptions(),
    ]
    for invoke in methods:
        before = len(calls)
        with pytest.raises((SwfteError, requests.HTTPError)) as caught:
            invoke()
        assert len(calls) == before + 1
        assert_private(caught.value)


def test_deployment_failure_redacts_backend_detail_and_caller_id(monkeypatch):
    monkeypatch.setattr(requests, "request", lambda *a, **kw: response({
        "id": "fixture", "state": "FAILED", "statusMessage": "capacity detail " + KEY,
    }))
    with pytest.raises(RuntimeError) as caught:
        SwfteClient(api_key=KEY).deployments.wait_for_ready(KEY, timeout=2, poll_interval=0)
    assert "capacity detail" in str(caught.value)
    assert_private(caught.value)


def test_stream_failure_captures_original_credential_and_closes_response(monkeypatch):
    closed = []
    result = response({}, 200)
    source = requests.ConnectionError("reader detail " + KEY)
    result.iter_lines = lambda: (_ for _ in ()).throw(source)
    result.close = lambda: closed.append(True)
    headers = []
    monkeypatch.setattr(requests, "post", lambda *a, **kw: headers.append(kw["headers"]) or result)
    client = SwfteClient(api_key=KEY)
    stream = client.chat.completions.create(model="fixture", messages=[], stream=True)
    client.api_key = "replacement-credential-fixture"
    with pytest.raises(requests.ConnectionError) as caught:
        list(stream)
    assert headers[0]["Authorization"] == "Bearer " + KEY
    assert closed == [True]
    assert "reader detail" in str(caught.value)
    assert_private(caught.value)


def test_stream_error_frame_is_private_and_success_content_is_unchanged(monkeypatch):
    result = response({}, 200)
    result.iter_lines = lambda: iter([("data: " + json.dumps({"error": echo()})).encode()])
    monkeypatch.setattr(requests, "post", lambda *a, **kw: result)
    client = SwfteClient(api_key=KEY)
    with pytest.raises(APIError) as caught:
        list(client.chat.completions.create(model="fixture", messages=[], stream=True))
    assert caught.value.body["error"]["safe"] == "retry in Studio"
    assert_private(caught.value)
    chunk = {"id": "fixture", "choices": [{"index": 0, "delta": {"content": KEY}}]}
    result.iter_lines = lambda: iter([("data: " + json.dumps(chunk)).encode(), b"data: [DONE]"])
    values = list(client.chat.completions.create(model="fixture", messages=[], stream=True))
    assert values[0].choices[0].delta.content == KEY


def test_workflow_malformed_and_terminal_error_objects_are_private(monkeypatch):
    client = SwfteClient(api_key=KEY)
    monkeypatch.setattr(requests, "request", lambda *a, **kw: response(echo(), 202))
    with pytest.raises(APIError) as malformed:
        client.workflows.invoke("fixture")
    assert malformed.value.body["safe"] == "retry in Studio"
    assert_private(malformed.value)
    for status in ["FAILED", "CANCELED", "PAUSED", "RUNNING"]:
        body = {"execution": {"executionId": "execution-1", "status": status,
                              "errorInfo": echo(), "outputData": echo()},
                "nodeExecutions": [{"nodeId": KEY, "nodeType": "HUMAN_INPUT", "status": "PAUSED", "pauseReason": KEY}]}
        replies = iter([response({"executionId": "execution-1"}, 202), response(body)])
        monkeypatch.setattr(requests, "request", lambda *a, **kw: next(replies))
        kind = WorkflowPausedError if status == "PAUSED" else WorkflowTimeoutError if status == "RUNNING" else WorkflowExecutionError
        with pytest.raises(kind) as caught:
            client.workflows.invoke_and_wait("fixture", timeout=0, raise_on_pause=True)
        error = caught.value
        assert error.execution_id == "execution-1"
        execution = error.last_status if status == "RUNNING" else error.execution
        assert execution.outputs["safe"] == "retry in Studio"
        assert_private(error)


def test_successful_secret_values_and_other_callers_diagnostic_text_are_unchanged(monkeypatch):
    value = {"value": KEY, "nested": echo()}
    monkeypatch.setattr(requests, "request", lambda *a, **kw: response(value))
    client = SwfteClient(api_key=KEY)
    assert client._api_request("GET", "/v2/secrets/fixture") == value
    other = "other-caller-opaque-fixture"
    source = requests.ConnectionError("safe marker " + other + " " + KEY)
    monkeypatch.setattr(requests, "request", lambda *a, **kw: (_ for _ in ()).throw(source))
    with pytest.raises(requests.ConnectionError) as caught:
        client._api_request("POST", "/fixture")
    assert other in str(caught.value)
    assert_private(caught.value)
