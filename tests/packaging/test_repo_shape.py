"""Static checks on files that publishing depends on (workflow, README, metadata)."""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
RELEASE = (ROOT / ".github/workflows/release.yml").read_text()
CI = (ROOT / ".github/workflows/ci.yml").read_text()


def test_workflows_do_not_reference_the_pypi_token():
    assert "PYPI_API_TOKEN" not in RELEASE
    assert not re.search(r"secrets\.PYPI", RELEASE)
    assert not re.search(r"^\s*password:", RELEASE, re.M)


def test_publish_uses_oidc_and_environment():
    pub = RELEASE[RELEASE.index("\n  publish:") : RELEASE.index("\n  github-release:")]
    assert "id-token: write" in pub
    assert "name: pypi-publish-prod" in pub
    assert "github.ref == 'refs/heads/main'" in pub
    assert "contents: write" not in pub
    assert "softprops" not in pub


def test_github_release_step_is_a_separate_job_without_oidc():
    rel = RELEASE[RELEASE.index("\n  github-release:") :]
    assert "softprops/action-gh-release" in rel
    assert "id-token" not in rel
    assert "target_commitish: ${{ github.sha }}" in rel


def test_every_action_is_pinned_to_a_full_sha_with_a_tag_comment():
    for text in (RELEASE, CI):
        uses = re.findall(r"^\s*(?:-\s+)?uses:\s*(\S+)(.*)", text, re.M)
        assert uses
        for ref, rest in uses:
            assert re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", ref), ref
            assert re.match(r"\s*# v\d", rest), (ref, rest)


def test_pr_ci_has_explicit_read_only_contents_permission():
    assert re.search(r"^permissions:\n  contents: read\n", CI, re.M)
    assert not re.search(r"\b(?:contents|id-token|actions|packages): write\b", CI)


def test_readme_links_point_at_swfte_sdk_not_swfte():
    readme = (ROOT / "README.md").read_text()
    assert "pypi.org/project/swfte/" not in readme
    assert "img.shields.io/pypi/v/swfte.svg" not in readme
    assert "pypi.org/project/swfte-sdk/" in readme
    assert "pip install swfte " not in readme and "pip install swfte\n" not in readme


def test_requests_floor_is_patched():
    text = (ROOT / "pyproject.toml").read_text()
    assert '"requests>=2.32.4"' in text


def test_urllib3_floor_is_patched_and_python_39_is_not_advertised():
    """GHSA-vxq7-64xx-v4gw is fixed only in urllib3 2.8.0, which needs Python >= 3.10."""
    text = (ROOT / "pyproject.toml").read_text()
    assert '"urllib3>=2.8.0"' in text
    assert "Programming Language :: Python :: 3.8" not in text
    assert "Programming Language :: Python :: 3.9" not in text
    assert "Programming Language :: Python :: 3.10" in text


def test_build_contract_and_ci_advertise_python_310_floor():
    text = (ROOT / "pyproject.toml").read_text()
    assert '"setuptools>=68.0.0,<77"' in text
    assert 'license = {file = "LICENSE"}' in text
    assert not re.search(r"^license-files\s*=", text, re.M)
    assert 'requires-python = ">=3.10"' in text
    assert "python-version: ['3.10', '3.11'" in CI
    assert "'3.8'" not in CI and "'3.9'" not in CI
    assert "python -m build" in CI
    assert "python -m twine check" in CI


def test_shadowing_module_is_gone_and_nothing_imports_it():
    assert not (ROOT / "swfte/analytics.py").exists()
    assert (ROOT / "swfte/analytics/__init__.py").exists()
    assert (ROOT / "swfte/py.typed").exists()
