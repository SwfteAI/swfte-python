
import json, threading, os, tempfile, importlib.util
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote
from swfte import SwfteClient
from swfte.exceptions import InvalidRequestError

def exercise():
    seen=[];forwarded=[];redirect=[0];id='cs_'+'a'*24;explicit='cs_'+'c'*24
    class Handler(BaseHTTPRequestHandler):
        def reply(self):
            raw=self.rfile.read(int(self.headers.get('Content-Length') or 0))
            rows=forwarded if self.server.canary else seen
            rows.append((self.command,self.path,self.headers.get('X-Swfte-Callsite'),json.loads(raw) if raw else None,self.headers.get('Authorization')))
            status=redirect[0] if redirect[0] and not self.server.canary else 200
            if 'missing' in self.path or self.headers.get('X-Workspace-Id')=='B':status=404
            if 'native-unavailable' in self.path:status=501
            self.send_response(status)
            if 300<=status<400:self.send_header('Location',canary_base+'/capture')
            self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps({'response':'ok','sessionId':'cfs_'+'a'*32,'runId':'fixture-only'}).encode())
        do_POST=reply;do_GET=reply
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.canary=False
    canary=ThreadingHTTPServer(('127.0.0.1',0),Handler);canary.canary=True
    canary_base='http://127.0.0.1:'+str(canary.server_port)
    threads=[threading.Thread(target=s.serve_forever,kwargs={'poll_interval':0.02},daemon=True) for s in [server,canary]]
    for thread in threads:thread.start()
    c=SwfteClient(api_key='unit-only-key',api_base_url='http://127.0.0.1:'+str(server.server_port),workspace_id='A',max_retries=1)
    keys=['SWFTE_CALLSITE_STACK','SWFTE_CODEMAP_CALLERS','SWFTE_ENV','ENV','PYTHON_ENV'];saved={k:os.environ.get(k) for k in keys}
    def entries(value,callsite=None):
        return [lambda:c.agents.chat(value,'hello',user_id='legacy user',conversation_id='conversation',callsite=callsite),lambda:c.chatflows.start_session(value,channel='WEB',context={'key':'value'},callsite=callsite),lambda:c.chatflows.test(value,{'input':'value'},callsite=callsite)]
    def readers(value):return [lambda:c.chatflows.get_session(value),lambda:c.chatflows.list_sessions(value),lambda:c.chatflows.stats(value)]
    def refused(run,kind=Exception):
        try:run()
        except kind:return
        raise AssertionError('expected refusal')
    try:
        os.environ.pop('SWFTE_CALLSITE_STACK',None)
        for value in ['', '.', '..','a\n','a\r','a\0','a\x7f','\ud800','\udc00',None,42,{}]:
            for run in entries(value,id)+readers(value):refused(run,InvalidRequestError)
            assert seen==[]
        for value in ['legacy /\\?#%2e: @é😀','...','@:-','system-agent','avima-runtime-agent','a'*256]:
            for callsite in [None,id,'invalid']:
                first=len(seen)
                for run in entries(value,callsite):run()
                component=quote(value,safe='');header=id if callsite==id else None
                assert [r[:3] for r in seen[first:]]==[('POST','/v1/agents/'+component+'/chat/legacy%20user',header),('POST','/v2/chatflows/'+component+'/sessions',header),('POST','/v2/chatflows/builder/'+component+'/test',header)]
                assert seen[first][3]=={'message':'hello','conversationId':'conversation'}
                assert seen[first+1][3]=={'channel':'WEB','context':{'key':'value'}}
                assert seen[first+2][3]=={'input':'value'}
        for user in [None,'',False,0,{},[]]:c.agents.chat('agent','hello',user_id=user);assert seen[-1][1]=='/v1/agents/agent/chat/sdk-user'
        for user in ['.','..','a\n','\ud800',42,{'legacy':'value'}]:
            first=len(seen);refused(lambda:c.agents.chat('agent','hello',user_id=user),InvalidRequestError);assert len(seen)==first
        user='opaque /\\?#%é😀';c.agents.chat('agent','hello',user_id=user);assert seen[-1][1]=='/v1/agents/agent/chat/'+quote(user,safe='')
        for value in ['cfs_'+'a'*32,'avima-session-cfs_'+'b'*32,'legacy session /%é']:
            first=len(seen)
            for run in readers(value):run()
            component=quote(value,safe='')
            assert [r[:4] for r in seen[first:]]==[('GET','/v2/chatflows/sessions/'+component,None,None),('GET','/v2/chatflows/'+component+'/sessions?page=0&size=20',None,None),('GET','/v2/chatflows/'+component+'/stats',None,None)]
            paged=len(seen);c.chatflows.list_sessions(value,page=2,size=7)
            assert [r[:4] for r in seen[paged:]]==[('GET','/v2/chatflows/'+component+'/sessions?page=2&size=7',None,None)]
        for context in [None,{}]:
            fallback=len(seen);c.chatflows.start_session('flow',context=context)
            assert seen[fallback][3]=={'channel':'WEB'}
        for payload in [None,{}]:
            fallback=len(seen);c.chatflows.test('flow',payload)
            assert seen[fallback][3]==payload
        with tempfile.TemporaryDirectory(prefix='nonworkflow-callers-') as directory:
            base=Path(directory).resolve();entries_map={};modules=[]
            for name,callsite in [('a',id),('b','cs_'+'b'*24)]:
                file=base/(name+'.py');file.write_text("def run(c,callsite=None):\n    c.agents.chat('agent','hello',callsite=callsite)\n    c.chatflows.start_session('flow',callsite=callsite)\n    c.chatflows.test('flow',{},callsite=callsite)\n")
                for line in [2,3,4]:entries_map[name+'.py:'+str(line)]=callsite
                spec=importlib.util.spec_from_file_location('nonworkflow_'+name,file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);modules.append(module)
            mapfile=base/'callers.json';mapfile.write_text(json.dumps({'version':1,'root':str(base),'entries':entries_map}));os.environ['SWFTE_CODEMAP_CALLERS']=str(mapfile)
            def callers(callsite=None):
                for module in modules:module.run(c,callsite)
            first=len(seen);callers();assert all(r[2] is None for r in seen[first:])
            os.environ['SWFTE_CALLSITE_STACK']='1'
            for key in ['SWFTE_ENV','ENV','PYTHON_ENV']:os.environ.pop(key,None)
            first=len(seen);callers();assert [r[2] for r in seen[first:]]==[id,id,id,'cs_'+'b'*24,'cs_'+'b'*24,'cs_'+'b'*24]
            first=len(seen);callers(explicit);assert all(r[2]==explicit for r in seen[first:])
            first=len(seen);callers('invalid');assert all(r[2] is None for r in seen[first:])
            for key in ['SWFTE_ENV','ENV','PYTHON_ENV']:
                os.environ[key]='production';first=len(seen);callers();assert all(r[2] is None for r in seen[first:])
                first=len(seen);callers(explicit);assert all(r[2]==explicit for r in seen[first:]);os.environ.pop(key)
            first=len(seen)
            for run in readers('cfs_read'):run()
            assert all(r[2] is None for r in seen[first:])
        for status in [301,302,303,307,308]:
            redirect[0]=status
            for run in entries('flow',id)+readers('cfs_read'):refused(run)
            assert forwarded==[]
        redirect[0]=0
        for run in entries('missing',id):refused(run)
        refused(lambda:c.chatflows.test('native-unavailable',{}))
        foreign=SwfteClient(api_key='unit-only-key',api_base_url='http://127.0.0.1:'+str(server.server_port),workspace_id='B',max_retries=1)
        refused(lambda:foreign.agents.chat('agent','hello'));refused(lambda:foreign.chatflows.start_session('flow'));refused(lambda:foreign.chatflows.test('flow',{}));assert len(seen)>0
        return len(seen)
    finally:
        for key,value in saved.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value
        for s in [server,canary]:s.shutdown();s.server_close()
        for thread in threads:thread.join()

def test_nonworkflow_boundary_real_wire():
    assert exercise()>0

if __name__=='__main__':
    import sys,subprocess
    if '--unit-gate' in sys.argv:
        import xml.etree.ElementTree as ET
        with tempfile.TemporaryDirectory(prefix='nonworkflow-unit-gate-') as directory:
            report=Path(directory)/'pytest.xml'
            result=subprocess.run([sys.executable,'-m','pytest',str(Path(__file__).resolve()),'-q','--junitxml='+str(report)])
            if result.returncode:sys.exit(result.returncode)
            suites=ET.parse(report).getroot().iter('testsuite')
            counts={key:0 for key in ['tests','failures','errors','skipped']}
            for suite in suites:
                for key in counts:counts[key]+=int(suite.attrib.get(key,0))
            if counts!={'tests':1,'failures':0,'errors':0,'skipped':0}:raise AssertionError('nonworkflow unit gate requires one actual passing test and no skips')
            print('SDK_PYTHON_NONWORKFLOW_UNIT_OK '+json.dumps(counts),flush=True)
    else:
        import swfte
        assert Path(swfte.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
        requests=exercise();print('SDK_PYTHON_NONWORKFLOW_PACKED_OK requests='+str(requests),flush=True)
