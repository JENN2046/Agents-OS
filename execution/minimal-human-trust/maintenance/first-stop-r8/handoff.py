"""Explicit post-stop handoff/recovery. Never invoked automatically by stop.

The original stop journal remains immutable. A separate locked, durable journal
records the new native decision. Source R6 is never treated as fence-compatible:
build_successor produces the new recovery-r8 capsule and its adoption consumer.
"""
from copy import deepcopy
import importlib.util,os,re,secrets,subprocess,sys,time
from pathlib import Path
from common_safe import need,canonical,digest,sha,parse,secure_read
import stop_driver as driver

UNIT='r16-app.service'
SUCCESSOR_ROOT=Path('/usr/lib/r16-maintenance/recovery-r8')
SUCCESSOR_STATE=Path('/var/lib/r16-maintenance/recovery-r8')
STOP_STATE=Path('/var/lib/r16-maintenance/first-stop-r8')
ADOPTION_SCHEMA='r16.first-stop-successor-adoption.v1'
POLICY_EXCEPTION='98552704b8bb8be9881318e8e8b12406448ea25f60951715a437198004ac4234'

def terminal_checkpoint(backend,approval,record,owner_required=True):
    target=approval['target'];owner=digest(approval)
    need(record.get('phase')=='TERMINAL' and record.get('signalAttemptConsumed') is True and
         record.get('approvalHash')==owner and record.get('targetHash')==digest(target), 'STOP_TERMINAL_REQUIRED')
    receipt=record.get('receipt',{})
    need(receipt.get('status')=='CONTROLLED_CRASH_STOPPED_NOT_DRAINED' and
         receipt.get('approvalHash')==owner and receipt.get('targetHash')==digest(target) and
         receipt.get('originalLedgerBytesPreserved') is True and receipt.get('cgroupEmpty') is True,
         'STOP_TERMINAL_RECEIPT_REQUIRED')
    row=driver.validate_observation(backend.inspect(target),target,owner,allow_exited=True)
    need(row['processExited'] and row['members']==[], 'EMPTY_ORIGINAL_CGROUP_REQUIRED')
    if owner_required: need(row['fenceOwner']==owner,'OWNED_STOP_FENCE_REQUIRED')
    current=driver.checkpoint_manifest(backend.checkpoint(target),approval)
    need(current==record.get('checkpoint') and digest(current)==record.get('checkpointDigest')==receipt.get('checkpointDigest'), 'STOP_CHECKPOINT_DRIFT')
    return row

def scoped(capability,key,expected):
    need(not isinstance(capability,(dict,bool)) and getattr(capability,key,None)==expected,'SEPARATE_NATIVE_SCOPE_REQUIRED')

