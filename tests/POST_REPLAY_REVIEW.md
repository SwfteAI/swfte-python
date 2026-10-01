# SDK POST repair source handoff

Status: SOURCE FROZEN FOR DRIVER VERIFICATION. No build, install, test, mutation
or network command was executed by the repair agent. Runtime gates remain
pending. This report belongs to the commit that contains it; the handoff gives
that exact final commit separately.

Base: `89fb09d36ac9c4e64b2178069f062936c8aa8e92`.
Early production checkpoint: `7635707` (narrow chat retry repair).

Changes and source evidence:

- `swfte/chat.py`: only Requests' documented pre-send `ConnectTimeout`
  reaches the retry loop. Generic `ConnectionError` can follow server
  execution, so it reaches the immediate typed failure path. A zero retry
  setting still means one attempt.
- `swfte/_http.py`: shared transport forcibly supplies
  `allow_redirects=False`, closes a refused response and raises `APIError`
  retaining its original 3xx status and JSON/text body.
- All 111 HTTP calls in 18 source modules route through that guard, including
  independent analytics calls and every HTTP verb. The exact file/line
  inventory is `tests/post_transport_inventory.json`. There is no direct
  Requests send or custom Requests session remaining outside the guard.
  Websocket behavior is outside this HTTP POST leaf.
- `pyproject.toml` keeps Python >=3.8 and the patched Requests >=2.32.4 floor,
  uses setuptools >=68,<77, and supplies the MIT LICENSE through legacy
  PEP 621 file metadata. Root independently resolved Requests 2.32.4 and
  dependencies on CPython 3.8.20; full artifact proof is still pending.
- PR CI explicitly has `contents: read`, includes Python 3.8 and builds
  wheel/sdist before packaging tests. Existing release SHA pins, OIDC jobs and
  publish guards were preserved.
- Old expectations now describe generic connection refusal as non-retriable.
  An existing empty-response test now declares its real 204 status instead of
  leaving a non-numeric MagicMock status; its original routing assertion is
  retained. Documentation states the exact retry and redirect policies.

Native proof source:

`tests/unit/test_post_replay.py` uses actual loopback source/sink servers that
record the entire request before closing without a response, answering normally
or returning a cross-origin 302/307. Authentication and workspace headers,
UTF-8 JSON, multipart bytes/fields and exact POST counts are inspected. Its nine
public operations cover chat, streaming chat, transcription, speech, file upload,
workflow invoke, image generation, multipart image edit and embeddings. Normal
responses are parsed through the real public APIs. Safe ConnectTimeout is
injected strictly before the real send and followed by a real successful call.

Source parameter accounting predicts 55 cases, with zero skips:

- consumed-body/drop: 18 (nine public paths, retry settings 0 and 3);
- normal response: 9;
- safe retry/budget/generic-error controls: 6;
- public cross-origin 302/307: 18;
- central authenticated GET/POST cross-origin 302/307: 4.

Driver execution, in this clone, must first install its isolated dependencies.
Run these as separate inspected commands, preserving direct exit statuses:

```text
.venv/bin/python -m pytest -q tests/unit/test_post_replay.py
.venv/bin/python -m pytest -q tests/unit tests/packaging/test_repo_shape.py
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*
.venv/bin/python -m pytest -q tests/packaging
/private/tmp/swfte-p5-resume-20261001/python38-proof/bin/python tests/packaging/check_python38_artifacts.py
.venv/bin/python tests/run_post_replay_mutations.py
```

The real 3.8 artifact helper refuses newer interpreters, builds both artifacts
through isolated backend resolution, verifies exact MIT LICENSE bytes and
Requires-Python metadata, and installs each into a separate fresh 3.8 consumer.
Each consumer imports every installed module under `-I`; success requires both
consumer counts and `PY38_WHEEL_SDIST_INSTALL_PASSED`. It needs build frontend,
venv/pip and approved dependency resolution. A syntax parse alone is not 3.8
installation proof.

Literal guard matrix: `tests/post_replay_mutations.json` (12 mutants).
Every anchor was inspected and matched exactly once; no mutant was executed.
`tests/run_post_replay_mutations.py` requires a passing selected baseline,
executes one literal production change, restores source bytes in finally, then
requires a passing restored result. A killed control must have actual assertion
failures, no collection/runtime errors or skips, the same named test set and the
matrix's named assertion. It records baseline/mutant/restored XML and hashes.
The runner never treats a broken import or uncollected test as a killed guard.

Four source passes:

1. Narrow replay fix; preserve status mappings and retry attempt semantics.
2. Follow every public HTTP path; protect redirect bodies as well as auth;
   preserve existing Requests mock hooks through the wrapper.
3. Review native consumed-body/sink controls and portability; repair the legacy
   mock status, safe-retry assertion handling and true-3.8 AST argument;
   inspect literal anchors and killed/restored requirements.
4. Re-read complete changes and metadata. Preserve patched dependencies,
   licensing, release job boundaries and exact source ownership. No additional
   source defect remained in this pass.

Remaining owner work: execute all native and compatibility gates, genuine 3.8
artifact/consumer proof and the 12 baseline/killed/restored cycles; independently
inspect final diff/tip and publish only through the driver's authorized PR flow.
No runtime pass or release readiness is claimed here.
