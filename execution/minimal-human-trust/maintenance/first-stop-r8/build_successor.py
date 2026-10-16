"""Deterministic source-only fork of the frozen R6 maintenance capsule.

No installer, signing or service call. Payload bytes/Release IDs are preserved.
The caller supplies an empty disposable output directory; SOURCE_FREEZE is
rebuilt over the modified source. Never rewrite the historical R6 capsule.
"""
import hashlib,json,re,stat
from pathlib import Path

OLD_SOURCE='/home/jenn/AGENTS_OS_Workspace/ops/g1d-native-recovery-reconnect-20261014-r1/r15-backport/maintenance-app-recovery-r6'
NEW_SOURCE=OLD_SOURCE.rsplit('/',1)[0]+'/maintenance-first-stop-r8-r2'
OLD_CLOUD='/home/ubuntu/r16-maintenance-app-recovery-r6-candidate'
NEW_CLOUD='/home/ubuntu/r16-maintenance-first-stop-r8-candidate'
R3_SOURCE=OLD_SOURCE.rsplit('/',1)[0]+'/maintenance-first-stop-r8-r3'
R3_CLOUD='/home/ubuntu/r16-maintenance-first-stop-r8-r3-candidate'
FROZEN_R6_FREEZE_SHA='0b9b1d2bb83f105c0b2ff514536ea777964d49d97ede3f1d06e83961a6fe82a0'
ORIGINAL_READER_SHA='0387912333782b6fa243b6a9ea122f53391aacfb86c1e6a528cba8fd0ed723f2'
REPAIRED_READER_SHA='48e46644ae56c72229d90f7031a8c0fea682f635a20d0114c8e54dff7e4409ff'
ADOPTION_SCHEMA='r16.first-stop-successor-adoption.v1'
POLICY_EXCEPTION='98552704b8bb8be9881318e8e8b12406448ea25f60951715a437198004ac4234'
FIRST_STOP_JS='''export function firstStopEvidence(adoption,plan){
  const hash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
  need(adoption?.schema==='r16.first-stop-successor-adoption.v1'&&
    adoption.status==='SUCCESSOR_FENCE_ADOPTED_SOURCE_APP_STOPPED'&&
    adoption.successorPlanHash===digest(plan)&&hash(plan?.capsuleHash)&&
    plan.sourceFreezeHash===plan.capsuleHash&&adoption.successorCapsuleHash===plan.capsuleHash&&
    adoption.drainStatus==='UNPROVEN'&&adoption.originalLedgerBytesPreserved===true&&adoption.cgroupEmpty===true&&
    ['checkpointDigest','stopApprovalHash','targetHash'].every(k=>hash(adoption[k])), 'FIRST_STOP_RECEIPT_BINDING_DRIFT');
  return Object.freeze({method:'CONTROLLED_CRASH_STOP',drainStatus:'UNPROVEN',
    checkpointDigest:adoption.checkpointDigest,stopApprovalHash:adoption.stopApprovalHash,targetHash:adoption.targetHash});
}
'''
FIRST_STOP_PY='''def first_stop_evidence(plan,h):
    adoption=read_json(STATE/'first-stop-adoption.json')
    need(adoption.get('schema')=='r16.first-stop-successor-adoption.v1' and
         adoption.get('status')=='SUCCESSOR_FENCE_ADOPTED_SOURCE_APP_STOPPED' and
         adoption.get('successorPlanHash')==h and ishash(plan.get('capsuleHash')) and
         plan.get('sourceFreezeHash')==plan['capsuleHash'] and adoption.get('successorCapsuleHash')==plan['capsuleHash'] and
         sha(secure_read(ROOT/'SOURCE_FREEZE.json',CAPSULE_LIMIT))==plan['capsuleHash'] and
         adoption.get('drainStatus')=='UNPROVEN' and adoption.get('originalLedgerBytesPreserved') is True and
         adoption.get('cgroupEmpty') is True and all(ishash(adoption.get(k)) for k in ('checkpointDigest','stopApprovalHash','targetHash')),
         'FIRST_STOP_RECEIPT_BINDING_DRIFT')
    return {'method':'CONTROLLED_CRASH_STOP','drainStatus':'UNPROVEN',
            **{k:adoption[k] for k in ('checkpointDigest','stopApprovalHash','targetHash')}}


'''
ADOPT_HELPER='''    if op == 'adopt-first-stop':
        need(len(args)==2 and data=={},'FIRST_STOP_HELPER_SCOPE_REFUSED')
        _,plan,h=installed_context()
        need(args[1]==h and plan.get('firstStopPolicyExceptionProposalHash')=='98552704b8bb8be9881318e8e8b12406448ea25f60951715a437198004ac4234','FIRST_STOP_PLAN_SCOPE_REFUSED')
        admission=read_json(STATE/'admission.json')
        need(admission.get('unused') is False and admission.get('planHash')==h and
             admission.get('capsuleHash')==sha(secure_read(ROOT/'SOURCE_FREEZE.json',CAPSULE_LIMIT)) and now_ms()<admission['expiresAt'],'FIRST_STOP_CLOUD_PLAN_NOT_ADMITTED')
        stop_hash=plan.get('firstStopCapsuleHash');need(ishash(stop_hash),'FIRST_STOP_CAPSULE_REQUIRED')
        directory=Path('/usr/lib/r16-maintenance/first-stop-r8')/stop_hash
        raw=secure_read(directory/'CAPSULE.json');need(sha(raw)==stop_hash,'FIRST_STOP_CAPSULE_DRIFT')
        stop_manifest=json.loads(raw)
        need(stop_manifest.get('schema')=='r16.first-stop-capsule.v1' and
             stop_manifest.get('policyExceptionProposalHash')==plan['firstStopPolicyExceptionProposalHash'] and
             set(stop_manifest['files'])=={'bootstrap.py','common_safe.py','native_entry.py','stop_driver.py','linux_backend.py','ledger_checkpoint.py','handoff.py','TARGET.json'},'FIRST_STOP_CAPSULE_SCOPE_REFUSED')
        for name,pin in stop_manifest['files'].items():
            need('/' not in name and sha(secure_read(directory/name))==pin,'FIRST_STOP_ROOT_SOURCE_DRIFT')
        sys.path.insert(0,str(directory))
        spec=importlib.util.spec_from_file_location('first_stop_r8_successor_entry',directory/'native_entry.py')
        native=importlib.util.module_from_spec(spec);sys.modules[spec.name]=native;spec.loader.exec_module(native)
        return native.adopt_from_successor_plan(stop_hash,h)
'''
ADOPT_BASELINE='''    def baseline(self, plan_hash='', adoption=None):
        if adoption is None: return self._strict_baseline(plan_hash)
        need(re.fullmatch('[a-f0-9]{64}',plan_hash or '') is not None,'PLAN_HASH_REQUIRED')
        need(isinstance(adoption,dict) and adoption.get('schema')=='r16.first-stop-successor-adoption.v1' and
             adoption.get('status')=='SUCCESSOR_FENCE_ADOPTED_SOURCE_APP_STOPPED' and
             adoption.get('successorPlanHash')==plan_hash and adoption.get('cgroupEmpty') is True and
             adoption.get('originalLedgerBytesPreserved') is True and adoption.get('drainStatus')=='UNPROVEN',
             'FIRST_STOP_ADOPTION_REQUIRED')
        for key in ('stopApprovalHash','targetHash','checkpointDigest','successorCapsuleHash'):
            need(isinstance(adoption.get(key),str) and re.fullmatch('[a-f0-9]{64}',adoption[key]),'FIRST_STOP_ADOPTION_REQUIRED')
        need(adoption.get('successorFenceSha256')==sha(fence_bytes(plan_hash)),'ADOPTION_FENCE_DRIFT')
        result={unit:self.backend.inspect(unit,plan_hash) for unit in ROLE_HOST}
        for unit,row in result.items():
            need(row.unit==unit and row.host==ROLE_HOST[unit] and row.active in ('active','inactive','failed'),'BASELINE_UNSTABLE')
            need(row.graceful_only() and not row.daemon_reload_needed,'UNSAFE_MANAGER_STOP_POLICY')
            if unit=='r16-app.service':
                need(row.stopped() and row.code_phase=='SOURCE' and row.fence_effective and
                     row.fence_hash==adoption['successorFenceSha256'] and
                     dict(row.code_hashes)==expected_code_pins(unit,'SOURCE'),'ADOPTED_APP_STATE_DRIFT')
            else: need(not row.fence_hash,'PREEXISTING_FENCE_OR_UNIT_DRIFT')
        # Keep the actual fence hash/effectivity in originalBaseline. Never
        # disguise a fenced observation as an unfenced R6 baseline.
        return result

    def _strict_baseline(self, plan_hash=''):
'''