def handoff_to_successor(*,backend,approval,stop_record,journal,successor,capability,fault=lambda p:None):
    """Caller holds RootJournal.locked and obtains exact fresh native scope.

    New plan fence is proved effective before removing the owned stop fence.
    Re-entry may finish that identical handoff but never starts a service.
    """
    owner=digest(approval);target=approval['target'];h=successor.plan_hash
    need(isinstance(approval.get('capsuleHash'),str) and re.fullmatch('[0-9a-f]{64}',approval['capsuleHash']) and
         successor.plan.get('firstStopCapsuleHash')==approval['capsuleHash'] and
         successor.plan.get('firstStopPolicyExceptionProposalHash')==POLICY_EXCEPTION,'SUCCESSOR_FIRST_STOP_SCOPE_DRIFT')
    scope={'successorPlanHash':h,'successorCapsuleHash':successor.capsule_hash,
           'stopApprovalHash':owner,'targetHash':digest(target)}
    scoped(capability,'handoff_approved',scope)
    saved=journal.read()
    if saved:
        need(saved.get('scope')==scope,'HANDOFF_SCOPE_DRIFT')
        if saved.get('phase')=='ADOPTED':
            successor.assert_effective();return {**deepcopy(saved['receipt']),'historicalReadOnly':True}
    row=terminal_checkpoint(backend,approval,stop_record,owner_required=not saved or saved['phase']!='REMOVE_STOP_INTENT')
    if not saved:
        saved={'schema':'r16.first-stop-handoff-journal.v1','scope':scope,'phase':'SUCCESSOR_FENCE_INTENT'}
        journal.write(saved);fault('journal:SUCCESSOR_FENCE_INTENT')
    # This method creates only the exact new plan's fence, or checks identical
    # already-installed bytes after an interrupted creation; it never starts.
    successor.ensure_effective();fault('effect:successor-fence')
    successor.assert_effective()
    row=terminal_checkpoint(backend,approval,stop_record,owner_required=row['fenceOwner'] is not None)
    if row['frozen']: backend.unfreeze(target,owner);fault('effect:unfreeze')
    saved['phase']='REMOVE_STOP_INTENT';journal.write(saved);fault('journal:REMOVE_STOP_INTENT')
    successor.assert_effective()
    row=terminal_checkpoint(backend,approval,stop_record,owner_required=False)
    if row['fenceOwner'] is not None:
        need(row['fenceOwner']==owner,'FOREIGN_STOP_FENCE');backend.unfence(target,owner);fault('effect:remove-stop-fence')
    successor.assert_effective()
    row=terminal_checkpoint(backend,approval,stop_record,owner_required=False)
    need(row['fenceOwner'] is None and not row['frozen'],'OLD_STOP_FENCE_NOT_RELEASED')
    receipt={'schema':ADOPTION_SCHEMA,'status':'SUCCESSOR_FENCE_ADOPTED_SOURCE_APP_STOPPED',
        **scope,'checkpointDigest':stop_record['checkpointDigest'],'successorFenceSha256':successor.fence_sha,
        'originalLedgerBytesPreserved':True,'cgroupEmpty':True,'drainStatus':'UNPROVEN',
        'serviceStarted':False,'authorityExtended':False}
    successor.publish_receipt(receipt);fault('effect:adoption-receipt')
    saved.update(phase='ADOPTED',receipt=receipt);journal.write(saved)
    return receipt

def restore_original(*,backend,approval,stop_record,journal,recovery,starter,capability,now,fault=lambda p:None):
    """Fresh root-TTY scope, source bytes intact, exactly one start attempt.

    An INTENT before thaw/unfence consumes the complete start attempt. Lost
    replies, process exits and repeated entry never authorize another start.
    Original dead-PID store locks are left to the unchanged R15 ProtectedStore.
    """
    owner=digest(approval);target=approval['target'];recovery_hash=digest(recovery)
    scope={'recoveryHash':recovery_hash,'stopApprovalHash':owner,'targetHash':digest(target)}
    scoped(capability,'recovery_approved',scope)
    need(recovery.get('schema')=='r16.first-stop-original-restore-intent.v1' and
         recovery.get('stopApprovalHash')==owner and recovery.get('targetHash')==digest(target) and
         recovery.get('checkpointDigest')==stop_record.get('checkpointDigest') and
         recovery.get('sourceHashes')==target['sourceHashes'] and
         recovery.get('actions')==['THAW_OWNED_EMPTY_CGROUP','REMOVE_OWN_STOP_FENCE','START_ORIGINAL_R15_ONCE'], 'EXACT_RECOVERY_INTENT_REQUIRED')
    saved=journal.read()
    def observe_result(saved,historical=False):
        already_restored=saved.get('phase')=='RESTORED'
        try:
            observed=starter.verify_restored(approval)
        except Exception as error:
            code=getattr(error,'code','ORIGINAL_START_OBSERVATION_UNPROVEN')
            if not isinstance(code,str) or not re.fullmatch('[A-Z0-9_]{1,80}',code): code='ORIGINAL_START_OBSERVATION_UNPROVEN'
            return {'status':'ORIGINAL_START_PENDING_READBACK_ONLY','terminal':False,
                    'automaticStartReplayAllowed':False,'historicalReadOnly':historical,'readbackOnly':historical,'code':code}
        if saved.get('phase')!='RESTORED':
            saved.update(phase='RESTORED',restored=observed);journal.write(saved)
        return {'status':'ORIGINAL_R15_RESTORED_NOT_DRAINED','terminal':True,
                'automaticStartReplayAllowed':False,'historicalReadOnly':historical and already_restored,'readbackOnly':historical,
                'businessAcceptance':False,'drainStatus':'UNPROVEN','readback':observed}
    if saved:
        need(saved.get('scope')==scope and saved.get('startAttemptConsumed') is True,'RESTORE_SCOPE_DRIFT')
        return observe_result(saved,True)
    need(type(recovery.get('approvedAt')) is int and type(recovery.get('deadline')) is int and
         recovery['approvedAt']<=now()<recovery['deadline']<=recovery['approvedAt']+300000,'RECOVERY_WINDOW_EXPIRED')
    row=terminal_checkpoint(backend,approval,stop_record)
    starter.assert_source_stopped()
    saved={'schema':'r16.first-stop-original-start-journal.v1','scope':scope,'phase':'START_INTENT',
           'startAttemptConsumed':True,'recovery':deepcopy(recovery)}
    journal.write(saved);fault('journal:START_INTENT')
    if row['frozen']: backend.unfreeze(target,owner);fault('effect:unfreeze')
    terminal_checkpoint(backend,approval,stop_record)
    need(now()<recovery['deadline'],'RECOVERY_WINDOW_EXPIRED')
    backend.unfence(target,owner);fault('effect:unfence')
    terminal_checkpoint(backend,approval,stop_record,owner_required=False)
    starter.assert_source_stopped()
    need(now()<recovery['deadline'],'RECOVERY_WINDOW_EXPIRED')
    starter.start_once();fault('effect:start-original')
    saved['phase']='START_RETURNED';journal.write(saved)
    return observe_result(saved)

