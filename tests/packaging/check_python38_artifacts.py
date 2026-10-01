"""Driver-only Python3.8 wheel/sdist builds and fresh installed-consumer proof.

Run with a real Python3.8 interpreter that has the build frontend installed.
This script installs/builds in isolated scratch environments and may resolve
dependencies; it is not invoked by the source-only repair agent.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from email.parser import Parser
import zipfile


ROOT = Path(__file__).resolve().parents[2]


def run(args, cwd, env=None):
    subprocess.run(args, cwd=str(cwd), env=env, check=True, timeout=300)


def main():
    if sys.version_info[:2] != (3, 8):
        raise SystemExit("PY38_REQUIRED: this proof cannot run on a newer interpreter")
    with tempfile.TemporaryDirectory(prefix="swfte-py38-artifacts-") as scratch:
        temp = Path(scratch)
        dist = temp / "dist"
        run([sys.executable, "-m", "build", "--wheel", "--sdist", "--outdir", str(dist), str(ROOT)], temp)
        wheels = list(dist.glob("*.whl"))
        sdists = list(dist.glob("*.tar.gz"))
        assert len(wheels) == len(sdists) == 1, "fresh build must produce exactly one wheel and sdist"
        wheel, sdist = wheels[0], sdists[0]
        with zipfile.ZipFile(wheel) as archive:
            metadata_path = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
            metadata = Parser().parsestr(archive.read(metadata_path).decode())
            licenses = [n for n in archive.namelist() if ".dist-info/" in n and n.endswith("/LICENSE")]
            assert len(licenses) == 1
            assert archive.read(licenses[0]) == (ROOT / "LICENSE").read_bytes()
        assert metadata["Name"] == "swfte-sdk"
        assert metadata["Requires-Python"] == ">=3.8"
        assert "MIT License" in metadata["License"]
        with tarfile.open(sdist) as archive:
            licenses = [m for m in archive.getmembers() if m.name.endswith("/LICENSE") and m.isfile()]
            assert len(licenses) == 1
            assert archive.extractfile(licenses[0]).read() == (ROOT / "LICENSE").read_bytes()
            info = next(m for m in archive.getmembers() if m.name.count("/") == 1 and m.name.endswith("/PKG-INFO"))
            sdist_metadata = Parser().parsestr(archive.extractfile(info).read().decode())
            assert sdist_metadata["Name"] == "swfte-sdk"
            assert sdist_metadata["Requires-Python"] == ">=3.8"
            assert "MIT License" in sdist_metadata["License"]
        consumer_check = """
import importlib, importlib.metadata, os, pkgutil, sys
import swfte
assert sys.version_info[:2] == (3, 8)
assert os.path.commonpath([sys.prefix, swfte.__file__]) == sys.prefix, swfte.__file__
assert importlib.metadata.version('swfte-sdk') == swfte.__version__ == '1.2.0'
modules = list(pkgutil.walk_packages(swfte.__path__, swfte.__name__ + '.'))
assert modules
for module in modules: importlib.import_module(module.name)
metadata = importlib.metadata.metadata('swfte-sdk')
assert metadata['Requires-Python'] == '>=3.8'
assert 'MIT License' in metadata['License']
print('PY38_INSTALLED_MODULES_IMPORTED', len(modules))
"""
        for name, artifact in [("wheel", wheel), ("sdist", sdist)]:
            consumer = temp / (name + "-consumer")
            run([sys.executable, "-m", "venv", str(consumer)], temp)
            executable = consumer / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            run([str(executable), "-m", "pip", "install", "--no-cache-dir", str(artifact)], temp)
            run([str(executable), "-I", "-c", consumer_check], temp)
        print("PY38_WHEEL_SDIST_INSTALL_PASSED", json.dumps({
            "interpreter": sys.version,
            "wheel": hashlib.sha256(wheel.read_bytes()).hexdigest(),
            "sdist": hashlib.sha256(sdist.read_bytes()).hexdigest(),
        }, sort_keys=True))


if __name__ == "__main__":
    main()