def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def replace_once(text,old,new):
    if text.count(old)!=1: raise ValueError('FROZEN_SOURCE_PATCH_CONTEXT_DRIFT: '+old[:70])
    return text.replace(old,new,1)

def transform(name,raw,q_hash=None,*,successor_source=None,successor_cloud=None):
    if not name.endswith(('.py','.mjs')): return raw
    text=raw.decode()
    # Capsule/operator paths only. Preserve r16-daily-...recovery-r6 payload
    # directory/version and every package/payload pin.
    text=text.replace(OLD_SOURCE,successor_source or NEW_SOURCE).replace(OLD_CLOUD,successor_cloud or NEW_CLOUD)
    text=text.replace('/r16-maintenance/recovery-r6','/r16-maintenance/recovery-r8')
    text=text.replace('r16-native-recovery-maintenance-r6.service','r16-native-recovery-maintenance-r8.service')
    text=text.replace('r16-maintenance-os-r6','r16-maintenance-os-r8')
    if name=='quiescence.py':
        text=text.replace("FENCE_ROOT = '/run/r16-maintenance-os-r8'", "FENCE_ROOT = '/run/r16-maintenance-recovery-r8'")
        text=text.replace("DROPIN_NAME = '90-r16-maintenance-os-r8.conf'", "DROPIN_NAME = '93-r16-maintenance-recovery-r8.conf'")
        text=replace_once(text,"    def baseline(self, plan_hash=''):\n",ADOPT_BASELINE)
    if name=='os_entry.py':
        if not q_hash: raise ValueError('NEW_QUIESCENCE_HASH_REQUIRED')
        text,n=re.subn(r"^Q_SHA = '[a-f0-9]{64}'$",'Q_SHA = '+repr(q_hash),text,flags=re.M)
        if n!=1: raise ValueError('QUIESCENCE_HASH_PATCH_DRIFT')
        text=replace_once(text,'backend = q.RealBackend();rows = q.Controller(backend).baseline(h)',
            "backend = q.RealBackend();adoption=read_json(STATE/'first-stop-adoption.json');need(adoption.get('successorCapsuleHash')==sha(secure_read(ROOT/'SOURCE_FREEZE.json',CAPSULE_LIMIT)),'ADOPTION_CAPSULE_DRIFT');rows = q.Controller(backend).baseline(h, adoption=adoption)")
        text=replace_once(text,"    need(admitted.get('planHash') == h, 'CLOUD_PLAN_ADMISSION_REFUSED')\n",
            "    need(admitted.get('planHash') == h, 'CLOUD_PLAN_ADMISSION_REFUSED')\n    adoption=read_json(STATE/'first-stop-adoption.json') if (STATE/'first-stop-adoption.json').exists() else cloud_rpc(q,'adopt-first-stop',h,{})\n    need(adoption.get('schema')=='r16.first-stop-successor-adoption.v1' and adoption.get('successorPlanHash')==h and adoption.get('successorCapsuleHash')==capsule and adoption.get('status')=='SUCCESSOR_FENCE_ADOPTED_SOURCE_APP_STOPPED','FIRST_STOP_ADOPTION_REFUSED')\n    ensure_file(STATE/'first-stop-adoption.json',canonical(adoption))\n")
        text=replace_once(text,"    recovery = op in ('unfence', 'start', 'readback')\n",ADOPT_HELPER+"    recovery = op in ('unfence', 'start', 'readback')\n")
        text=replace_once(text,'def os_action(action):\n',FIRST_STOP_PY+'def os_action(action):\n')
        text=replace_once(text,"q = load_q();journal = Journal(STATE / 'os-journal.json')",
            "q = load_q();first_stop=first_stop_evidence(plan,h);journal = Journal(STATE / 'os-journal.json')")
        text=replace_once(text,"'adapterLedgerMutationPerformed':False,'globalSameEpochBusinessStopClaim':False,'forceTerminationUsed':False,",
            "'adapterLedgerMutationPerformed':False,'globalSameEpochBusinessStopClaim':False,'forceTerminationUsed':False,\n                'firstStopForceUsed':True,'firstStop':first_stop,")
        text=replace_once(text,'        return result\n    if action == \'observe\':',
            "        return {**result,'firstStopForceUsed':True,'firstStop':first_stop}\n    if action == 'observe':")
        text=replace_once(text,"'actors': controller.observe(p), 'businessReadinessClaim': False}",
            "'actors': controller.observe(p), 'businessReadinessClaim': False,'firstStopForceUsed':True,'firstStop':first_stop}")
        text=replace_once(text,"    projection={'schema':receipt['schema'],'status':receipt['status'],'businessAcceptance':False}\n",
            "    first_stop=first_stop_evidence(read_json(STATE/'plan.json'),h)\n    need(receipt.get('firstStop')==first_stop,'FIRST_STOP_COMPLETION_RECEIPT_DRIFT')\n    projection={'schema':receipt['schema'],'status':receipt['status'],'businessAcceptance':False,'firstStop':first_stop,'firstStopForceUsed':True}\n")
    if name=='run.mjs':
        text=replace_once(text,'function protectedJournal(){\n',FIRST_STOP_JS+'function protectedJournal(firstStop){\n')
        text=replace_once(text,"return json(STATE+'/transaction-'+name+'.json');",
            "const value=json(STATE+'/transaction-'+name+'.json');if(name==='receipt')need(same(value.firstStop,firstStop),'FIRST_STOP_COMPLETION_RECEIPT_DRIFT');return value;")
        text=replace_once(text,"write:(name,v)=>atomicJson(STATE+'/transaction-'+name+'.json',v)",
            "write:(name,v)=>atomicJson(STATE+'/transaction-'+name+'.json',name==='receipt'?{...v,firstStop,firstStopForceUsed:true,businessAcceptance:false}:v)")
        text=replace_once(text,"rootContext();const plan=json(STATE+'/plan.json'),context=json(STATE+'/context.json');verifyCapsule(plan);",
            "rootContext();const plan=json(STATE+'/plan.json'),context=json(STATE+'/context.json');verifyCapsule(plan);const firstStop=firstStopEvidence(json(STATE+'/first-stop-adoption.json'),plan);")
        text=replace_once(text,"return locked(STATE+'/.transaction-lock',()=>drive({journal:protectedJournal(),adapters}));",
            "return locked(STATE+'/.transaction-lock',async()=>({...await drive({journal:protectedJournal(firstStop),adapters}),firstStop,firstStopForceUsed:true,businessAcceptance:false}));")
    return text.encode()

