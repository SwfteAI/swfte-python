# Releasing `swfte-sdk`

**Nothing has ever been published from this repository** — `swfte-sdk` returns
404 on PyPI. The name is therefore still free, and the first publish claims it.

## What has to exist first (one-time)

| Thing | State | Notes |
|---|---|---|
| `PYPI_API_TOKEN` repository secret | **already set** (2026-05-07) | scope it to the project after the first publish |
| `pypi-publish-prod` environment | create under Settings → Environments | add required reviewers if the plan allows |

### Optional, and better: Trusted Publishing

The nexus-devtools release uses PyPI Trusted Publishing (OIDC) so no long-lived
token exists anywhere. To move here too: on PyPI add a *pending publisher* for
`SwfteAI/swfte-python`, workflow `release.yml`, environment
`pypi-publish-prod`, then delete the `password:` line from the publish step.
The workflow already requests `id-token: write`, so nothing else changes.

## Cutting a release

1. Bump `version` in `pyproject.toml`, add a `CHANGELOG.md` entry, merge.
2. Optionally tag `v<version>` and push. **This builds and verifies; it does not
   publish.** The previous workflow published on tag push with no confirmation.
3. Actions → **Release** → *Run workflow*: tick `publish`, and type the exact
   version into `confirm_version`. A mismatch aborts before anything uploads.

A PyPI version cannot be recalled — `yank` hides it but burns the number
forever — which is why the confirmation is a typed version rather than a
checkbox.

## What the pipeline checks first

- the tag matches `pyproject.toml`
- the version is not already on PyPI
- `twine check` passes, so a README PyPI would reject fails *before* the version
  is burned
- the built wheel installs into a clean venv and imports
- **the installed package's default `base_url` is
  `https://api.swfte.com/agents/v2/gateway`**

The last one exists because that default shipped wrong — it omitted `/agents`,
so every caller who took it got a bare nginx 403.
