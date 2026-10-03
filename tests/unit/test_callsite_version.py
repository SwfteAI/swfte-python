"""Exercise actual wire branches and redirect boundaries; server snapshot fixtures are not live backend credit."""
import json
import sys
from pathlib import Path
if __name__ == "__main__" and sys.argv[1:] == ["--unit-gate"]:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import importlib.util
import threading
from urllib.parse import quote, unquote
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest
from swfte import SwfteClient, _callsite
from swfte.exceptions import InvalidRequestError

INPUT={'label':'workflow-wire','nested':{'enabled':True,'values':[1,'two',None]}}
ID = 'cs_' + 'a' * 24

class Handler(BaseHTTPRequestHandler):
    def reply(self):
        raw=self.rfile.read(int(self.headers.get('Content-Length') or 0))
        self.server.bodies[len(self.server.seen)]=json.loads(raw) if raw else None
        self.server.seen.append((self.command,self.path,self.headers.get('X-Swfte-Callsite')))
        if self.server.redirect:
            self.send_response(302); self.send_header('Location',self.server.redirect); self.end_headers(); return
        segment=unquote(self.path.split('/versions/')[1].split('/')[0]) if '/versions/' in self.path else None
        if self.headers.get('X-Workspace-Id') == 'B' or (segment is not None and self.server.published.get(segment) not in ('PUBLISHED','DEPRECATED')):
            status,body=404,{'error':'VERSION_NOT_PUBLISHED'}
        elif self.path.endswith('/status'):
            execution_id=self.path.split('/')[-2]
            version=self.server.executions[execution_id]
            status,body=200,{'execution':{'executionId':execution_id,'status':'SUCCEEDED','workflowVersion':version,'outputData':{'marker':'snapshot-'+str(version)}}}
        else:
            version=segment if segment is not None else self.server.live
            eid='ex_'+str(len(self.server.executions)); self.server.executions[eid]=version
            status,body=200,{'executionId':eid,'status':'PENDING','sessionId':'session','response':'ok','runId':'run'}
        raw=json.dumps(body).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    do_POST=reply
    do_GET=reply
    def log_message(self,*args): pass

@pytest.fixture
def server(monkeypatch):
    monkeypatch.delenv('SWFTE_CALLSITE_STACK',raising=False)
    srv=ThreadingHTTPServer(('127.0.0.1',0),Handler); srv.seen=[]; srv.bodies={}; srv.executions={}; srv.live=3; srv.redirect=None
    srv.published={label:'PUBLISHED' for label in ['3','1.0.7','1.0.7-rc.2+build.09','1.0.7+'+'a'*122]}
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
    for bad in [0,-1,1.5,True,None,float('nan'),2147483648]:
        with pytest.raises(Exception): c.workflows.invoke_version('wf_shared',bad)
    assert server.seen == []
    c.workflows.invoke_version('wf@shared:release',3,callsite=ID+'\n')
    assert server.seen[0][1] == '/v2/workflows/wf%40shared%3Arelease/versions/3/invoke' and server.seen[0][2] is None

def test_all_artifact_runtime_branches_and_default_off(server):
    c=client(server)
    c.workflows.execute('wf_shared',callsite=ID); c.workflows.invoke('wf_shared',callsite=ID)
    c.workflows.invoke_version('wf_shared',3,callsite=ID); c.agents.chat('ag_shared','hello',callsite=ID)
    c.chatflows.start_session('cf_shared',callsite=ID); c.chatflows.test('cf_shared',{},callsite=ID)
    assert len(server.seen)==6 and all(x[2]==ID for x in server.seen)
    c.chatflows.test('cf_shared',{}); assert server.seen[-1][2] is None

def test_real_redirect_never_forwards_to_second_listener(server):
    canary=ThreadingHTTPServer(('127.0.0.1',0),Handler); canary.seen=[];canary.bodies={}; canary.executions={}; canary.live=3; canary.redirect=None
    thread=threading.Thread(target=canary.serve_forever,kwargs={'poll_interval':0.02},daemon=True); thread.start()
    try:
        server.redirect='http://127.0.0.1:'+str(canary.server_port)+'/canary'
        c=client(server)
        for run in [lambda:c.workflows.invoke_version('wf_shared',3,callsite=ID),lambda:c.workflows.execute('wf_shared',callsite=ID),lambda:c.agents.chat('ag_shared','hello',callsite=ID),lambda:c.chatflows.test('cf_shared',{},callsite=ID)]:
            with pytest.raises(Exception): run()
        assert canary.seen == []
    finally: canary.shutdown(); canary.server_close(); thread.join()