class RootPhaseJournal:
    """Separate phase file protected by the already-held stop transaction lock."""
    def __init__(self,parent,name):
        need(name in ('handoff.json','restore-original.json'),'FIXED_PHASE_JOURNAL_REQUIRED')
        self.parent=parent;self.path=parent.paths.state/name
    def read(self):
        self.parent.require('journal-read');need(self.parent.lockfd is not None,'JOURNAL_LOCK_REQUIRED')
        raw=self.parent.files.read(self.path,mode=0o600,allow_missing=True)
        return None if raw is None else parse(raw)
    def write(self,value):
        self.parent.require('journal-write');need(self.parent.lockfd is not None,'JOURNAL_LOCK_REQUIRED')
        self.parent.files.atomic(self.path,canonical(value))

class RootOriginalStarter:
    def __init__(self,backend): self.backend=backend
    def assert_source_stopped(self):
        from linux_backend import SOURCE,LAUNCHER,LAUNCHER_SHA,SOURCE_HASHES,UNIT,ENV
        b=self.backend;b.system.require_root()
        need(sha(b.system.source_read(LAUNCHER))==LAUNCHER_SHA,'SOURCE_LAUNCHER_DRIFT')
        for rel,h in SOURCE_HASHES.items(): need(sha(b.system.source_read(SOURCE/rel))==h,'ORIGINAL_SOURCE_DRIFT')
        row=self.readback();need(row.get('MainPID')=='0' and row.get('ControlPID')=='0' and row.get('ActiveState') in ('inactive','failed'),'ORIGINAL_NOT_STOPPED')
        # Backend.inspect separately proves the original boot/selector/manifest,
        # no replacement PID/cgroup member, and all complete ledger bytes.
    def readback(self):
        raw=self.backend.system.run(('/usr/bin/systemctl','show',UNIT,'--property=Id,ActiveState,SubState,MainPID,ControlPID,InvocationID,NRestarts,NeedDaemonReload'))
        data=dict(line.split('=',1) for line in raw.decode().splitlines() if '=' in line)
        need(data.get('Id')==UNIT,'START_READBACK_UNIT_DRIFT');return data
    def start_once(self):
        self.backend.system.require_root()
        scope=self.backend.admission.recovery_approved
        need(isinstance(scope,dict),'NATIVE_RECOVERY_SCOPE_REQUIRED')
        saved=parse(self.backend.files.read(self.backend.paths.state/'restore-original.json',mode=0o600))
        need(saved.get('scope')==scope and saved.get('phase')=='START_INTENT' and
             saved.get('startAttemptConsumed') is True,'DURABLE_START_INTENT_REQUIRED')
        intent=saved.get('recovery',{})
        need(digest(intent)==scope.get('recoveryHash') and
             intent.get('approvedAt',0)<=self.backend.system.now()<intent.get('deadline',0),'NATIVE_RECOVERY_WINDOW_EXPIRED')
        self.backend.system.run(('/usr/bin/systemctl','start','--no-block',UNIT))
    def verify_restored(self,approval):
        from linux_backend import SOURCE,LAUNCHER,LAUNCHER_SHA,SOURCE_HASHES,ARGV,CGROUP
        b=self.backend;target=approval['target'];end=b.system.monotonic()+10
        while True:
            p=b.properties();members,frozen,requested=b._kernel_group()
            need(b.system.kernel_read('/proc/sys/kernel/random/boot_id').decode().strip()==target['bootId'],'RESTORE_BOOT_DRIFT')
            if p['ActiveState']=='active' and p['SubState']=='running' and p['MainPID'].isdigit() and int(p['MainPID'])>1:
                pid=int(p['MainPID']);start=b._proc(pid)
                need(start is not None and (pid,start)!=(target['pid'],target['startTicks']) and
                     re.fullmatch('[0-9a-f]{32}',p['InvocationID']) and p['InvocationID']!=target['invocationId'], 'RESTORE_PROCESS_IDENTITY_UNPROVEN')
                need(p['ControlPID']=='0' and p['ControlGroup']==CGROUP and members==[pid] and not frozen and not requested and
                     p['NRestarts']==str(target['nRestarts']) and p['NeedDaemonReload']=='no' and
                     p['RefuseManualStart']=='no' and p['SendSIGKILL']=='no' and p['KillSignal']=='15' and p['LimitCORE']=='0', 'RESTORE_MANAGER_STATE_UNPROVEN')
                need(all('r16-first-stop-r8.conf' not in path and 'r16-maintenance-recovery-r8.conf' not in path
                         for path in p['DropInPaths'].split()),'RESTORE_FENCE_STILL_PRESENT')
                need(b.system.kernel_read('/proc/'+str(pid)+'/cgroup').decode().strip()=='0::'+CGROUP,'RESTORE_PROCESS_CGROUP_DRIFT')
                argv=tuple(x.decode() for x in b.system.kernel_read('/proc/'+str(pid)+'/cmdline').split(b'\0') if x)
                need(argv==ARGV,'RESTORE_PROCESS_ARGV_DRIFT')
                need(sha(b.system.source_read(LAUNCHER))==LAUNCHER_SHA and
                     {rel:sha(b.system.source_read(SOURCE/rel)) for rel in SOURCE_HASHES}==SOURCE_HASHES,'RESTORE_ORIGINAL_SOURCE_DRIFT')
                successor={**target,'pid':pid,'startTicks':start,'invocationId':p['InvocationID'],'nRestarts':int(p['NRestarts'])}
                observed=b.checkpointer.capture_baseline(successor)
                need(observed['expectedOriginalUnknown']==approval['expectedOriginalUnknown'] and
                     observed['expectedLeaseBindings']==approval['expectedLeaseBindings'] and
                     observed['expectedSemanticBindingsDigest']==approval['expectedSemanticBindingsDigest'],'RESTORE_ORIGINAL_SEMANTICS_DRIFT')
                # A second kernel/manager read binds the checkpoint to the same
                # process. Do not compare whole ledger bytes after valid native
                # dead-PID lock recovery; the two original semantic pins persist.
                again=b.properties();again_members,again_frozen,again_requested=b._kernel_group()
                need(all(again[k]==p[k] for k in ('MainPID','ControlPID','InvocationID','NRestarts','ActiveState','SubState')) and
                     again_members==[pid] and not again_frozen and not again_requested and b._proc(pid)==start,'RESTORE_OBSERVATION_DRIFT')
                return {'unit':UNIT,'pid':pid,'startTicks':start,'invocationId':p['InvocationID'],
                        'singletonCgroup':True,'originalUnknownPreserved':True,'originalLeasesPreserved':True,
                        'semanticBindingsDigest':approval['expectedSemanticBindingsDigest'],'drainStatus':'UNPROVEN'}
            need(b.system.monotonic()<end,'ORIGINAL_START_NOT_CONFIRMED');b.system.sleep(.05)

