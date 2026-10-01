"""Exercise actual wire branches and redirect boundaries; server snapshot fixtures are not live backend credit."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest
from swfte import SwfteClient

ID = 'cs_' + 'a' * 24

class Handler(BaseHTTPRequestHandler):
    def reply(self):
        self.rfile.read(int(self.headers.get('Content-Length') or 0))
        self.server.seen.append((self.command,self.path,self.headers.get('X-Swfte-Callsite')))
        if self.server.redirect:
            self.send_response(302); self.send_header('Location',self.server.redirect); self.end_headers(); return
        if self.headers.get('X-Workspace-Id') == 'B' or '/versions/9/' in self.path:
            status,body=404,{'error':'VERSION_NOT_PUBLISHED'}
        elif self.path.endswith('/status'):
            version=self.server.executions[self.path.split('/')[-2]]
            status,body=200,{'execution':{'executionId':'ex','status':'SUCCEEDED','workflowVersion':version,'outputData':{'marker':'snapshot-'+str(version)}}}
        else:
            version=int(self.path.split('/versions/')[1].split('/')[0]) if '/versions/' in self.path else self.server.live
            eid='ex_'+str(len(self.server.executions)); self.server.executions[eid]=version
            status,body=200,{'executionId':eid,'status':'PENDING','sessionId':'session','response':'ok','runId':'run'}
        raw=json.dumps(body).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    do_POST=reply
    do_GET=reply
    def log_message(self,*args): pass

@pytest.fixture
def server(monkeypatch):
    monkeypatch.delenv('SWFTE_CALLSITE_STACK',raising=False)
    srv=ThreadingHTTPServer(('127.0.0.1',0),Handler); srv.seen=[]; srv.executions={}; srv.live=3; srv.redirect=None
    thread=threading.Thread(target=srv.serve_forever,kwargs={'poll_interval':0.02},daemon=True); thread.start()
    yield srv
    srv.shutdown(); srv.server_close(); thread.join()

def client(server,workspace='A'):
    base='http://127.0.0.1:'+str(server.server_port)
    return SwfteClient(api_key='unit-test-key',base_url=base,api_base_url=base,workspace_id=workspace,max_retries=1)

def test_pin_survives_promotion_with_post_only_attribution_and_404_refusal(server):
    c=client(server); server.live=4
    pinned=c.workflows.invoke_version_and_wait('wf_shared',3,callsite=ID,poll_interval=0.001)
    live=c.workflows.invoke_and_wait('wf_shared',poll_interval=0.001)
    assert pinned.outputs == {'marker':'snapshot-3'} and live.outputs == {'marker':'snapshot-4'}
    assert server.seen[0][1:] == ('/v2/workflows/wf_shared/versions/3/invoke',ID)
    assert all(x[2] is None for x in server.seen if x[1].endswith('/status'))
    for target,version in [(c,9),(client(server,'B'),3)]:
        with pytest.raises(Exception) as caught: target.workflows.invoke_version('wf_shared',version)
        assert caught.value.status_code == 404
    assert sum(x[1]=='/v2/workflows/wf_shared/invoke' for x in server.seen)==1

def test_invalid_pins_never_call_transport_and_invalid_id_is_omitted(server):
    c=client(server)
    for bad in [0,-1,1.5,True,None,'3',float('nan'),2147483648]:
        with pytest.raises(Exception): c.workflows.invoke_version('wf_shared',bad)
    assert server.seen == []
    c.workflows.invoke_version('wf /shared',3,callsite=ID+'\n')
    assert server.seen[0][1] == '/v2/workflows/wf%20%2Fshared/versions/3/invoke' and server.seen[0][2] is None

def test_all_artifact_runtime_branches_and_default_off(server):
    c=client(server)
    c.workflows.execute('wf_shared',callsite=ID); c.workflows.invoke('wf_shared',callsite=ID)
    c.workflows.invoke_version('wf_shared',3,callsite=ID); c.agents.chat('ag_shared','hello',callsite=ID)
    c.chatflows.start_session('cf_shared',callsite=ID); c.chatflows.test('cf_shared',{},callsite=ID)
    assert len(server.seen)==6 and all(x[2]==ID for x in server.seen)
    c.chatflows.test('cf_shared',{}); assert server.seen[-1][2] is None

def test_real_redirect_never_forwards_to_second_listener(server):
    canary=ThreadingHTTPServer(('127.0.0.1',0),Handler); canary.seen=[]; canary.executions={}; canary.live=3; canary.redirect=None
    thread=threading.Thread(target=canary.serve_forever,kwargs={'poll_interval':0.02},daemon=True); thread.start()
    try:
        server.redirect='http://127.0.0.1:'+str(canary.server_port)+'/canary'
        c=client(server)
        for run in [lambda:c.workflows.invoke_version('wf_shared',3,callsite=ID),lambda:c.workflows.execute('wf_shared',callsite=ID),lambda:c.agents.chat('ag_shared','hello',callsite=ID),lambda:c.chatflows.test('cf_shared',{},callsite=ID)]:
            with pytest.raises(Exception): run()
        assert canary.seen == []
    finally: canary.shutdown(); canary.server_close(); thread.join()
