"""Tests on the BUILT artefacts. Run after `python -m build` (dist/), or set SWFTE_WHEEL."""

import ast
import glob
import os
import pathlib
import re
import subprocess
import sys
import zipfile
from email.parser import Parser

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _wheel() -> pathlib.Path:
    explicit = os.environ.get("SWFTE_WHEEL")
    found = [pathlib.Path(explicit)] if explicit else [pathlib.Path(p) for p in glob.glob(str(ROOT / "dist" / "*.whl"))]
    assert len(found) == 1, f"expected exactly one built wheel (run `python -m build` first), got {found}"
    return found[0]


@pytest.fixture(scope="module")
def extracted(tmp_path_factory):
    dest = tmp_path_factory.mktemp("wheel")
    with zipfile.ZipFile(_wheel()) as z:
        z.extractall(dest)
        names = z.namelist()
    return dest, names


def _pyproject_version() -> str:
    m = re.search(r'^version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M)
    assert m
    return m.group(1)


def test_every_module_in_the_wheel_parses_as_python_38(extracted):
    """Catches a syntax error like the stray quote that used to be in swfte/analytics.py."""
    dest, names = extracted
    py = [n for n in names if n.endswith(".py")]
    assert py
    for n in py:
        ast.parse((dest / n).read_text(), filename=n, feature_version=8)


def test_every_module_in_the_wheel_imports(extracted):
    dest, names = extracted
    mods = []
    for n in names:
        if n.endswith(".py") and n.startswith("swfte/"):
            mod = n[:-3].replace("/", ".")
            mods.append(mod[: -len(".__init__")] if mod.endswith(".__init__") else mod)
    assert "swfte" in mods and "swfte.analytics" in mods and "swfte.chat" in mods
    code = (
        "import importlib,sys\n"
        f"sys.path.insert(0, {str(dest)!r})\n"
        "import swfte\n"
        f"assert swfte.__file__.startswith({str(dest)!r}), swfte.__file__\n"
        "bad=[]\n"
        "for m in sys.argv[1:]:\n"
        "    try: importlib.import_module(m)\n"
        "    except Exception as e: bad.append((m, repr(e)))\n"
        "assert not bad, bad\n"
        "print('ALL_IMPORTED', len(sys.argv)-1)\n"
    )
    out = subprocess.run([sys.executable, "-c", code, *mods], capture_output=True, text=True, cwd=str(dest))
    assert out.returncode == 0, out.stdout + out.stderr
    assert "ALL_IMPORTED" in out.stdout


def test_wheel_has_no_shadow_module_and_ships_py_typed(extracted):
    _, names = extracted
    assert "swfte/analytics.py" not in names
    assert "swfte/analytics/__init__.py" in names
    assert "swfte/py.typed" in names


def test_wheel_preserves_mit_license_and_python_38_minimum(extracted):
    dest, names = extracted
    metadata_name = next(n for n in names if n.endswith(".dist-info/METADATA"))
    metadata = Parser().parsestr((dest / metadata_name).read_text())
    assert metadata["Name"] == "swfte-sdk"
    assert metadata["Requires-Python"] == ">=3.8"
    assert "MIT License" in metadata["License"]
    license_names = [n for n in names if n.endswith("/LICENSE") and ".dist-info/" in n]
    assert len(license_names) == 1
    assert (dest / license_names[0]).read_bytes() == (ROOT / "LICENSE").read_bytes()


def test_wheel_ships_no_tests_examples_or_env_files(extracted):
    _, names = extracted
    for n in names:
        assert not n.startswith(("tests/", "examples/", "docs/")), n
        assert ".env" not in n, n


def test_version_is_consistent_everywhere(extracted):
    dest, names = extracted
    v = _pyproject_version()
    assert v == "1.2.0"
    meta = next(n for n in names if n.endswith(".dist-info/METADATA"))
    assert f"\nVersion: {v}\n" in "\n" + (dest / meta).read_text()
    assert _wheel().name.startswith(f"swfte_sdk-{v}-")
    code = f"import sys; sys.path.insert(0, {str(dest)!r}); import swfte; print(swfte.__version__)"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(dest))
    assert out.stdout.strip() == v, out.stdout + out.stderr


def test_changelog_has_dated_section_for_the_version():
    text = (ROOT / "CHANGELOG.md").read_text()
    assert re.search(rf"^## {re.escape(_pyproject_version())} - \d{{4}}-\d{{2}}-\d{{2}}$", text, re.M)