class RootSuccessorCapsule:
    """Actual new capsule, not the incompatible frozen R6 entry.

    Exact capsule/plan hashes originate in the separate native scope. The
    installed capsule must independently authenticate every source file.
    """
    def __init__(self,scope):
        need(os.getuid()==os.geteuid()==0,'ROOT_REQUIRED')
        raw=secure_read(SUCCESSOR_ROOT/'SOURCE_FREEZE.json');manifest=parse(raw)
        self.capsule_hash=sha(raw)
        need(scope.get('successorCapsuleHash')==self.capsule_hash,'SUCCESSOR_NATIVE_CAPSULE_DRIFT')
        for rel,h in manifest['files'].items():
            need(rel and not rel.startswith('/') and all(x not in ('','.','..') for x in rel.split('/')),'SUCCESSOR_PATH_REFUSED')
            need(sha(secure_read(SUCCESSOR_ROOT/rel))==h,'SUCCESSOR_SOURCE_DRIFT')
        raw=secure_read(SUCCESSOR_ROOT/'os_entry.py')
        module=importlib.util.module_from_spec(importlib.util.spec_from_loader('r8_successor_root_entry',loader=None))
        sys.modules[module.__name__]=module;exec(compile(raw,str(SUCCESSOR_ROOT/'os_entry.py'),'exec'),module.__dict__)
        need(module.ROOT==SUCCESSOR_ROOT and module.STATE==SUCCESSOR_STATE,'SUCCESSOR_ROOT_REQUIRED')
        _,self.plan,self.plan_hash=module.installed_context()
        need(scope.get('successorPlanHash')==self.plan_hash,'SUCCESSOR_NATIVE_PLAN_DRIFT')
        self.entry=module;self.q=module.load_q();self.backend=self.q.RealBackend()
        need(self.backend.host==self.q.CLOUD,'FIXED_CLOUD_ROOT_REQUIRED')
        self.fence_sha=self.q.sha(self.q.fence_bytes(self.plan_hash))
    def ensure_effective(self):
        q=self.q;row=self.backend.inspect(UNIT,self.plan_hash)
        need(row.stopped() and row.code_phase=='SOURCE','SUCCESSOR_REQUIRES_ORIGINAL_STOPPED')
        if row.fence_hash:
            need(row.fence_hash==self.fence_sha,'FOREIGN_SUCCESSOR_FENCE')
            if not row.fence_effective: self.backend._run(('/usr/bin/systemctl','daemon-reload'))
        else:
            p=q._Permit(q._BRAND,self.plan_hash,time.monotonic()+max(0,self.plan['expiresAt']-self.entry.now_ms())/1000,{})
            p.state='FENCING';self.backend._bind_admitted(p);self.backend.fence(UNIT,self.plan_hash)
        return self.assert_effective()
    def assert_effective(self):
        _,_,actual_plan=self.entry.installed_context()
        need(actual_plan==self.plan_hash,'SUCCESSOR_INSTALLED_PLAN_DRIFT')
        row=self.backend.inspect(UNIT,self.plan_hash)
        need(row.stopped() and row.code_phase=='SOURCE' and row.fence_hash==self.fence_sha and
             row.fence_effective and not row.daemon_reload_needed,'SUCCESSOR_FENCE_NOT_EFFECTIVE')
        return row
    def publish_receipt(self,receipt):
        need(receipt['successorPlanHash']==self.plan_hash and receipt['successorCapsuleHash']==self.capsule_hash,'SUCCESSOR_RECEIPT_DRIFT')
        self.assert_effective();self.entry.ensure_file(SUCCESSOR_STATE/'first-stop-adoption.json',canonical(receipt))

