"""Observe real HTTP headers on the frozen Conduit variant, against fresh databases."""
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

W=Path(__file__).resolve().parent.parent
OUT=Path(os.environ["PROBE_BUILD_DIR"]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("CONDUIT_V15_DOCKER_REAL", shutil.which("docker"))
os.environ["PATH"] = str(W / "reproduce/bin") + os.pathsep + os.environ["PATH"]
kind,image=sys.argv[1:3]
label=sys.argv[3] if len(sys.argv)>3 else kind
prefix='conduit-v15-headers-'+label
net,db,app=[prefix+s for s in ['-net','-db','-app']]
port=4503
out=OUT/f'headers-{label}.json'
assert not out.exists(),out
record=dict(kind=kind,image=image,rails_condition='Rails 8.1.4, load_defaults 8.1, API-only, production; frozen v14 app',
            requests=[])

def docker(*args,check=True,**kwargs):
    p=subprocess.run(['docker',*args],capture_output=True,text=True,timeout=150,**kwargs)
    if check and p.returncode:
        raise RuntimeError('Docker '+str(args[:2])+' exit '+str(p.returncode))
    return p

def req(name,method,path,body=None,token=None,raw=None,extra=None,expected=None,control=False):
    data=raw.encode() if raw is not None else json.dumps(body).encode() if body is not None else None
    headers={'Accept':'application/json'}
    if data is not None: headers['Content-Type']='application/json'
    if token: headers['Authorization']='Token '+token
    headers.update(extra or {})
    request=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=data,headers=headers,method=method)
    try: response=urllib.request.urlopen(request,timeout=10)
    except urllib.error.HTTPError as e: response=e
    with response:
        data=response.read()
        try: body=json.loads(data) if data else None
        except ValueError: body=None
        content_type=response.headers.get('Content-Type')
        expected_type=('text/html; charset=utf-8' if kind!='rails' else 'application/json; charset=utf-8') if control else \
                      None if response.status==204 else 'application/json; charset=utf-8'
        row=dict(name=name,method=method,path=path,status=response.status,content_type=content_type,
            shape=sorted(body) if isinstance(body,dict) else type(body).__name__,expected_status=expected,
            pass_status=expected is None or response.status==expected,
            expected_content_type=expected_type,retirement_json_case=not control and response.status!=204,
            pass_charset=content_type==expected_type)
        record['requests'].append(row)
        return body

