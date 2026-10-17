#!/usr/bin/python3
"""Ordinary-user read-only-preflight code bundle. Never installs or allocates.

Package content is only pinned as a previously independently verified candidate;
this code-only bundle does not copy its payload or authorize its installation.
"""
import argparse,hashlib,json,os,re,stat,subprocess
from pathlib import Path
PREFIX='maintenance/source19-native-transition-r1/'
ROOT='/usr/lib/r16-maintenance/source19-native-transition-r1'
PIN='/etc/r16-maintenance/source19-native-transition-r1-entry-capsule.json'
FILES=[PREFIX+x for x in ('profile.py','stop_transition.py','linux_backend.py','native_checkpoint.py','checkpoint_public.mjs','orchestration.py','publication.mjs','transaction.mjs','history-baseline.mjs')]+[PREFIX+'entry/'+x for x in ('common.py','operator.py','native_guard.py','foreground.py','rpc.py','transport.py','bootstrap.py','service_main.py','service-run.mjs','public-state.mjs','revision-plan.mjs','r16-source19-native-transition-r1-rpc','r16-source19-native-transition-r1.sudoers')]+['maintenance/first-stop-r8/linux_backend.py','maintenance/release-r6/transaction-driver.mjs','maintenance/release-r6/io.mjs','src/lease-core.mjs','src/control-clock.mjs','authority/source-baseline.mjs']
class Refused(ValueError):pass
def need(v,c):
 if not v:raise Refused(c)
