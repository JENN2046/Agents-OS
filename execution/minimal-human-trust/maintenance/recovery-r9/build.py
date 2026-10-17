"""Non-root deterministic R9 capsule, preserving all 12,600 frozen R6 files."""
import argparse,ast,hashlib,importlib.util,json,os,re,stat,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
FROZEN=Path('/home/jenn/AGENTS_OS_Workspace/ops/g1d-native-recovery-reconnect-20261014-r1/r15-backport/maintenance-app-recovery-r6')
OUT=FROZEN.parent/'maintenance-recovered-r9'
CLOUD='/home/ubuntu/r16-maintenance-recovered-r9-candidate'
PRIOR=Path('/home/jenn/Documents/Codex/2026-10-16/G1D-R8-R3-EXPIRED-ABORT-COMPENSATION-R1')
FROZEN_SHA='0b9b1d2bb83f105c0b2ff514536ea777964d49d97ede3f1d06e83961a6fe82a0'
OVERRIDE_PINS={'quiescence.py':'279193bdc2457444d455bf35d48e9bf3f98d0483efddac6138fd40dccf417f74','os_entry.py':'d6e8f1262910adf60688770bc7794a14aeb56c8075e75020e74f400fe098d41b'}
def reviewed_override_path(name):
 # Historical R9 input, independent of later readiness/recovery source fixes.
 if name=='os_entry.py':return HERE/'fixtures/os-entry-at-1697b82.txt'
 return HERE.parent/'release-r6'/name
def need(v,c):
 if not v:raise ValueError(c)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def read(path,limit=64*1024*1024):
 p=Path(path);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode) and a.st_nlink==1 and not a.st_mode&0o002 and a.st_size<=limit,'BUILD_REGULAR_SOURCE_REQUIRED');raw=b''
  while len(raw)<=limit:
   block=os.read(fd,min(1048576,limit+1-len(raw)))
   if not block:break
   raw+=block
  stamp=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  need(len(raw)==a.st_size and stamp(a)==stamp(os.fstat(fd))==stamp(p.lstat()),'BUILD_SOURCE_CHANGED');return raw,stat.S_IMODE(a.st_mode)
 finally:os.close(fd)
