from pathlib import Path
import hashlib,subprocess,sys,tempfile,venv
root=Path.cwd()
with tempfile.TemporaryDirectory(prefix='sdk-nonworkflow-package-') as directory:
    temp=Path(directory);wheels=temp/'wheels';wheels.mkdir()
    subprocess.run([sys.executable,'-m','pip','wheel','--no-deps','--wheel-dir',str(wheels),str(root)],check=True)
    wheel=next(wheels.glob('swfte_sdk-*.whl'));print('SDK_PYTHON_NONWORKFLOW_WHEEL_SHA256 '+hashlib.sha256(wheel.read_bytes()).hexdigest(),flush=True)
    consumer=temp/'consumer';venv.EnvBuilder(with_pip=True,symlinks=False).create(consumer)
    python=consumer/'bin'/'python';subprocess.run([str(python),'-m','pip','install',str(wheel)],cwd=temp,check=True)
    check=temp/'check.py';check.write_text((root/'tests/unit/test_nonworkflow_route_boundary.py').read_text())
    subprocess.run([str(python),str(check)],cwd=temp,check=True)
