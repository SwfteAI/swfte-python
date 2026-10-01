"""Build a real wheel, install it in a new venv and run the installed API on loopback."""
from pathlib import Path
import subprocess
import sys
import tempfile
import venv

CHECK = '''import json,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from swfte import SwfteClient
from pathlib import Path
import swfte,sys
assert Path(swfte.__file__).is_relative_to(Path(sys.prefix))
seen=[]
class Handler(BaseHTTPRequestHandler):
 def reply(self):
  self.rfile.read(int(self.headers.get("Content-Length") or 0));seen.append((self.path,self.headers.get("X-Swfte-Callsite")))
  body={"execution":{"executionId":"packed","status":"SUCCEEDED","outputData":{"marker":"snapshot-3"}}} if self.path.endswith("/status") else {"executionId":"packed","status":"PENDING"}
  raw=json.dumps(body).encode();self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(raw)
 do_POST=reply
 do_GET=reply
 def log_message(self,*args):pass
server=ThreadingHTTPServer(("127.0.0.1",0),Handler);thread=threading.Thread(target=server.serve_forever,kwargs={"poll_interval":0.02},daemon=True);thread.start()
try:
 client=SwfteClient(api_key="packed-unit-key",api_base_url="http://127.0.0.1:"+str(server.server_port))
 result=client.workflows.invoke_version_and_wait("wf_packed",3,callsite="cs_"+"a"*24,poll_interval=0.001)
 assert result.outputs=={"marker":"snapshot-3"}
 assert seen==[("/v2/workflows/wf_packed/versions/3/invoke","cs_"+"a"*24),("/v2/workflows/executions/packed/status",None)]
 print("SDK_PYTHON_PACKED_OK installed-wheel requests="+str(len(seen)))
finally:server.shutdown();server.server_close();thread.join()
'''

root=Path.cwd()
with tempfile.TemporaryDirectory(prefix='swfte-python-packed-') as directory:
    temp=Path(directory); wheels=temp/'wheels'; wheels.mkdir()
    subprocess.run([sys.executable,'-m','pip','wheel','--no-deps','--wheel-dir',str(wheels),str(root)],check=True)
    wheel=next(wheels.glob('swfte_sdk-*.whl'))
    consumer=temp/'consumer'; venv.EnvBuilder(with_pip=True,symlinks=False).create(consumer)
    python=consumer/'bin'/'python'
    subprocess.run([str(python),'-m','pip','install',str(wheel)],cwd=temp,check=True)
    check=temp/'check.py';check.write_text(CHECK)
    subprocess.run([str(python),str(check)],cwd=temp,check=True)