def test_semantic_pins_preserve_exact_build_identity_and_never_fall_back_to_live(server):
    c=client(server); server.live=4
    invocation=c.workflows.invoke_version('wf_shared','1.0.7')
    assert invocation.execution_id and server.seen[0][1:] == ('/v2/workflows/wf_shared/versions/1.0.7/invoke',None)
    pinned=c.workflows.invoke_version_and_wait('wf_shared','1.0.7',callsite=ID,poll_interval=0.001)
    assert pinned.outputs == {'marker':'snapshot-1.0.7'}
    build='1.0.7-rc.2+build.09'
    prerelease=c.workflows.invoke_version_and_wait('wf_shared',build,callsite=ID,poll_interval=0.001)
    assert prerelease.outputs == {'marker':'snapshot-'+build}
    assert [row for row in server.seen if row[1].endswith('/invoke')][-1][1:] == ('/v2/workflows/wf_shared/versions/1.0.7-rc.2%2Bbuild.09/invoke',ID)
    boundary='1.0.7+'+'a'*122
    assert len(boundary)==128
    c.workflows.invoke_version('wf_shared',boundary)
    assert server.seen[-1][1] == '/v2/workflows/wf_shared/versions/1.0.7%2B'+'a'*122+'/invoke'
    for target,version in [(c,'9.9.9'),(client(server,'B'),'1.0.7')]:
        with pytest.raises(Exception) as caught: target.workflows.invoke_version('wf_shared',version)
        assert caught.value.status_code == 404
    assert all(row[2] is None for row in server.seen if row[1].endswith('/status'))
    assert all(row[1] != '/v2/workflows/wf_shared/invoke' for row in server.seen)

def test_unsafe_raw_version_segments_have_zero_effect_for_invoke_and_wait(server):
    c=client(server)
    for bad in ['', '1.0.7/', '1.0.7?x=1', '1.0.7#x', '../1.0.7',
                '.', '..', '1.0.7%2Fextra', ' 1.0.7', '1.0.7 ', '1.0.7\n', '\n1.0.7', '1.0.7\r', '1.0.7\0',
                '١.0.7', '---._+:@', 'v3\\extra', '1.0.7\t', '1.0.7+'+'a'*123]:
        with pytest.raises(Exception): c.workflows.invoke_version('wf_shared',bad,callsite=ID)
        with pytest.raises(Exception): c.workflows.invoke_version_and_wait('wf_shared',bad,callsite=ID,poll_interval=0.001)
        assert server.seen == []


def test_safe_legacy_labels_require_exact_published_records_for_all_invoke_wait_branches(server):
    c=client(server); server.live=4; server.published.pop('3')
    for label in ['v3','v4','custom@v3:release','latest','5','01.0.7','1.0','1.0.7+','1.0.7-','3']:
        route='/v2/workflows/wf_shared/versions/'+quote(label,safe='')+'/invoke'
        before=len(server.seen); old_executions=len(server.executions)
        for run in [lambda:c.workflows.invoke_version('wf_shared',label,callsite=ID),
                    lambda:c.workflows.invoke_version_and_wait('wf_shared',label,callsite=ID,poll_interval=0.001)]:
            with pytest.raises(Exception) as caught: run()
            assert caught.value.status_code==404
        assert len(server.executions)==old_executions
        assert server.seen[before:]==[('POST',route,ID),('POST',route,ID)]
        server.published[label]='PUBLISHED'
        assert c.workflows.invoke_version('wf_shared',label).execution_id
        assert server.seen[-1]==('POST',route,None)
        c.workflows.invoke_version('wf_shared',label,callsite=ID)
        assert server.seen[-1]==('POST',route,ID)
        assert c.workflows.invoke_version_and_wait('wf_shared',label,poll_interval=0.001).outputs=={'marker':'snapshot-'+label}
        assert server.seen[-2]==('POST',route,None)
        assert c.workflows.invoke_version_and_wait('wf_shared',label,callsite=ID,poll_interval=0.001).outputs=={'marker':'snapshot-'+label}
        assert server.seen[-2]==('POST',route,ID)
    server.published['draft-v3']='DRAFT'
    before=len(server.executions)
    for label in ['draft-v3','unknown-v3']:
        with pytest.raises(Exception) as caught: c.workflows.invoke_version_and_wait('wf_shared',label,poll_interval=0.001)
        assert caught.value.status_code==404
    with pytest.raises(Exception) as caught: client(server,'B').workflows.invoke_version('wf_shared','v3')
    assert caught.value.status_code==404 and len(server.executions)==before
    server.published['retired@v3:release']='DEPRECATED'
    assert c.workflows.invoke_version_and_wait('wf_shared','retired@v3:release',poll_interval=0.001).outputs=={'marker':'snapshot-retired@v3:release'}
    assert all(row[0]=='GET' and row[2] is None for row in server.seen if row[1].endswith('/status'))
    assert all(row[1]!='/v2/workflows/wf_shared/invoke' for row in server.seen)