try:
    record['image_id']=docker('image','inspect','--format','{{.Id}}',image).stdout.strip()
    docker('network','create',net)
    docker('run','-d','--name',db,'--network',net,'--network-alias','db',
        '--tmpfs','/var/lib/postgresql/data:rw,size=256m','-e','POSTGRES_PASSWORD=postgres',
        '-e','POSTGRES_DB=conduit','conduit-v15-postgres:17')
    deadline=time.monotonic()+120
    while docker('exec',db,'pg_isready','-h','127.0.0.1','-U','postgres','-d','conduit',check=False).returncode:
        if time.monotonic()>deadline: raise RuntimeError('database readiness')
        time.sleep(.2)
    if kind!='rails':
        docker('exec','-i',db,'psql','-v','ON_ERROR_STOP=1','-U','postgres','-d','conduit',
               input=(W/'variant/source/db/structure.sql').read_text())
    args=['run','-d','--name',app,'--network',net,'-p',f'127.0.0.1:{port}:8080',
          '-e','DATABASE_URL=postgres://postgres:postgres@db:5432/conduit',
          '-e','SECRET_KEY_BASE='+'0123456789abcdef'*8,'-e','PORT=8080',image]
    if kind=='rails': args+=['./bin/rails','server','-b','0.0.0.0','-p','8080']
    docker(*args)
    deadline=time.monotonic()+120
    while True:
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/tags',timeout=2) as response:
                if response.status==200: break
        except Exception: pass
        if docker('inspect','--format','{{.State.Running}}',app).stdout.strip()!='true':
            raise RuntimeError('app exited')
        if time.monotonic()>deadline: raise RuntimeError('HTTP readiness')
        time.sleep(.2)
    req('empty_collection','GET','/api/tags',expected=200)
    req('health_object','GET','/health',expected=200)
    req('action_failure_rescue','GET','/api/user',expected=401)
    req('before_action_failure_rescue','GET','/api/tags',token='invalid',expected=401)
    req('not_found_action','GET','/api/missing-header-probe',expected=404)
    req('malformed_json_control','POST','/api/users',raw='{"user":',expected=400,control=True)
    req('validation_errors','POST','/api/users',body={'user':{}},expected=422)
    user={'username':'header','email':'header@example.invalid','password':'password123'}
    r=req('created_user','POST','/api/users',body={'user':user},expected=201)
    token=r['user']['token']
    req('duplicate_user','POST','/api/users',body={'user':user},expected=409)
    req('user_object','GET','/api/user',token=token,expected=200)
    req('profile_object','GET','/api/profiles/header',expected=200)
    r=req('created_article','POST','/api/articles',body={'article':{'title':'Header','description':'D',
        'body':'B','tagList':['utf8']}},token=token,expected=201)
    slug=r['article']['slug']
    req('article_collection','GET','/api/articles',expected=200)
    req('article_object','GET','/api/articles/'+slug,expected=200)
    r=req('created_comment','POST','/api/articles/'+slug+'/comments',body={'comment':{'body':'C'}},
          token=token,expected=201)
    cid=r['comment']['id']
    req('comment_collection','GET','/api/articles/'+slug+'/comments',expected=200)
    r=req('created_share','POST','/api/articles/'+slug+'/share',token=token,body={},expected=201)
    req('shared_article','GET','/api/shares/'+str(r['share']['id'])+'/article',
        extra={'X-Share-Key':r['share']['key']},expected=200)
    r=req('accepted_export','POST','/api/user/exports',body={},token=token,expected=202)
    req('export_object','GET','/api/user/exports/'+str(r['export']['id']),token=token,expected=200)
    req('record_invalid_rescue','PUT','/api/user',body={'user':{'username':''}},token=token,expected=422)
    for i in range(21):
        req('login_failure_'+str(i+1),'POST','/api/users/login',
            body={'user':{'email':'throttle@example.invalid','password':'wrong'}},expected=401 if i<20 else 429)
    req('head_no_content','DELETE',f'/api/articles/{slug}/comments/{cid}',token=token,expected=204)
    if kind=='rails':
        p=docker('exec',app,'bundle','exec','ruby','-r','./config/environment','-e',
            'require "json"; puts JSON.generate(ruby: RUBY_VERSION, rails: Rails.version, api_only: Rails.application.config.api_only, escape_json_responses: Rails.application.config.action_controller.escape_json_responses)')
        candidates=[]
        for line in p.stdout.splitlines():
            try: value=json.loads(line)
            except ValueError: continue
            if isinstance(value,dict) and 'ruby' in value and 'rails' in value: candidates.append(value)
        record['oracle']=candidates[-1]
    else:
        record['server_sha256']=docker('exec',app,'sha256sum','/app/server').stdout.split()[0]
    record['pass']=all(r['pass_status'] and r['pass_charset'] for r in record['requests'])
except Exception as error:
    record.update(pass_=False,error=type(error).__name__+': '+str(error))
    record['pass']=False
finally:
    logs=docker('logs',app,check=False)
    (OUT/f'headers-{label}-app.log').write_text(logs.stdout+logs.stderr)
    docker('rm','-f',app,db,check=False)
    docker('network','rm',net,check=False)
    out.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(kind=kind,total=len(record['requests']),pass_=record.get('pass'),error=record.get('error'),
    failing_names=[r['name'] for r in record['requests'] if not(r['pass_status'] and r['pass_charset'])])),flush=True)
raise SystemExit(0 if record.get('pass') else 1)
