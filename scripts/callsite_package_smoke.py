"""Build a real wheel, install it in a new venv and run the installed API on loopback."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import venv

CHECK = r'''import json,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import unquote
from swfte import SwfteClient
from swfte.exceptions import InvalidRequestError
from pathlib import Path
import swfte,sys
assert Path(swfte.__file__).is_relative_to(Path(sys.prefix))
seen=[]; executions={}
class Handler(BaseHTTPRequestHandler):
 def reply(self):
  self.rfile.read(int(self.headers.get("Content-Length") or 0));seen.append((self.command,self.path,self.headers.get("X-Swfte-Callsite")))
  if self.path.endswith("/status"):
   eid=self.path.split("/")[-2];body={"execution":{"executionId":eid,"status":"SUCCEEDED","outputData":{"marker":"snapshot-"+executions[eid]}}}
  else:
   version=unquote(self.path.split("/versions/")[1].split("/")[0]) if "/versions/" in self.path else "live"
   eid="packed_"+str(len(executions));executions[eid]=version;body={"executionId":eid,"status":"PENDING"}
  raw=json.dumps(body).encode();self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(raw)
 do_POST=reply
 do_GET=reply
 def log_message(self,*args):pass
server=ThreadingHTTPServer(("127.0.0.1",0),Handler);thread=threading.Thread(target=server.serve_forever,kwargs={"poll_interval":0.02},daemon=True);thread.start()
try:
 client=SwfteClient(api_key="packed-unit-key",api_base_url="http://127.0.0.1:"+str(server.server_port))
 id="cs_"+"a"*24
 integer=client.workflows.invoke_version_and_wait("wf_packed",3,callsite=id,poll_interval=0.001)
 assert integer.outputs=={"marker":"snapshot-3"}
 assert seen[-2]==("POST","/v2/workflows/wf_packed/versions/3/invoke",id) and seen[-1][2] is None
 client.workflows.invoke_version("wf_packed","1.0.7")
 assert seen[-1]==("POST","/v2/workflows/wf_packed/versions/1.0.7/invoke",None)
 semantic=client.workflows.invoke_version_and_wait("wf_packed","1.0.7",callsite=id,poll_interval=0.001)
 assert semantic.outputs=={"marker":"snapshot-1.0.7"}
 build="1.0.7-rc.2+build.09"
 built=client.workflows.invoke_version_and_wait("wf_packed",build,callsite=id,poll_interval=0.001)
 assert built.outputs=={"marker":"snapshot-"+build}
 assert seen[-2]==("POST","/v2/workflows/wf_packed/versions/1.0.7-rc.2%2Bbuild.09/invoke",id)
 count=len(seen)
 for bad in ["5","1.0.7/","1.0.7?x=1","1.0.7#x","../1.0.7","1.0.7%2Fextra","1.0.7\n","1.0.7+"+"a"*123]:
  for run in [lambda:client.workflows.invoke_version("wf_packed",bad),lambda:client.workflows.invoke_version_and_wait("wf_packed",bad)]:
   try: run()
   except InvalidRequestError: pass
   else: raise AssertionError("malformed String was accepted")
   assert len(seen)==count
 assert len(seen)==7 and all(row[2] is None for row in seen if row[1].endswith("/status"))
 print("SDK_PYTHON_PACKED_OK installed-wheel requests="+str(len(seen))+" semanticStrings=exact badStringTransportRequests=0")
finally:server.shutdown();server.server_close();thread.join()
'''

root=Path.cwd()
with tempfile.TemporaryDirectory(prefix='swfte-python-packed-') as directory:
    temp=Path(directory); wheels=temp/'wheels'; wheels.mkdir()
    subprocess.run([sys.executable,'-m','pip','wheel','--no-deps','--wheel-dir',str(wheels),str(root)],check=True)
    wheel=next(wheels.glob('swfte_sdk-*.whl'))
    print('SDK_PYTHON_WHEEL_SHA256 '+hashlib.sha256(wheel.read_bytes()).hexdigest(),flush=True)
    consumer=temp/'consumer'; venv.EnvBuilder(with_pip=True,symlinks=False).create(consumer)
    python=consumer/'bin'/'python'
    subprocess.run([str(python),'-m','pip','install',str(wheel)],cwd=temp,check=True)
    check=temp/'check.py';check.write_text(CHECK)
    subprocess.run([str(python),str(check)],cwd=temp,check=True)
