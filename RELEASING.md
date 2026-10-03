# Releasing `swfte-sdk`

Distribution name `swfte-sdk`, import name `swfte`, current version **1.2.0**.
Nothing has been published yet, so the first publish claims the name. The
`swfte` name is unregistered as well; register a placeholder for it after the
first release so nobody else can (dependency confusion).

## Owner setup (one time, only a person can do this)

1. **PyPI account** with 2FA (hardware key). No API token is needed or wanted.
2. **Pending trusted publisher** (PyPI, Your account, Publishing, "Add a new
   pending publisher"): project `swfte-sdk`, owner `SwfteAI`, repository
   `swfte-python`, workflow `release.yml`, environment `pypi-publish-prod`.
   The first successful publish creates the project.
3. **Delete the old token**: remove the repository secret `PYPI_API_TOKEN` and
   revoke the token in PyPI account settings. The workflow no longer reads it.
4. **GitHub environment `pypi-publish-prod`**: deployment branches = `main` only;
   required reviewers = team `release-approvers` with at least two people who are
   not the person dispatching; turn on "prevent self-review".
5. **Branch protection on `main`** (pull request required, no force pushes).
6. After the first publish, register the placeholder project `swfte`.

Note: the environment is deliberately still `pypi-publish-prod` (it already
carries the required reviewers). The trusted publisher must be registered with
that exact environment name; a different name would make the upload fail.

## Publish procedure

1. Merge the release commit to `main`. `pyproject.toml` `version`, `swfte/_version.py`
   and the dated `CHANGELOG.md` heading must agree (tests enforce this).
2. Confirm the version is free:
   `curl -s -o /dev/null -w '%{http_code}' https://pypi.org/pypi/swfte-sdk/<version>/json`
   must print `404`.
3. Optional: `git tag v<version> && git push origin v<version>`. A tag push only
   builds and verifies (it never publishes); the tag must equal the source
   version or preflight fails.
4. Actions, **Release**, *Run workflow* on `main`: tick `publish` and type the
   exact version into `confirm_version`. A mismatch aborts. A dispatch from any
   other branch does not reach the publish job.
5. An approver from `release-approvers` approves the paused `publish` job. It
   uploads through Trusted Publishing; then the separate `github-release` job
   creates the GitHub Release for the built commit.
6. Verify in a fresh venv: `pip install swfte-sdk==<version>`,
   `python -c "import swfte; print(swfte.__version__)"`; check the PyPI page
   shows the Trusted Publisher attestation and correct README links.

A PyPI version cannot be recalled (`yank` hides it but burns the number
forever), which is why the confirmation is a typed version.

## What the pipeline checks before upload

- the tag matches `pyproject.toml`; the version is not already on PyPI
- `twine check` passes on sdist and wheel
- the built wheel installs into a clean venv and imports
- the installed package's default `base_url` is
  `https://api.swfte.com/agents/v2/gateway`

The test suite additionally checks, on the built wheel, that every module parses
and imports and that the version is consistent (`tests/packaging`).

## Local build check

    python -m build && python -m twine check dist/* && SWFTE_WHEEL=$(ls dist/*.whl) pytest tests/packaging
