"""Stdlib preflight branches with mocks and isolated loopback; no registry call."""

import importlib.util
import io
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from unittest.mock import MagicMock

import pytest

source = Path(__file__).resolve().parents[2] / "scripts" / "check_pypi_version.py"
spec = importlib.util.spec_from_file_location("pypi_version_preflight", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_pypi_exact_404_is_the_only_publication_positive_control():
    def absent(url, timeout):
        assert url == "https://pypi.org/pypi/swfte-sdk/1.2.0/json"
        assert timeout == 15
        raise HTTPError(url, 404, "missing", {}, io.BytesIO(b""))
    module.require_unpublished("1.2.0", absent)


def test_pypi_existing_forbidden_redirect_outage_and_network_failure_block_publication():
    for status in [200, 301, 403, 429, 500, 503]:
        def failed(url, timeout):
            raise HTTPError(url, status, "fixture", {}, io.BytesIO(b""))
        with pytest.raises(RuntimeError):
            module.require_unpublished("1.2.0", failed)
    for failure in [URLError("offline fixture"), TimeoutError("timeout fixture")]:
        def offline(url, timeout):
            raise failure
        with pytest.raises(RuntimeError, match="could not be verified"):
            module.require_unpublished("1.2.0", offline)


def test_pypi_success_response_200_is_also_blocked_and_workflow_uses_guard():
    result = MagicMock()
    result.__enter__.return_value = result
    result.getcode.return_value = 200
    with pytest.raises(RuntimeError, match="already exists"):
        module.require_unpublished("1.2.0", lambda url, timeout: result)
    workflow = (source.parents[1] / ".github" / "workflows" / "release.yml").read_text()
    assert 'python scripts/check_pypi_version.py "$VERSION"' in workflow


def test_pypi_actual_redirect_handler_never_reaches_404_sink_and_direct_404_allows():
    reads = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            reads.append(self.path)
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/sink")
            else:
                self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = "http://127.0.0.1:{}".format(server.server_port)
    # Use the real production default opener against an isolated loopback URL.
    default_open = module.require_unpublished.__defaults__[0]
    try:
        with pytest.raises(RuntimeError, match="HTTP 302"):
            module.require_unpublished("1.2.0", lambda url, timeout: default_open(base + "/redirect", timeout))
        assert reads == ["/redirect"], "a redirect must never reach the apparent-404 sink"
        module.require_unpublished("1.2.0", lambda url, timeout: default_open(base + "/direct", timeout))
        assert reads == ["/redirect", "/direct"]
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
        assert not worker.is_alive()
