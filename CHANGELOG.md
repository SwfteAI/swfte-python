# Changelog

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
