"""Build a real wheel, install it in a new venv and run the installed API on loopback."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import venv

CHECK = r'''import json,threading,os
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import quote,unquote
from swfte import SwfteClient
from swfte.exceptions import InvalidRequestError
from pathlib import Path
import swfte,sys
assert Path(swfte.__file__).is_relative_to(Path(sys.prefix))
INPUT={'label':'workflow-wire','nested':{'enabled':True,'values':[1,'two',None]}}
seen=[]; bodies={}; executions={}
published={label:'PUBLISHED' for label in ['3','1.0.7','1.0.7-rc.2+build.09']}
os.environ.pop('SWFTE_CALLSITE_STACK',None)
class Handler(BaseHTTPRequestHandler):
 def reply(self):
  raw=self.rfile.read(int(self.headers.get("Content-Length") or 0));bodies[len(seen)]=json.loads(raw) if raw else None;seen.append((self.command,self.path,self.headers.get("X-Swfte-Callsite")))
  version=unquote(self.path.split("/versions/")[1].split("/")[0]) if "/versions/" in self.path else "live"
  status=200
  if self.headers.get("X-Workspace-Id")=="B" or ("/versions/" in self.path and published.get(version) not in ("PUBLISHED","DEPRECATED")):
   status=404;body={"error":"VERSION_NOT_PUBLISHED"}
  elif self.path.endswith("/status"):
   eid=self.path.split("/")[-2];body={"execution":{"executionId":eid,"status":"SUCCEEDED","outputData":{"marker":"snapshot-"+executions[eid]}}}
  else:
   eid="packed_"+str(len(executions));executions[eid]=version;body={"executionId":eid,"status":"PENDING","sessionId":"session","response":"ok","runId":"run"}
  raw=json.dumps(body).encode();self.send_response(status);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(raw)
 do_POST=reply
 do_GET=reply
 def log_message(self,*args):pass
server=ThreadingHTTPServer(("127.0.0.1",0),Handler);thread=threading.Thread(target=server.serve_forever,kwargs={"poll_interval":0.02},daemon=True);thread.start()
try:
 client=SwfteClient(api_key="packed-unit-key",api_base_url="http://127.0.0.1:"+str(server.server_port),workspace_id="A",max_retries=1)
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
 labels=["v3","v4","custom@v3:release","latest","5","01.0.7","1.0","1.0.7+","1.0.7-","3"]
 for label in labels: published.pop(label,None)
 for label in labels:
  route="/v2/workflows/wf_packed/versions/"+quote(label,safe="")+"/invoke"
  before=len(seen);old_executions=len(executions)
  for run in [lambda:client.workflows.invoke_version("wf_packed",label,callsite=id),lambda:client.workflows.invoke_version_and_wait("wf_packed",label,callsite=id,poll_interval=0.001)]:
   try: run()
   except Exception as error: assert error.status_code==404
   else: raise AssertionError("absent exact label was accepted")
  assert len(executions)==old_executions and seen[before:]==[("POST",route,id),("POST",route,id)]
  published[label]="PUBLISHED"
  assert client.workflows.invoke_version("wf_packed",label).execution_id
  assert seen[-1]==("POST",route,None)
  client.workflows.invoke_version("wf_packed",label,callsite=id)
  assert seen[-1]==("POST",route,id)
  assert client.workflows.invoke_version_and_wait("wf_packed",label,poll_interval=0.001).outputs=={"marker":"snapshot-"+label}
  assert seen[-2]==("POST",route,None)
  assert client.workflows.invoke_version_and_wait("wf_packed",label,callsite=id,poll_interval=0.001).outputs=={"marker":"snapshot-"+label}
  assert seen[-2]==("POST",route,id)
 published["draft-v3"]="DRAFT";old_executions=len(executions)
 foreign=SwfteClient(api_key="packed-unit-key",api_base_url="http://127.0.0.1:"+str(server.server_port),workspace_id="B",max_retries=1)
 for target,label in [(client,"draft-v3"),(client,"unknown-v3"),(foreign,"v3")]:
  try: target.workflows.invoke_version_and_wait("wf_packed",label,poll_interval=0.001)
  except Exception as error: assert error.status_code==404
  else: raise AssertionError("unpublished or foreign label was accepted")
 assert len(executions)==old_executions
 published["retired@v3:release"]="DEPRECATED"
 assert client.workflows.invoke_version_and_wait("wf_packed","retired@v3:release",poll_interval=0.001).outputs=={"marker":"snapshot-retired@v3:release"}
 for attribution in [id,None]:
  first=len(seen)
  client.workflows.execute("wf_packed",callsite=attribution)
  client.workflows.invoke("wf_packed",callsite=attribution)
  assert client.workflows.invoke_and_wait("wf_packed",callsite=attribution,poll_interval=0.001).outputs=={"marker":"snapshot-live"}
  client.agents.chat("ag_packed","hello",callsite=attribution)
  client.chatflows.start_session("cf_packed",callsite=attribution)
  client.chatflows.test("cf_packed",{},callsite=attribution)
  requests=seen[first:]
  assert len(requests)==7
  assert all(row[2]==attribution for row in requests if row[0]=="POST")
  assert all(row[2] is None for row in requests if row[0]=="GET")
 count=len(seen)
 for bad in ["","---._+:@",".","..","1.0.7/","1.0.7?x=1","1.0.7#x","../1.0.7","1.0.7%2Fextra","1.0.7\n","1.0.7\r","1.0.7\0"," v3","v3 ","v3\\extra","١.0.7","1.0.7+"+"a"*123]:
  for run in [lambda:client.workflows.invoke_version("wf_packed",bad),lambda:client.workflows.invoke_version_and_wait("wf_packed",bad)]:
   try: run()
   except InvalidRequestError: pass
   else: raise AssertionError("malformed String was accepted")
   assert len(seen)==count
 assert len(seen)==106 and all(row[2] is None for row in seen if row[1].endswith("/status"))
 boundary_start=len(seen);boundary_executions=len(executions)
 def entries(wf):
     return [lambda:client.workflows.execute(wf,INPUT),lambda:client.workflows.execute(wf,INPUT,skip_validation=True),
             lambda:client.workflows.execute(wf,INPUT,skip_validation=True,callsite=id),
             lambda:client.workflows.invoke(wf,INPUT),lambda:client.workflows.invoke(wf,INPUT,callsite=id),
             lambda:client.workflows.invoke_and_wait(wf,INPUT,poll_interval=0.001,callsite=id),
             lambda:client.workflows.invoke_version(wf,3,INPUT),lambda:client.workflows.invoke_version(wf,'1.0.7',INPUT,callsite=id),
             lambda:client.workflows.invoke_version_and_wait(wf,3,INPUT,poll_interval=0.001),
             lambda:client.workflows.invoke_version_and_wait(wf,'1.0.7',INPUT,poll_interval=0.001,callsite=id)]
 for wf in ['', '.', '..','../other','a/b','a\\b','a?x=1','a#x','a%2fother',' a','a ','a\n','a\r','a\0','é','a+b','a'*129,None,42,{}]:
     for run in entries(wf):
         try: run()
         except InvalidRequestError: pass
         else: raise AssertionError("unsafe workflow ID accepted")
     assert len(seen)==boundary_start and len(executions)==boundary_executions
 for wf in ['wf_shared','@:-','...','wf@release:v1','a'*128]:
     first=len(seen)
     for run in entries(wf): run()
     rows=seen[first:]
     assert all(bodies[first+i]==(INPUT if row[0]=='POST' else None) for i,row in enumerate(rows))
     prefix='/v2/workflows/'+quote(wf,safe='')
     posts=[row for row in rows if row[0]=='POST']
     assert [row[1] for row in posts] == [prefix+'/execute',prefix+'/execute?skipValidation=True',prefix+'/execute?skipValidation=True',prefix+'/invoke',prefix+'/invoke',prefix+'/invoke',prefix+'/versions/3/invoke',prefix+'/versions/1.0.7/invoke',prefix+'/versions/3/invoke',prefix+'/versions/1.0.7/invoke']
     assert [row[2] for row in posts] == [None,None,id,None,id,id,None,id,None,id]
     assert all(row[2] is None for row in rows if row[0]=='GET')
 print("SDK_PYTHON_PACKED_OK installed-wheel requests="+str(len(seen))+" semanticStrings=exact legacyStrings=exact-published-records unsafeStringTransportRequests=0")
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