def canonical(v):
 if isinstance(v,dict):return '{'+','.join(json.dumps(k)+':'+canonical(v[k])for k in sorted(v,key=lambda s:s.encode('utf-16-be')))+'}'
 if isinstance(v,list):return '['+','.join(canonical(x)for x in v)+']'
 return json.dumps(v,ensure_ascii=False,separators=(',',':'))
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(v):return sha(canonical(v).encode())
def read(p,git_source=False):
 p=Path(p);need(not any(x.is_symlink()for x in(p,*p.parents)),'SOURCE_LINK')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode)and a.st_nlink==1 and a.st_uid==os.getuid()and not a.st_mode&(0o002 if git_source else 0o022)and a.st_size<=32*1024*1024,'SOURCE_UNSAFE');b=os.read(fd,a.st_size+1);z=os.fstat(fd);n=p.lstat()
  stamp=lambda s:(s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  need(len(b)==a.st_size and stamp(a)==stamp(z)==stamp(n),'SOURCE_CHANGED');return b
 finally:os.close(fd)
def emit(p,b,mode=0o644):
 p.parent.mkdir(mode=0o755,parents=True,exist_ok=True);fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
 try:
  offset=0
  while offset<len(b):
   count=os.write(fd,b[offset:]);need(count>0,'OUTPUT_WRITE_UNCERTAIN');offset+=count
  os.fchmod(fd,mode);os.fsync(fd)
 finally:os.close(fd)
def build(repo,out,package,head):
 need(os.getuid()==os.geteuid()!=0,'ORDINARY_USER_REQUIRED');repo=repo.resolve();out=out.absolute();product=repo/'execution/minimal-human-trust'
 git=lambda *a:subprocess.check_output(['git','-C',str(repo),*a],text=True).strip()
 need(re.fullmatch('[a-f0-9]{40}',head)and git('rev-parse','HEAD')==head,'EXACT_SOURCE_HEAD_REQUIRED');need(not git('status','--porcelain'),'CLEAN_SOURCE_REQUIRED');need(not out.exists(),'NEW_OUTPUT_REQUIRED')
 sources={n:read(product/n,git_source=True)for n in FILES}
 for n,b in sources.items():need(b==subprocess.check_output(['git','-C',str(repo),'show',head+':execution/minimal-human-trust/'+n]),'EXACT_TRACKED_SOURCE_BYTES_REQUIRED')
 # Target identities are tied to the actual isolated physical package metadata.
 inventory=json.loads(read(package/'metadata/PAYLOAD_INVENTORY.json'))['files'];native=json.loads(read(package/'metadata/native-manifest.json'))
 need(digest(native)=='085e578d4c974aa706b6980e1fd20cd9880e694c3a6edfb237924cd6c8525dcb'and len(inventory)==12592 and digest(inventory)=='30cc64a3d3e5684a08d249d5c52bee4f3d8815833cac8399b073c0a7dc61731e','EXACT_UNSIGNED_NATIVE_CANDIDATE_REQUIRED')
 rows={n:{'sha256':sha(b),'bytes':len(b),'mode':0o644}for n,b in sources.items()}
 files={ROOT+'/runtime/'+n:r['sha256']for n,r in rows.items()}
 template={'schema':'r16.source19-native-transition.plan.v1','scope':'SAME_PLAN_SOURCE19_NATIVE_MAINTENANCE_NOT_DRAINED','sourcePublicConfigHash':'56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec','sourceDeliveryHash':'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9','grantHash':'00ac437d66143e627132975555d06396d69ff69616f630d19e3622627e15c5e6','sourceNativeVersion':'2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4','targetReleaseId':'r16-daily-20261017-source19-native-lifecycle-r1','targetNativeVersion':digest(native),'targetInventoryHash':digest(inventory),'codeFreezeHash':digest(files),'allowNativeNonGracefulOnce':True,'acceptUnprovenInflight':True,'acceptPossibleUpstreamContinuation':True,'recoveryPolicy':'KEEP_CRASHED_NATIVE_STOPPED_NO_AUTOMATIC_BUSINESS_REOPEN'}
 freeze={'schema':'r16.source19-native-transition.entry-freeze.v1','mode':'READONLY_PREFLIGHT_SOURCE','files':rows,'packageFiles':{},'planTemplate':template,'revisionRequest':{'legacy21_22Disposition':'CANCELLED_UNALLOCATED_REPLAN','forward':None,'recovery':None}}
 raw=canonical(freeze).encode();capsule=sha(raw);out.mkdir(mode=0o700,parents=False)
 for n,b in sources.items():emit(out/'root/runtime'/n,b)
 emit(out/'root/ENTRY_FREEZE.json',raw,0o600);pin={'schema':'r16.source19-native-transition.installed-entry.v1','capsuleHash':capsule};emit(out/'installed-entry-pin.json',canonical(pin).encode(),0o600)
 targets={ROOT+'/runtime/'+n:{**r,'uid':0,'gid':0}for n,r in rows.items()};targets[ROOT+'/ENTRY_FREEZE.json']={'sha256':capsule,'bytes':len(raw),'mode':0o600,'uid':0,'gid':0};praw=canonical(pin).encode();targets[PIN]={'sha256':sha(praw),'bytes':len(praw),'mode':0o600,'uid':0,'gid':0}
 cloudTargets={}
 for name,dst,mode in [('r16-source19-native-transition-r1-rpc','/usr/libexec/r16-source19-native-transition-r1-rpc',0o755),('r16-source19-native-transition-r1.sudoers','/etc/sudoers.d/r16-source19-native-transition-r1',0o440)]:
  b=sources[PREFIX+'entry/'+name];emit(out/'cloud-policy'/name,b,mode);cloudTargets[dst]={'sha256':sha(b),'bytes':len(b),'mode':mode,'uid':0,'gid':0}

 admission={'schema':'r16.source19-native-transition.code-admission-candidate.v1','sourceHead':head,'capsuleHash':capsule,'scope':'INSTALL_ROOT_OWNED_READONLY_PREFLIGHT_CODE_AND_FIXED_RPC_ONLY','targets':targets,'cloudOnlyTargets':cloudTargets,'directoryMode':0o755,'existingPathPolicy':'ABSENT_OR_EXACT_MATCH_ONLY_NO_OVERWRITE','rootOwned':True,'requiresRealHostAdminReview':True,'authority':False,'readyForNativeConfirmation':False,'productionEffects':0,'serviceUnitInstalled':False,'helperOrSudoersInstalled':False,'packageOrReleaseInstalled':False,'signaturesIssued':0,'ownerIdentityChanged':False,'revisionAllocated':False,'businessAcceptance':False,'blockedExecutionReasons':['TARGET_ACTIVATION_CURRENT_CHECKPOINT_RECOVERY_CONTRACT_NOT_IMPLEMENTED','REAL_TWO_HOST_ROOT_PREFLIGHT_NOT_YET_PERFORMED'],'rollback':'Archive only exact matching newly installed code, pin and cloud readonly RPC policy; leave existing services, business state and prior policy untouched.'}
 emit(out/'CODE_ADMISSION_CANDIDATE.json',canonical(admission).encode())
 need(git('rev-parse','HEAD')==head and not git('status','--porcelain')and all(read(product/n,git_source=True)==b for n,b in sources.items()),'SOURCE_CHANGED_DURING_BUILD')
 receipt={'schema':'r16.source19-native-transition.code-bundle-build.v1','sourceHead':head,'capsuleHash':capsule,'sourceFiles':len(rows),'sourceBytes':sum(len(b)for b in sources.values()),'authority':False,'readyForNativeConfirmation':False,'productionEffects':0,'packageCopied':False,'revisionAllocated':False,'businessAcceptance':False}
 emit(out/'BUILD_RECEIPT.json',canonical(receipt).encode());return receipt
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--package',type=Path,required=True);p.add_argument('--source-head',required=True);a=p.parse_args()
 try:print(json.dumps(build(a.repo,a.output,a.package,a.source_head)))
 except(Exception)as e:print(json.dumps({'status':'REFUSED','code':str(e)if isinstance(e,Refused)else'CODE_BUNDLE_BUILD_FAILED','productionEffects':0}));raise SystemExit(78)