def test_pinned_numeric_and_opaque_stack_capture_two_callers_refuse_every_production_flag(server,monkeypatch,tmp_path):
    source=tmp_path/'pinned_callers.py';callers=tmp_path/'callers.json'
    lines=[
        'def direct_a(c,v,callsite=None):',
        "    return c.workflows.invoke_version('wf_shared',v,callsite=callsite)",
        '',
        'def direct_b(c,v,callsite=None):',
        "    return c.workflows.invoke_version('wf_shared',v,callsite=callsite)",
        '',
        'def wait_a(c,v,callsite=None):',
        "    return c.workflows.invoke_version_and_wait('wf_shared',v,callsite=callsite,poll_interval=0.001)",
        '',
        'def wait_b(c,v,callsite=None):',
        "    return c.workflows.invoke_version_and_wait('wf_shared',v,callsite=callsite,poll_interval=0.001)",
    ]
    id_a='cs_'+'a'*24;id_b='cs_'+'b'*24
    source.write_text('\n'.join(lines)+'\n')
    callers.write_text(json.dumps({'version':1,'root':str(tmp_path),'entries':{
        'pinned_callers.py:2':id_a,'pinned_callers.py:5':id_b,
        'pinned_callers.py:8':id_a,'pinned_callers.py:11':id_b,
    }}))
    spec=importlib.util.spec_from_file_location('sdk_pinned_callers',source)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    c=client(server);server.published['v3']='PUBLISHED'
    monkeypatch.setenv('SWFTE_CODEMAP_CALLERS',str(callers))
    monkeypatch.setattr(_callsite,'_production_warned',False)
    for name in ['SWFTE_ENV','ENV','PYTHON_ENV']:monkeypatch.delenv(name,raising=False)
    def invoke(explicit=None):
        for pin in [3,'v3']:
            mod.direct_a(c,pin,explicit);mod.direct_b(c,pin,explicit)
            mod.wait_a(c,pin,explicit);mod.wait_b(c,pin,explicit)
    invoke()
    assert all(row[2] is None for row in server.seen)
    server.seen.clear();monkeypatch.setenv('SWFTE_CALLSITE_STACK','1')
    invoke()
    assert [row[2] for row in server.seen if row[0]=='POST']==[id_a,id_b,id_a,id_b,id_a,id_b,id_a,id_b]
    assert all(row[0]=='GET' and row[2] is None for row in server.seen if row[1].endswith('/status'))
    for name in ['SWFTE_ENV','ENV','PYTHON_ENV']:
        server.seen.clear();monkeypatch.setenv(name,'production');monkeypatch.setattr(_callsite,'_production_warned',False)
        with pytest.warns(RuntimeWarning,match='ignored in production'):invoke()
        assert all(row[2] is None for row in server.seen)
        server.seen.clear();invoke(ID)
        assert all(row[2]==ID for row in server.seen if row[0]=='POST')
        assert all(row[2] is None for row in server.seen if row[0]=='GET')
        monkeypatch.delenv(name)

def test_workflow_identifier_boundary_has_zero_transport_and_exact_legal_routes(server):
    c=client(server)
    def entries(wf):
        return [lambda:c.workflows.execute(wf,INPUT),lambda:c.workflows.execute(wf,INPUT,skip_validation=True),
                lambda:c.workflows.execute(wf,INPUT,skip_validation=True,callsite=ID),
                lambda:c.workflows.invoke(wf,INPUT),lambda:c.workflows.invoke(wf,INPUT,callsite=ID),
                lambda:c.workflows.invoke_and_wait(wf,INPUT,poll_interval=0.001,callsite=ID),
                lambda:c.workflows.invoke_version(wf,3,INPUT),lambda:c.workflows.invoke_version(wf,'1.0.7',INPUT,callsite=ID),
                lambda:c.workflows.invoke_version_and_wait(wf,3,INPUT,poll_interval=0.001),
                lambda:c.workflows.invoke_version_and_wait(wf,'1.0.7',INPUT,poll_interval=0.001,callsite=ID)]
    for wf in ['', '.', '..','../other','a/b','a\\b','a?x=1','a#x','a%2fother',' a','a ','a\n','a\r','a\0','é','a+b','a'*129,None,42,{}]:
        for run in entries(wf):
            with pytest.raises(InvalidRequestError): run()
        assert server.seen == [] and server.executions == {}
    for wf in ['wf_shared','@:-','...','wf@release:v1','a'*128]:
        first=len(server.seen)
        for run in entries(wf): run()
        rows=server.seen[first:]
        assert all(server.bodies[first+i]==(INPUT if row[0]=='POST' else None) for i,row in enumerate(rows))
        prefix='/v2/workflows/'+quote(wf,safe='')
        posts=[row for row in rows if row[0]=='POST']
        assert [row[1] for row in posts] == [prefix+'/execute',prefix+'/execute?skipValidation=True',prefix+'/execute?skipValidation=True',prefix+'/invoke',prefix+'/invoke',prefix+'/invoke',prefix+'/versions/3/invoke',prefix+'/versions/1.0.7/invoke',prefix+'/versions/3/invoke',prefix+'/versions/1.0.7/invoke']
        assert [row[2] for row in posts] == [None,None,ID,None,ID,ID,None,ID,None,ID]
        assert all(row[2] is None for row in rows if row[0]=='GET')


if __name__ == "__main__":
    if sys.argv[1:] != ["--unit-gate"]:
        raise SystemExit("Use --unit-gate to run the workflow transport controls")
    exit_code=pytest.main([str(Path(__file__).resolve()),"-q"])
    if exit_code==0:
        print("SDK_PYTHON_WORKFLOW_UNIT_OK")
    raise SystemExit(exit_code)