def replace_once(text,a,b):need(text.count(a)==1,'BUILD_PATCH_CONTEXT_DRIFT:'+a[:60]);return text.replace(a,b,1)
def provenance():
 spec=importlib.util.spec_from_file_location('r9_builder_provenance',HERE/'prior-verifier.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m.PROVENANCE,m.PINS
def guard_bootstrap_effects(text):
 """The native bootstrap's absolute window guards each kernel effect call.

 Service subprocesses do not inherit Python globals and use the stored plan's
 existing forward/recovery deadlines. Fsync completes already admitted writes.
 """
 helper="""
def native_bootstrap_window():
    accepted=globals().get('NATIVE_ACCEPTED_AT')
    if accepted is not None:
        need(type(accepted) is int and accepted<=now_ms()<accepted+300000,'NEW_NATIVE_BOOTSTRAP_WINDOW_EXPIRED')

def native_bootstrap_effect(effect,*args,**kwargs):
    native_bootstrap_window()
    return effect(*args,**kwargs)
"""
 tree=ast.parse(text)
 class Guard(ast.NodeTransformer):
  def visit_Call(self,node):
   self.generic_visit(node);f=node.func
   guarded=isinstance(f,ast.Attribute) and ((isinstance(f.value,ast.Name) and f.value.id=='os' and f.attr in {'open','write','fchmod','unlink','link','replace'}) or (isinstance(f.value,ast.Name) and f.value.id=='subprocess' and f.attr=='run') or f.attr in {'mkdir','chmod'})
   if guarded:return ast.copy_location(ast.Call(func=ast.Name(id='native_bootstrap_effect',ctx=ast.Load()),args=[f,*node.args],keywords=node.keywords),node)
   return node
 tree=Guard().visit(tree);tree.body.extend(ast.parse(helper).body);ast.fix_missing_locations(tree)
 # Helpers must be defined before the guarded entry's __main__ branch.
 main=tree.body[-3];need(isinstance(main,ast.If),'GENERATED_MAIN_CONTEXT_DRIFT')
 tree.body=tree.body[:-3]+tree.body[-2:]+[main]
 return ast.unparse(tree)+'\n'
def transform(name,raw):
 if not name.endswith(('.py','.mjs')):return raw
 s=raw.decode().replace(str(FROZEN),str(OUT)).replace('/home/ubuntu/r16-maintenance-app-recovery-r6-candidate',CLOUD)
 s=s.replace('/r16-maintenance/recovery-r6','/r16-maintenance/recovery-r9').replace('r16-native-recovery-maintenance-r6.service','r16-native-recovery-maintenance-r9.service').replace('r16-maintenance-os-r6','r16-maintenance-os-r9')
 if name=='quiescence.py':
  s=s.replace("FENCE_ROOT = '/run/r16-maintenance-os-r9'","FENCE_ROOT = '/run/r16-maintenance-recovery-r9'").replace("DROPIN_NAME = '90-r16-maintenance-os-r9.conf'","DROPIN_NAME = '94-r16-maintenance-recovery-r9.conf'")
 if name=='run.mjs':
  s=replace_once(s,"return json(STATE+'/transaction-'+name+'.json');","const value=json(STATE+'/transaction-'+name+'.json');if(name==='receipt')need(same(value.sourceRecoveryEvidence,json(STATE+'/plan.json').sourceRecoveryEvidence),'RECOVERED_SOURCE_RECEIPT_DRIFT');return value;")
  s=replace_once(s,"write:(name,v)=>atomicJson(STATE+'/transaction-'+name+'.json',v)","write:(name,v)=>atomicJson(STATE+'/transaction-'+name+'.json',name==='receipt'?{...v,sourceRecoveryEvidence:json(STATE+'/plan.json').sourceRecoveryEvidence,historicalSourceStopForceUsed:true,forceTerminationUsed:false,businessAcceptance:false}:v)")
 if name=='context.mjs':
  s=replace_once(s,"  atomicJson(STATE+'/context.json',context);", "  need(Date.now()<plan.expiresAt,'NATIVE_WINDOW_INVALID');\n  atomicJson(STATE+'/context.json',context);")
  s=replace_once(s,"  atomicJson('/etc/r16-maintenance/recovery-r9-source-freeze.json'", "  need(Date.now()<plan.expiresAt,'NATIVE_WINDOW_INVALID');\n  atomicJson('/etc/r16-maintenance/recovery-r9-source-freeze.json'")
 if name=='os_entry.py':
  s=replace_once(s,"manifest, sources, manifest_raw = verify_capsule(capsule);record=install_capsule(manifest, sources, capsule, manifest_raw)","manifest, sources, manifest_raw = verify_capsule(capsule)\n    prior_namespace={'__name__':'r9_prior_readonly'}\n    exec(compile(sources['prior-verifier.py'],'<sealed-r9-prior-verifier>','exec'),prior_namespace)\n    prior_namespace['verify_prior'](manifest,sources)\n    record=install_capsule(manifest, sources, capsule, manifest_raw)")
  s=replace_once(s,"projection={'schema':receipt['schema'],'status':receipt['status'],'businessAcceptance':False}","prior=read_json(STATE/'plan.json')['sourceRecoveryEvidence']\n    need(receipt.get('sourceRecoveryEvidence')==prior,'RECOVERED_SOURCE_RECEIPT_DRIFT')\n    projection={'schema':receipt['schema'],'status':receipt['status'],'businessAcceptance':False,'sourceRecoveryEvidence':prior,'historicalSourceStopForceUsed':True,'forceTerminationUsed':False}")
  s=replace_once(s,"manifest, sources, manifest_raw = verify_capsule(capsule)\n    prior_namespace=", "accepted=globals().get('NATIVE_ACCEPTED_AT')\n    need(type(accepted) is int and accepted<=now_ms()<accepted+300000,'NEW_NATIVE_BOOTSTRAP_WINDOW_REQUIRED')\n    manifest, sources, manifest_raw = verify_capsule(capsule)\n    prior_namespace=")
  s=replace_once(s,"    prior_namespace={'__name__':'r9_prior_readonly'}", "    native=globals().get('NATIVE_CONFIRMATION');pending=globals().get('NATIVE_PENDING')\n    need(isinstance(native,dict) and isinstance(pending,dict) and native.get('schema')=='r16.r9.native-install-confirmation.v1' and pending.get('schema')=='r16.r9.native-install-pending.v1','EXACT_NEW_NATIVE_CONFIRMATION_REQUIRED')\n    need(native.get('issuedAt')==accepted and native.get('expiresAt')==accepted+300000 and native.get('pendingHash')==digest(pending) and native.get('nonce')==pending.get('nonce'),'EXACT_NEW_NATIVE_CONFIRMATION_REQUIRED')\n    need(pending.get('host')==(CLOUD if kind=='bootstrap-cloud' else LOCAL) and pending.get('capsuleHash')==capsule and pending.get('entrySha256')==manifest['files']['os_entry.py'] and pending.get('sourceRecoveryEvidence')==manifest['planTemplate']['sourceRecoveryEvidence'] and pending.get('sourceAppBaseline')=='STOPPED' and pending.get('oldPlanRenewed') is False,'EXACT_NEW_NATIVE_TARGET_REQUIRED')\n    prior_namespace={'__name__':'r9_prior_readonly'}")
  s=replace_once(s,"'createdAt':now_ms()", "'createdAt':now_ms(),'nativeAcceptedAt':globals()['NATIVE_ACCEPTED_AT'],'nativePendingHash':digest(globals()['NATIVE_PENDING']),'nativePending':globals()['NATIVE_PENDING'],'nativeConfirmation':globals()['NATIVE_CONFIRMATION']")
  s=replace_once(s,"need(record['createdAt']<=now_ms()<record['createdAt']+1800000,'BOOTSTRAP_WINDOW_EXPIRED')", "need(record.get('nativeAcceptedAt')==globals().get('NATIVE_ACCEPTED_AT') and record['nativeAcceptedAt']<=now_ms()<record['nativeAcceptedAt']+300000,'NEW_NATIVE_BOOTSTRAP_WINDOW_EXPIRED')")
  s=s.replace("record['createdAt']+1800000","record['nativeAcceptedAt']+1800000")
  s=replace_once(s,"approved = record['createdAt'];deadline", "approved = record['nativeAcceptedAt'];deadline")
 return (guard_bootstrap_effects(s) if name=='os_entry.py' else s).encode()
def build(out=OUT):
 out=Path(out);need(os.getuid()!=0 and out.is_absolute() and not out.is_symlink() and (not out.exists() or out.is_dir() and not any(out.iterdir())),'EMPTY_NON_ROOT_OUTPUT_REQUIRED')
 raw,_=read(FROZEN/'SOURCE_FREEZE.json');need(sha(raw)==FROZEN_SHA,'FROZEN_R6_CAPSULE_DRIFT');f=json.loads(raw);need(len(f['files'])==14 and len(f['payloadFiles'])==12600,'FROZEN_COUNTS_DRIFT')
 original={}
 for n,pin in f['files'].items():
  b,_=read(FROZEN/n);need(sha(b)==pin,'FROZEN_RUNTIME_DRIFT:'+n);original[n]=b
 for n,pin in OVERRIDE_PINS.items():
  original[n]=read(reviewed_override_path(n))[0];need(sha(original[n])==pin,'REVIEWED_OVERRIDE_DRIFT:'+n)
 result={n:transform(n,b) for n,b in original.items()}
 qsha=sha(result['quiescence.py']);entry,count=re.subn(rb"(?m)^Q_SHA = '[a-f0-9]{64}'$",('Q_SHA = '+repr(qsha)).encode(),result['os_entry.py']);need(count==1,'NEW_Q_PIN_REQUIRED');result['os_entry.py']=entry
 evidence,pins=provenance();result['prior-verifier.py']=read(HERE/'prior-verifier.py')[0]
 for new,old in {'prior-compensation.py':'compensation.py','prior-native-guard.py':'native_guard.py','prior-evidence.json':'LOCAL_EVIDENCE.json'}.items():
  b,_=read(PRIOR/old);need(sha(b)==pins[new],'PRIOR_REVIEWED_INPUT_DRIFT');result[new]=b
 result['cache-cleanup.py']=read(HERE/'cache-cleanup.py')[0]
 inventory=json.loads(read(FROZEN/'package/metadata/PAYLOAD_INVENTORY.json')[0]);package={};closure={}
 for n,pin in f['payloadFiles'].items():
  need(not Path(n).is_absolute() and '\\' not in n and all(x not in ('','.','..') for x in n.split('/')),'PACKAGE_PATH_REFUSED');b,mode=read(FROZEN/'package'/n)
  expected=inventory[n[len('payload/'):]]['mode'] if n.startswith('payload/') else 0o644
  need(sha(b)==pin and mode==expected,'FROZEN_PACKAGE_BYTES_OR_MODE_DRIFT:'+n);package[n]=(b,mode);closure[n]={'sha256':pin,'mode':mode,'bytes':len(b)}
 need(sha(canon(closure))=='c7bc7ba7fa3fb0fbc5099ef28709059a5116a5943cc9aecd75bc17cb1abbafd8','INDEPENDENT_PACKAGE_CLOSURE_DRIFT')
 actual=set()
 for p in (FROZEN/'package').rglob('*'):
  st=p.lstat();need(stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode),'FROZEN_PACKAGE_SPECIAL_FILE')
  if stat.S_ISDIR(st.st_mode):need(stat.S_IMODE(st.st_mode)==0o755,'FROZEN_PACKAGE_DIRECTORY_MODE')
  else:actual.add(str(p.relative_to(FROZEN/'package')))
 need(actual==set(package),'FROZEN_PACKAGE_EXTRA_FILE')
 for n,b in result.items():
  if n.endswith('.py'):compile(b,n,'exec')
 source_head=subprocess.check_output(('git','rev-parse','HEAD'),cwd=HERE,text=True).strip();need(re.fullmatch('[a-f0-9]{40}',source_head),'SOURCE_HEAD_REQUIRED')
 need(not subprocess.check_output(('git','status','--porcelain'),cwd=HERE,text=True),'DIRTY_SOURCE_BUILD_REFUSED')
 freeze={**f,'files':{n:sha(b) for n,b in sorted(result.items())},'planTemplate':{**f['planTemplate'],'sourceRecoveryEvidence':evidence,'maintenanceSourceHead':source_head}}
 out.mkdir(parents=True,exist_ok=True);out.chmod(0o755)
 def emit(n,b,mode):
  p=out/n;p.parent.mkdir(parents=True,exist_ok=True)
  cursor=p.parent
  while cursor!=out:cursor.chmod(0o755);cursor=cursor.parent
  with p.open('xb') as file:file.write(b)
  p.chmod(mode)
 for n,b in result.items():emit(n,b,0o644)
 for n,(b,mode) in package.items():emit('package/'+n,b,mode)
 emit('SOURCE_FREEZE.json',canon(freeze),0o644)
 return {'schema':'r16.r9-recovered-source-physical-build.v1','status':'ISOLATED_UNSIGNED_NOT_INSTALLED','frozenBaseSha256':FROZEN_SHA,'capsuleHash':sha(canon(freeze)),'osEntryHash':sha(entry),'quiescenceHash':qsha,'runtimeFiles':len(result),'packageFiles':len(package),'payloadFiles':len(inventory),'packageClosureHash':sha(canon(closure)),'packageBytes':sum(len(b) for b,_ in package.values()),'planTemplate':freeze['planTemplate'],'oldPlanRenewed':False,'physicalOutput':str(out),'productionExecuted':False}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=OUT);args=parser.parse_args();print(json.dumps(build(args.output),indent=2))