def build(source,out,stop_capsule_hash):
    source,out=Path(source),Path(out)
    if out.resolve().is_relative_to(source.resolve()) or out.exists() and any(out.iterdir()): raise ValueError('EMPTY_NEW_OUTPUT_REQUIRED')
    if not isinstance(stop_capsule_hash,str) or re.fullmatch('[0-9a-f]{64}',stop_capsule_hash) is None:raise ValueError('EXACT_FIRST_STOP_CAPSULE_HASH_REQUIRED')
    freeze=json.loads((source/'SOURCE_FREEZE.json').read_bytes())
    originals={}
    for name,pin in freeze['files'].items():
        if not name or name.startswith('/') or any(x in ('','.','..') for x in name.split('/')): raise ValueError('SOURCE_PATH_REFUSED')
        raw=(source/name).read_bytes()
        if sha(raw)!=pin: raise ValueError('FROZEN_SOURCE_DRIFT: '+name)
        originals[name]=raw
    result={name:transform(name,raw) for name,raw in originals.items() if name!='os_entry.py'}
    result['os_entry.py']=transform('os_entry.py',originals['os_entry.py'],sha(result['quiescence.py']))
    out.mkdir(parents=True,exist_ok=True)
    for name,raw in sorted(result.items()):
        dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    updated={**freeze,'files':{name:sha(raw) for name,raw in sorted(result.items())},
        'planTemplate':{**freeze['planTemplate'],'firstStopCapsuleHash':stop_capsule_hash,
                        'firstStopPolicyExceptionProposalHash':POLICY_EXCEPTION}}
    (out/'SOURCE_FREEZE.json').write_bytes(canonical(updated))
    return {'schema':'r16.successor-source-build.v1','originalSourceFreezeSha256':sha((source/'SOURCE_FREEZE.json').read_bytes()),
        'sourceFreezeSha256':sha(canonical(updated)),'sourceFiles':len(result),'payloadPinsUnchanged':updated['payloadFiles']==freeze['payloadFiles'],
        'targetReleaseUnchanged':updated['planTemplate']['targetReleaseId']==freeze['planTemplate']['targetReleaseId'],
        'firstStopCapsuleHash':stop_capsule_hash,'installed':False}

