# Changelog

## Unreleased

### Fixed

- `workflows.invoke_and_wait` / `wait_for_completion` no longer burn the whole
  timeout on a human-in-the-loop run: `PAUSED` / `WAITING_FOR_INPUT` (see
  `PAUSED_STATUSES`) return at once with `execution.paused` True and
  `execution.waiting_for` (the gate node from `nodeExecutions`);
  `raise_on_pause=True` raises `WorkflowPausedError` instead.
  `classify_execution_status` gains `"paused"`.
- README: the package is `swfte-sdk` (`pip install swfte-sdk`), imported as `swfte`.

### Added

- `agents.chat(agent_id, message, user_id=None, conversation_id=None)` —
  `POST /v1/agents/{agent_id}/chat/{user_id}` with
  `{"message": ..., "conversationId": ...}`. Returns `AgentChatResponse` with
  `.response` (normalised from `content` when the server uses that key),
  `.conversation_id` and `.raw`. `user_id` defaults to `"sdk-user"`
  (`DEFAULT_CHAT_USER_ID`).
- `workflows.invoke(workflow_id, inputs)` — `POST /v2/workflows/{id}/invoke`,
  runs the published snapshot; returns `WorkflowInvocation(execution_id=...)`.
- `workflows.invoke_and_wait(workflow_id, inputs, timeout=300, poll_interval=2)`
  — invokes and polls to a terminal status. Success is any of `SUCCESS`,
  `SUCCEEDED`, `COMPLETED`; `FAILED`/`TIMEOUT`/`CANCELLED`/`CANCELED` raise
  `WorkflowExecutionError` (a `RuntimeError`); the client-side deadline raises
  `WorkflowTimeoutError` (a `TimeoutError`).
- `catalog.search(...)`, `catalog.get(kind, id)`, `catalog.contract(kind, id)`
  over `/v2/catalog/*`.
- `api_base_url` argument (and `SWFTE_API_BASE_URL`) for the agents-service root.
  Defaults to `base_url` minus its trailing gateway segment — what every
  management resource already computed; they now all read it from one place.
- `APIError` carries `status_code` and `body`. The new calls map 401/403 to
  `AuthenticationError` and 429 to `RateLimitError` and are never retried.

### Changed

- `workflows.get_execution_status()` understands the server's
  `{"execution": {...}, "nodeExecutions": [...], "progress": n}` shape. It used to
  read `status` from the top level, where it never is, so every execution looked
  `PENDING`. `WorkflowExecution` gains `status_raw`, `outcome`, `is_terminal`,
  `succeeded`, `node_executions` and `raw`; `ExecutionStatus` gains `SUCCESS`,
  `SUCCEEDED`, `TIMEOUT` and `CANCELED`.
- `workflows.wait_for_completion()` shares the new terminal rules (it only knew
  `COMPLETED`, so it timed out on every successful run). Its exceptions subclass
  the `TimeoutError` / `RuntimeError` it raised before.
- `pytest` no longer requires `pytest-cov`: the coverage flags moved from
  `addopts` to CI.

### Fixed

- `test_client_default_base_url` asserted the pre-1.1.1 default URL.

## 1.1.1 — 2026-09-01

### Fixed

- **The shipped default `base_url` returned 403.** `SwfteClient(api_key=...)` —
  the first line of every quickstart — could not make a request. The default
  pointed at `https://api.swfte.com/v2/gateway`, which is not a route: the
  gateway lives behind `/agents`, so the request was refused with a bare nginx
  403 that surfaced as an HTML blob rather than a usable error. The default is
  now `https://api.swfte.com/agents/v2/gateway`.

  Verified against production with a key created in the Connect console:
  the old path answers 403, the new one answers 200 with a completion and
  metered usage. Anyone who had worked around this by passing `base_url`
  explicitly is unaffected.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.1.0 — 2026-05-07

### Added
- New V2 resource clients exposed on `SwfteClient`:
  - `client.chatflows` — full ChatFlow CRUD, builder, sessions, versions and publishing.
  - `client.datasets` and `client.documents` — RAG dataset and document management with batch
    update + processing-status endpoints.
  - `client.files` — single and batch upload, list, get, download, preview, delete, cleanup.
  - `client.rag` — hybrid search, reranking, model catalogues, retrieval strategies and
    BM25 vocabulary management.
  - `client.mcp` — connect/list/disconnect MCP servers, list tools, schema, single and
    batch execute, analytics, health-check and tool status.
  - `client.modules` — module CRUD, resource attachment, build (with SSE progress),
    versions, QA bank, impact reports.
  - `client.marketplace` — browse, install, list installations and uninstall.
  - `client.voice_calls` — list, in-progress, get, transcript, recording, audit and
    chatflow-scoped call lookup.
  - `client.audit` — workspace event query, resource-scoped events, "my events" and
    CSV/JSON export.
  - `client.cost_control` — routing rule CRUD + toggle, workspace and per-model usage
    caps, usage statistics and per-deployment scaling configuration.
  - `client.agent_wizard` — generate, refine, review and persist agents from prompts
    or templates; link MCP tools and knowledge bases.
- `docs/cookbook/` — runnable Python examples for each of the top-15 V2 controllers.
- `ABOUT.md` — full Swfte company profile.
- `README.md` "About Swfte" section and "Resources" footer with links to
  [swfte.com](https://www.swfte.com), [/resources](https://www.swfte.com/resources),
  [/developers](https://www.swfte.com/developers), [/pricing](https://www.swfte.com/pricing),
  [/security](https://www.swfte.com/security) and [status.swfte.com](https://status.swfte.com).

### Changed
- `User-Agent` bumped to `swfte-python/1.1.0`.
- Workspace ID now sent as both `X-Workspace-ID` and `x-workspace-id` for compatibility
  with strict header normalisation in some intermediaries.
- `pyproject.toml` URLs now point to [github.com/SwfteAI/swfte-python](https://github.com/SwfteAI/swfte-python)
  and [www.swfte.com](https://www.swfte.com).

## [1.0.0] - 2025-01-XX

### Added
- Unified API client for all AI providers
- Chat completions with streaming support
- Image generation (DALL-E, Stable Diffusion)
- Audio transcription and text-to-speech
- Embeddings generation
- Agent management (CRUD operations)
- Workflow orchestration
- Automatic retry logic with exponential backoff
- Rate limit handling
- Full type hints for IDE support
- Async/await support
- Environment variable configuration

### Supported Providers
- OpenAI (GPT-4, GPT-3.5, DALL-E, Whisper, TTS)
- Anthropic (Claude 3 family)
- Google (Gemini Pro)
- Self-hosted models via RunPod

---

[1.1.0]: https://github.com/SwfteAI/swfte-python/releases/tag/v1.1.0
[1.0.0]: https://github.com/SwfteAI/swfte-python/releases/tag/v1.0.0
