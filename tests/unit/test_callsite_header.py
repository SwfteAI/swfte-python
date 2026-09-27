"""
X-Swfte-Callsite: per-call-site runtime attribution (CONTRACT §6).

Runs every artifact-invoking method against a real local HTTP server
(``http.server`` on 127.0.0.1) and asserts on the headers that actually
arrived on the wire.
"""

import importlib.util
import json
import threading
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from swfte import SwfteClient
from swfte import _callsite

HEADER = "X-Swfte-Callsite"
CS_A = "cs_" + "a" * 24
CS_B = "cs_" + "0123456789abcdef01234567"
CS_C = "cs_" + "c" * 24


class _Handler(BaseHTTPRequestHandler):
    def _reply(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        self.server.seen.append((self.command, self.path, self.headers.get(HEADER)))
        path = self.path.split("?", 1)[0]
        if path.endswith("/invoke") or path.endswith("/execute"):
            body = {"executionId": "ex_1", "status": "QUEUED"}
        elif path.endswith("/status"):
            body = {"execution": {"executionId": "ex_1", "status": "SUCCEEDED"}}
        elif "/chat/" in path:
            body = {"response": "hi", "conversationId": "c_1"}
        else:
            body = {"id": "s_1"}
        raw = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    do_GET = _reply
    do_POST = _reply

    def log_message(self, *args):  # keep pytest output clean
        pass


@pytest.fixture
def server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    srv.seen = []
    thread = threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    yield srv
    srv.shutdown()
    srv.server_close()


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    for name in ("SWFTE_CALLSITE_STACK", "SWFTE_CODEMAP_CALLERS", "SWFTE_ENV", "ENV",
                 "PYTHON_ENV", "SWFTE_API_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)  # no stray <cwd>/.swfte/codemap/callers.json
    monkeypatch.setattr(_callsite, "_production_warned", False)


@pytest.fixture
def client(server):
    host, port = server.server_address
    return SwfteClient(api_key="k", api_base_url=f"http://{host}:{port}")


def call_every_method(client, **kw):
    """One call per artifact-invoking method; returns the method names in order."""
    client.workflows.invoke("wf_1", {"x": 1}, **kw)
    client.workflows.invoke_and_wait("wf_1", {"x": 1}, timeout=5, poll_interval=0, **kw)
    client.workflows.execute("wf_1", {"x": 1}, **kw)
    client.agents.chat("ag_1", "hello", **kw)
    client.chatflows.start_session("cf_1", **kw)
    client.chatflows.test("cf_1", {"a": 1}, **kw)


def invoking(seen):
    """Headers of the artifact-invoking requests (status polls excluded)."""
    return [(m, p, h) for (m, p, h) in seen if not p.split("?")[0].endswith("/status")]


def write_map(tmp_path, entries, root=None):
    path = tmp_path / ".swfte" / "codemap" / "callers.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"version": 1, "root": str(root or tmp_path), "entries": entries}))
    return path


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def line_of(path, needle):
    for i, text in enumerate(path.read_text().splitlines(), start=1):
        if needle in text:
            return i
    raise AssertionError(f"{needle!r} not in {path}")


def test_default_sends_no_header(client, server, tmp_path):
    # even a matching caller map is ignored without the opt-in flag
    write_map(tmp_path, {"anything.py:1": CS_A})
    call_every_method(client)
    assert len(invoking(server.seen)) == 6
    assert all(h is None for (_, _, h) in server.seen)


def test_explicit_id_on_each_method_family(client, server):
    call_every_method(client, callsite=CS_B)
    calls = invoking(server.seen)
    assert [p.split("?")[0] for (_, p, _) in calls] == [
        "/v2/workflows/wf_1/invoke",
        "/v2/workflows/wf_1/invoke",
        "/v2/workflows/wf_1/execute",
        "/v1/agents/ag_1/chat/sdk-user",
        "/v2/chatflows/cf_1/sessions",
        "/v2/chatflows/builder/cf_1/test",
    ]
    assert [h for (_, _, h) in calls] == [CS_B] * 6
    polls = [h for (_, p, h) in server.seen if p.endswith("/status")]
    assert polls and all(h is None for h in polls)


@pytest.mark.parametrize("bad", [
    "cs_" + "A" * 24,            # upper-case hex
    "cs_" + "a" * 23,            # too short
    "cs_" + "a" * 25,            # too long
    "cs_" + "g" * 24,            # not hex
    "xx_" + "a" * 24,            # wrong prefix
    "",
    " cs_" + "a" * 24,
    "cs_" + "a" * 24 + "\n",
])
def test_invalid_id_is_never_sent(client, server, tmp_path, monkeypatch, bad):
    # stack capture on and a matching map present: the invalid explicit id still sends nothing
    monkeypatch.setenv("SWFTE_CALLSITE_STACK", "1")
    call_every_method(client, callsite=bad)
    assert all(h is None for (_, _, h) in server.seen)


def test_invalid_id_in_the_caller_map_is_never_sent(client, server, tmp_path, monkeypatch):
    mod_path = tmp_path / "bad_caller.py"
    mod_path.write_text("def run(c):\n    return c.workflows.invoke('wf_1', {})\n")
    write_map(tmp_path, {"bad_caller.py:2": "cs_NOT-VALID"})
    monkeypatch.setenv("SWFTE_CALLSITE_STACK", "1")
    load_module(mod_path, "cmap_bad_caller").run(client)
    assert server.seen[-1][2] is None


def _two_callers(tmp_path):
    pkg = tmp_path / "app"
    pkg.mkdir()
    a = pkg / "billing.py"
    b = pkg / "reports.py"
    a.write_text("def go(client):\n    return client.workflows.invoke('wf_1', {'from': 'a'})\n")
    b.write_text(
        "import os\n\n\ndef go(client):\n"
        "    x = os.getpid()\n"
        "    return client.workflows.invoke('wf_1', {'from': 'b', 'x': x})\n"
    )
    return a, b


def test_two_callers_of_one_method_get_two_ids_under_stack_capture(client, server, tmp_path, monkeypatch):
    a, b = _two_callers(tmp_path)
    la, lb = line_of(a, "invoke("), line_of(b, "invoke(")
    write_map(tmp_path, {f"app/billing.py:{la}": CS_A, f"app/reports.py:{lb}": CS_C})
    monkeypatch.setenv("SWFTE_CALLSITE_STACK", "1")
    load_module(a, "cmap_app_billing").go(client)
    load_module(b, "cmap_app_reports").go(client)
    assert [h for (_, _, h) in server.seen] == [CS_A, CS_C]


def test_stack_capture_resolves_for_every_method_family(client, server, tmp_path, monkeypatch):
    mod_path = tmp_path / "every.py"
    lines = [
        "def run(c):",
        "    c.workflows.invoke('wf_1', {})",
        "    c.workflows.invoke_and_wait('wf_1', {}, timeout=5, poll_interval=0)",
        "    c.workflows.execute('wf_1', {})",
        "    c.agents.chat('ag_1', 'hi')",
        "    c.chatflows.start_session('cf_1')",
        "    c.chatflows.test('cf_1', {})",
    ]
    mod_path.write_text("\n".join(lines) + "\n")
    ids = ["cs_" + f"{n:024x}" for n in range(1, 7)]
    write_map(tmp_path, {f"every.py:{n + 2}": ids[n] for n in range(6)})
    monkeypatch.setenv("SWFTE_CALLSITE_STACK", "1")
    load_module(mod_path, "cmap_every").run(client)
    assert [h for (_, _, h) in invoking(server.seen)] == ids
    assert all(h is None for (_, p, h) in server.seen if p.endswith("/status"))


def test_env_path_to_caller_map_is_honoured(client, server, tmp_path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    mod_path = src / "job.py"
    mod_path.write_text("def run(c):\n    return c.agents.chat('ag_1', 'hi')\n")
    elsewhere = tmp_path / "maps" / "callers.json"
    elsewhere.parent.mkdir()
    elsewhere.write_text(json.dumps({"version": 1, "root": str(src), "entries": {"job.py:2": CS_A}}))
    monkeypatch.setenv("SWFTE_CODEMAP_CALLERS", str(elsewhere))
    monkeypatch.setenv("SWFTE_CALLSITE_STACK", "1")
    load_module(mod_path, "cmap_job").run(client)
    assert server.seen[-1][2] == CS_A


@pytest.mark.parametrize("var", ["SWFTE_ENV", "ENV", "PYTHON_ENV"])
def test_production_refuses_stack_capture_but_honours_explicit(client, server, tmp_path, monkeypatch, var):
    mod_path = tmp_path / "prod_caller.py"
    mod_path.write_text(
        "def run(c):\n"
        "    c.workflows.invoke('wf_1', {})\n"
        "    c.workflows.invoke('wf_1', {})\n"
    )
    write_map(tmp_path, {"prod_caller.py:2": CS_A, "prod_caller.py:3": CS_A})
    monkeypatch.setenv("SWFTE_CALLSITE_STACK", "1")
    monkeypatch.setenv(var, "production")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        load_module(mod_path, "cmap_prod_caller").run(client)
        client.workflows.invoke("wf_1", {}, callsite=CS_B)
    assert [h for (_, _, h) in server.seen] == [None, None, CS_B]
    refusals = [w for w in caught if "SWFTE_CALLSITE_STACK" in str(w.message)]
    assert len(refusals) == 1


def test_explicit_wins_over_stack_capture(client, server, tmp_path, monkeypatch):
    mod_path = tmp_path / "explicit_caller.py"
    mod_path.write_text(
        "def run(c, cs):\n"
        "    return c.workflows.invoke('wf_1', {}, callsite=cs)\n"
    )
    write_map(tmp_path, {"explicit_caller.py:2": CS_A})
    monkeypatch.setenv("SWFTE_CALLSITE_STACK", "1")
    mod = load_module(mod_path, "cmap_explicit_caller")
    mod.run(client, CS_B)
    mod.run(client, None)  # same line, no explicit id: the map applies
    assert [h for (_, _, h) in server.seen] == [CS_B, CS_A]


def test_missing_or_unmatched_map_sends_nothing(client, server, tmp_path, monkeypatch):
    mod_path = tmp_path / "unmapped.py"
    mod_path.write_text("def run(c):\n    return c.workflows.invoke('wf_1', {})\n")
    monkeypatch.setenv("SWFTE_CALLSITE_STACK", "1")
    mod = load_module(mod_path, "cmap_unmapped")
    mod.run(client)                                    # no map at all
    write_map(tmp_path, {"unmapped.py:99": CS_A})
    mod.run(client)                                    # map, wrong line
    write_map(tmp_path, {"unmapped.py:2": CS_A}, root=tmp_path / "other-root")
    mod.run(client)                                    # map, file outside its root
    (tmp_path / ".swfte" / "codemap" / "callers.json").write_text("{not json")
    mod.run(client)                                    # corrupt map
    assert [h for (_, _, h) in server.seen] == [None, None, None, None]


def test_stack_flag_must_be_exactly_one(client, server, tmp_path, monkeypatch):
    mod_path = tmp_path / "flag_caller.py"
    mod_path.write_text("def run(c):\n    return c.workflows.invoke('wf_1', {})\n")
    write_map(tmp_path, {"flag_caller.py:2": CS_A})
    mod = load_module(mod_path, "cmap_flag_caller")
    for value in ("true", "0", "yes"):
        monkeypatch.setenv("SWFTE_CALLSITE_STACK", value)
        mod.run(client)
    assert [h for (_, _, h) in server.seen] == [None, None, None]