def _safe_member(name):
    if not isinstance(name,str) or not name or name.startswith('/') or '\\' in name or any(x in ('','.','..') for x in name.split('/')):raise ValueError('SOURCE_PATH_REFUSED')
    return name

def _regular_bytes(path,maximum=64*1024*1024):
    before=path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_mode&0o022 or before.st_size>maximum:raise ValueError('BUILD_INPUT_FILE_REFUSED')
    raw=path.read_bytes();after=path.lstat()
    identity=lambda x:(x.st_dev,x.st_ino,x.st_mode,x.st_nlink,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
    if len(raw)!=before.st_size or identity(before)!=identity(after):raise ValueError('BUILD_INPUT_CHANGED')
    return raw

def build_repaired_r3(source,out,stop_capsule_hash,repaired_reader):
    """Exact old/new reader override into a new source and complete package.

    This is a local builder, never bootstrap/supersession or authorization.
    No original byte, inode, plan or protected runtime path is changed.
    """
    source,out,repaired_reader=Path(source),Path(out),Path(repaired_reader)
    if out.is_symlink() or out.exists() and not out.is_dir():raise ValueError('EMPTY_NEW_OUTPUT_REQUIRED')
    if out.resolve().is_relative_to(source.resolve()) or out.exists() and any(out.iterdir()):raise ValueError('EMPTY_NEW_OUTPUT_REQUIRED')
    if not isinstance(stop_capsule_hash,str) or re.fullmatch('[0-9a-f]{64}',stop_capsule_hash) is None:raise ValueError('EXACT_FIRST_STOP_CAPSULE_HASH_REQUIRED')
    freeze_raw=_regular_bytes(source/'SOURCE_FREEZE.json',16*1024*1024)
    if sha(freeze_raw)!=FROZEN_R6_FREEZE_SHA:raise ValueError('ORIGINAL_FROZEN_R6_CAPSULE_REQUIRED')
    freeze=json.loads(freeze_raw)
    if set(freeze)!={'schema','files','payloadFiles','planTemplate'} or freeze['schema']!='r16.native-recovery-source-freeze.v3' or len(freeze['files'])!=14:raise ValueError('ORIGINAL_FROZEN_R6_SCOPE_REFUSED')
    if freeze['files'].get('quiescence.py')!=ORIGINAL_READER_SHA:raise ValueError('ORIGINAL_READER_PIN_REQUIRED')
    original={}
    for name,pin in freeze['files'].items():
        raw=_regular_bytes(source/_safe_member(name),4*1024*1024)
        if sha(raw)!=pin:raise ValueError('FROZEN_SOURCE_DRIFT: '+name)
        original[name]=raw
    repaired=_regular_bytes(repaired_reader,4*1024*1024)
    if sha(repaired)!=REPAIRED_READER_SHA:raise ValueError('EXACT_REPAIRED_READER_REQUIRED')
    package=source/'package';actual=set()
    for path in package.rglob('*'):
        metadata=path.lstat()
        if stat.S_ISDIR(metadata.st_mode):
            if stat.S_IMODE(metadata.st_mode)!=0o755:raise ValueError('PACKAGE_DIRECTORY_MODE_REFUSED')
        elif stat.S_ISREG(metadata.st_mode):actual.add(str(path.relative_to(package)))
        else:raise ValueError('PACKAGE_SPECIAL_FILE_REFUSED')
    if actual!=set(freeze['payloadFiles']):raise ValueError('PACKAGE_INVENTORY_DRIFT')
    inventory_raw=_regular_bytes(package/'metadata/PAYLOAD_INVENTORY.json',16*1024*1024)
    if sha(inventory_raw)!=freeze['payloadFiles'].get('metadata/PAYLOAD_INVENTORY.json'):raise ValueError('PACKAGE_INVENTORY_PIN_REQUIRED')
    inventory=json.loads(inventory_raw)
    if not isinstance(inventory,dict):raise ValueError('PACKAGE_INVENTORY_SHAPE_REFUSED')
    modes={};total=0;payload_hashes={}
    for name,pin in freeze['payloadFiles'].items():
        _safe_member(name)
        if not name.startswith(('metadata/','payload/')):raise ValueError('PACKAGE_PATH_REFUSED')
        mode=inventory[name[len('payload/'):]]['mode'] if name.startswith('payload/') else 0o644
        if type(mode) is not int or mode&~0o755 or mode&0o022:raise ValueError('PACKAGE_MODE_REFUSED')
        raw=_regular_bytes(package/name)
        if sha(raw)!=pin or stat.S_IMODE((package/name).lstat().st_mode)!=mode:raise ValueError('PACKAGE_BYTE_OR_MODE_DRIFT')
        if name.startswith('payload/'):
            key=name[len('payload/'):];row=inventory[key]
            if row.get('sha256')!=pin or row.get('bytes')!=len(raw):raise ValueError('PACKAGE_INVENTORY_BINDING_DRIFT')
            payload_hashes[key]=pin
        total+=len(raw)
        if total>512*1024*1024:raise ValueError('PACKAGE_CAPACITY_REFUSED')
        modes[name]=mode
    # Existing R6 plan hashes the path->payload SHA map, not pretty inventory
    # metadata bytes (which carry additional baseline/provenance fields).
    if set(payload_hashes)!=set(inventory) or sha(canonical(payload_hashes))!=freeze['planTemplate']['packageInventoryHash']:raise ValueError('PACKAGE_INVENTORY_BINDING_DRIFT')
    inputs={**original,'quiescence.py':repaired}
    result={name:transform(name,raw,successor_source=R3_SOURCE,successor_cloud=R3_CLOUD) for name,raw in inputs.items() if name!='os_entry.py'}
    result['os_entry.py']=transform('os_entry.py',inputs['os_entry.py'],sha(result['quiescence.py']),successor_source=R3_SOURCE,successor_cloud=R3_CLOUD)
    updated={**freeze,'files':{name:sha(raw) for name,raw in sorted(result.items())},'planTemplate':{**freeze['planTemplate'],'firstStopCapsuleHash':stop_capsule_hash,'firstStopPolicyExceptionProposalHash':POLICY_EXCEPTION}}
    out.mkdir(parents=True,exist_ok=True);out.chmod(0o755)
    def emit(name,raw,mode):
        target=out/_safe_member(name);target.parent.mkdir(parents=True,exist_ok=True)
        cursor=target.parent
        while cursor!=out:cursor.chmod(0o755);cursor=cursor.parent
        with target.open('xb') as file:file.write(raw)
        target.chmod(mode)
    for name,raw in sorted(result.items()):emit(name,raw,0o644)
    for name,pin in sorted(freeze['payloadFiles'].items()):
        raw=_regular_bytes(package/name)
        if sha(raw)!=pin or stat.S_IMODE((package/name).lstat().st_mode)!=modes[name]:raise ValueError('PACKAGE_COPY_INPUT_CHANGED')
        emit('package/'+name,raw,modes[name])
    emit('SOURCE_FREEZE.json',canonical(updated),0o644)
    return {'schema':'r16.repaired-reader-successor-source-build.v1','originalSourceFreezeSha256':sha(freeze_raw),'originalReaderSha256':ORIGINAL_READER_SHA,'reviewedReaderOverrideSha256':sha(repaired),'sourceFreezeSha256':sha(canonical(updated)),'quiescenceSha256':sha(result['quiescence.py']),'osEntrySha256':sha(result['os_entry.py']),'sourceFiles':len(result),'physicalPackageFilesVerifiedAndCopied':len(modes),'payloadBytes':total,'payloadPinsUnchanged':updated['payloadFiles']==freeze['payloadFiles'],'targetAndTrustTemplateUnchanged':{k:v for k,v in updated['planTemplate'].items() if k not in ('firstStopCapsuleHash','firstStopPolicyExceptionProposalHash')}==freeze['planTemplate'],'localCandidateSource':R3_SOURCE,'cloudCandidateSource':R3_CLOUD,'installed':False,'newNativeApprovalRequired':True,'oldPlanAuthorityExtended':False}

if __name__=='__main__':
    import sys
    if len(sys.argv)==6 and sys.argv[1]=='--repaired-reader-r3':
        print(json.dumps(build_repaired_r3(*sys.argv[2:]),sort_keys=True));raise SystemExit(0)
    if len(sys.argv)!=4: raise SystemExit('usage: build_successor.py FROZEN_R6_SOURCE EMPTY_OUTPUT FIRST_STOP_CAPSULE_SHA256')
    print(json.dumps(build(*sys.argv[1:]),sort_keys=True))