def recover_original_native(admission,approval,parent_journal,terminal_factory,checkpointer):
    """Called only from the frozen R8 root native entry under its existing lock."""
    from linux_backend import LinuxBackend
    backend=LinuxBackend(admission,checkpointer);record=parent_journal.read()
    journal=RootPhaseJournal(parent_journal,'restore-original.json');saved=journal.read()
    if saved:
        recovery=saved['recovery']
    else:
        terminal_checkpoint(backend,approval,record)
        at=time.time_ns()//1000000
        recovery={'schema':'r16.first-stop-original-restore-intent.v1','stopApprovalHash':digest(approval),
            'targetHash':digest(approval['target']),'checkpointDigest':record['checkpointDigest'],
            'sourceHashes':approval['target']['sourceHashes'],'approvedAt':at,'deadline':at+120000,
            'nonce':secrets.token_hex(16),'actions':['THAW_OWNED_EMPTY_CGROUP','REMOVE_OWN_STOP_FENCE','START_ORIGINAL_R15_ONCE']}
        tty=terminal_factory()
        try:
            tty.say('Restore original R15 App once; keep its original dead-PID locks and every ledger byte. Native crash recovery may mark interrupted work UNKNOWN. Upstream work may continue. No automatic retry.')
            tty.confirm(recovery,'RESTORE_ORIGINAL')
        finally: tty.close()
    admission.recovery_approved={'recoveryHash':digest(recovery),'stopApprovalHash':digest(approval),'targetHash':digest(approval['target'])}
    return restore_original(backend=backend,approval=approval,stop_record=record,journal=journal,
        recovery=recovery,starter=RootOriginalStarter(backend),capability=admission,now=lambda:time.time_ns()//1000000)

def handoff_successor_native(admission,approval,parent_journal,terminal_factory,checkpointer):
    """Future explicit native action, requires separately installed new capsule.

    Never called by stop/status/recover-original and never installs that capsule.
    """
    from linux_backend import LinuxBackend
    backend=LinuxBackend(admission,checkpointer);record=parent_journal.read()
    raw=secure_read(SUCCESSOR_ROOT/'SOURCE_FREEZE.json');plan=parse(secure_read(SUCCESSOR_STATE/'plan.json'))
    scope={'successorPlanHash':digest(plan),'successorCapsuleHash':sha(raw),
           'stopApprovalHash':digest(approval),'targetHash':digest(approval['target'])}
    successor=RootSuccessorCapsule(scope)
    journal=RootPhaseJournal(parent_journal,'handoff.json');saved=journal.read()
    intent_path=parent_journal.paths.state/'handoff-native-intent.json'
    if saved:
        intent=parse(parent_journal.files.read(intent_path,mode=0o600))
        need(intent.get('scope')==scope,'NATIVE_HANDOFF_INTENT_DRIFT')
        need(saved.get('phase')=='ADOPTED' or time.time_ns()//1000000<intent['deadline'],'NATIVE_HANDOFF_EXPIRED')
    else:
        terminal_checkpoint(backend,approval,record)
        at=time.time_ns()//1000000
        intent={'schema':'r16.first-stop-native-successor-intent.v1','scope':scope,
            'checkpointDigest':record['checkpointDigest'],'approvedAt':at,'deadline':at+120000,
            'nonce':secrets.token_hex(16),'actions':['ADD_AND_PROVE_SUCCESSOR_FENCE','REMOVE_OWN_STOP_FENCE','PUBLISH_STOPPED_BASELINE_ADOPTION'],
            'mayStart':False,'mayInstall':False,'maySign':False,'drainStatus':'UNPROVEN'}
        tty=terminal_factory()
        try:
            tty.say('Adopt the stopped original App into the separately approved recovery-r8 maintenance plan. A verified successor fence replaces the stop fence with overlap; no service starts and no install/sign occurs.')
            tty.confirm(intent,'HANDOFF_TO_MAINTENANCE')
        finally:tty.close()
        parent_journal.files.atomic(intent_path,canonical(intent),immutable=True)
    admission.handoff_approved=scope
    return handoff_to_successor(backend=backend,approval=approval,stop_record=record,journal=journal,
        successor=successor,capability=admission)
