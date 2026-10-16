import copy,importlib.util,json,sys,tempfile,unittest,subprocess
from pathlib import Path
from unittest import mock

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import handoff as h
import build_successor as build
import stop_driver as d
import test_stop_driver as fixtures

class Journal:
    def __init__(self): self.value=None
    def read(self): return copy.deepcopy(self.value)
    def write(self,v): self.value=copy.deepcopy(v)

class Capability: pass

class Crash(BaseException): pass

def stopped():
    a,b,j,t=fixtures.fixture()
    a['capsuleHash']='1'*64
    d.Driver(b,j,lambda:t[0]).run(a)
    return a,b,j.read(),t

class Successor:
    def __init__(self,b):
        self.plan_hash='a'*64;self.capsule_hash='b'*64;self.fence_sha='c'*64
        self.b=b;self.effective=False;self.receipt=None;self.fail_effective=False
        self.plan={'firstStopCapsuleHash':'1'*64,'firstStopPolicyExceptionProposalHash':h.POLICY_EXCEPTION}
    def ensure_effective(self):
        self.b.effects.append('successor-fence');self.effective=not self.fail_effective
        self.assert_effective()
    def assert_effective(self): h.need(self.effective,'SUCCESSOR_FENCE_NOT_EFFECTIVE')
    def publish_receipt(self,v): self.assert_effective();self.receipt=copy.deepcopy(v)

class Tests(unittest.TestCase):
    def setup_handoff(self):
        a,b,record,t=stopped();j=Journal();s=Successor(b);cap=Capability()
        cap.handoff_approved={'successorPlanHash':s.plan_hash,'successorCapsuleHash':s.capsule_hash,
            'stopApprovalHash':h.digest(a),'targetHash':h.digest(a['target'])}
        original=b.unfence
        def remove(target,owner):
            self.assertTrue(s.effective,'UNFENCED_GAP');original(target,owner)
        b.unfence=remove
        args=dict(backend=b,approval=a,stop_record=record,journal=j,successor=s,capability=cap)
        return args,b,s,t
    def test_overlap_fence_handoff_keeps_real_receipt_and_no_start(self):
        args,b,s,t=self.setup_handoff();before=copy.deepcopy(b.files)
        result=h.handoff_to_successor(**args)
        self.assertEqual(result['schema'],h.ADOPTION_SCHEMA);self.assertIsNone(b.row['fenceOwner'])
        self.assertTrue(s.effective);self.assertEqual(b.files,before);self.assertFalse(result['serviceStarted'])
        self.assertLess(b.effects.index('successor-fence'),b.effects.index('unfence'))
        self.assertEqual(s.receipt,result)
        count=len(b.effects);self.assertTrue(h.handoff_to_successor(**args)['historicalReadOnly']);self.assertEqual(len(b.effects),count)
    def test_successor_not_effective_never_removes_stop_fence(self):
        args,b,s,t=self.setup_handoff();s.fail_effective=True
        with self.assertRaisesRegex(Exception,'SUCCESSOR_FENCE_NOT_EFFECTIVE'):h.handoff_to_successor(**args)
        self.assertIsNotNone(b.row['fenceOwner']);self.assertNotIn('unfence',b.effects)
    def test_fault_checkpoints_never_create_gap_and_resume_identical_handoff(self):
        points=('journal:SUCCESSOR_FENCE_INTENT','effect:successor-fence','journal:REMOVE_STOP_INTENT','effect:remove-stop-fence','effect:adoption-receipt')
        for point in points:
            with self.subTest(point=point):
                args,b,s,t=self.setup_handoff()
                def fault(at):
                    if at==point:raise Crash()
                with self.assertRaises(Crash):h.handoff_to_successor(**args,fault=fault)
                self.assertTrue(b.row['fenceOwner'] is not None or s.effective)
                self.assertEqual(h.handoff_to_successor(**args)['status'],'SUCCESSOR_FENCE_ADOPTED_SOURCE_APP_STOPPED')
    def test_manifest_pid_cgroup_and_native_scope_drift_refuse(self):
        for variant in ('ledger','members','source','scope'):
            with self.subTest(variant=variant):
                args,b,s,t=self.setup_handoff()
                if variant=='ledger':b.files['host/archive-example.json']['bytes']=b'{"changed":true}'
                if variant=='members':b.row['members']=[777]
                if variant=='source':b.row['sourceHashes']={}
                if variant=='scope':args['capability'].handoff_approved=True
                with self.assertRaises(Exception):h.handoff_to_successor(**args)
                self.assertNotIn('unfence',b.effects)
    def setup_restore(self):
        a,b,record,t=stopped();j=Journal();cap=Capability()
        recovery={'schema':'r16.first-stop-original-restore-intent.v1','stopApprovalHash':h.digest(a),
            'targetHash':h.digest(a['target']),'checkpointDigest':record['checkpointDigest'],
            'sourceHashes':a['target']['sourceHashes'],'approvedAt':t[0],'deadline':t[0]+120000,
            'nonce':'d'*32,'actions':['THAW_OWNED_EMPTY_CGROUP','REMOVE_OWN_STOP_FENCE','START_ORIGINAL_R15_ONCE']}
        cap.recovery_approved={'recoveryHash':h.digest(recovery),'stopApprovalHash':h.digest(a),'targetHash':h.digest(a['target'])}
        class Starter:
            calls=0
            def assert_source_stopped(inner):self.assertEqual(b.row['members'],[])
            def start_once(inner):
                self.assertTrue(j.value['startAttemptConsumed']);self.assertEqual(j.value['phase'],'START_INTENT')
                self.assertIsNone(b.row['fenceOwner']);inner.calls+=1
            def readback(inner):return {'Id':h.UNIT,'startCalls':inner.calls}
            def verify_restored(inner,approval):
                h.need(inner.calls==1,'ORIGINAL_START_NOT_CONFIRMED');return inner.readback()
        starter=Starter()
        return dict(backend=b,approval=a,stop_record=record,journal=j,recovery=recovery,starter=starter,capability=cap,now=lambda:t[0]),b,t
    def test_original_start_requires_new_intent_and_is_at_most_once(self):
        args,b,t=self.setup_restore();before=copy.deepcopy(b.files)
        self.assertEqual(h.restore_original(**args)['status'],'ORIGINAL_R15_RESTORED_NOT_DRAINED')
        for _ in range(3):self.assertFalse(h.restore_original(**args)['automaticStartReplayAllowed'])
        self.assertEqual(args['starter'].calls,1);self.assertEqual(b.files,before)
    def test_fault_before_or_after_start_consumes_attempt_no_automatic_replay(self):
        for point in ('journal:START_INTENT','effect:unfence','effect:start-original'):
            args,b,t=self.setup_restore()
            def fault(at):
                if at==point:raise Crash()
            with self.assertRaises(Crash):h.restore_original(**args,fault=fault)
            before=args['starter'].calls
            self.assertTrue(h.restore_original(**args)['readbackOnly']);self.assertEqual(args['starter'].calls,before)
    def test_expired_or_changed_restore_refuses_before_unfence(self):
        args,b,t=self.setup_restore();t[0]=args['recovery']['deadline']
        with self.assertRaisesRegex(Exception,'RECOVERY_WINDOW_EXPIRED'):h.restore_original(**args)
        self.assertNotIn('unfence',b.effects);self.assertEqual(args['starter'].calls,0)

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Real reviewed R6 source bytes/pins; only payload inventory is a tiny
        # inert fixture. This is source integration, never physical acceptance.
        pins=json.loads((HERE/'fixtures/R6_SOURCE_PINS.json').read_bytes())
        cls.source_temp=tempfile.TemporaryDirectory(prefix='r8-reviewed-source-fixture-')
        cls.SOURCE=Path(cls.source_temp.name)/'frozen-r6';cls.SOURCE.mkdir()
        try:
            for name,pin in pins['files'].items():
                if name.startswith('/') or any(x in ('','.','..') for x in name.split('/')):raise AssertionError('FIXTURE_SOURCE_PATH_REFUSED')
                raw=(HERE.parent/'release-r6'/name).read_bytes()
                if build.sha(raw)!=pin:raise AssertionError('FROZEN_R6_REPOSITORY_SOURCE_DRIFT: '+name)
                target=cls.SOURCE/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            inert=b'{"schema":"isolated-inert-source-build-fixture","production":false}'
            payload=cls.SOURCE/'package/metadata/ISOLATED.json';payload.parent.mkdir(parents=True);payload.write_bytes(inert)
            freeze={'schema':'r16.native-recovery-source-freeze.v3',**pins,
                    'payloadFiles':{'metadata/ISOLATED.json':build.sha(inert)}}
            (cls.SOURCE/'SOURCE_FREEZE.json').write_bytes(build.canonical(freeze))
        except BaseException:
            cls.source_temp.cleanup();raise
    @classmethod
    def tearDownClass(cls):cls.source_temp.cleanup()
    def test_generated_final_receipt_carries_exact_first_forced_stop_evidence(self):
        with tempfile.TemporaryDirectory(prefix='r8-first-stop-receipt-') as temp:
            out=Path(temp)/'candidate';build.build(self.SOURCE,out,'1'*64)
            entry=module('r8_first_stop_receipt_metadata',out/'os_entry.py')
            raw=(out/'SOURCE_FREEZE.json').read_bytes();capsule=build.sha(raw)
            plan={'capsuleHash':capsule,'sourceFreezeHash':capsule,'firstStopCapsuleHash':'1'*64}
            ph=entry.digest(plan)
            adoption={'schema':h.ADOPTION_SCHEMA,'status':'SUCCESSOR_FENCE_ADOPTED_SOURCE_APP_STOPPED',
                'successorPlanHash':ph,'successorCapsuleHash':capsule,'drainStatus':'UNPROVEN',
                'checkpointDigest':'c'*64,'stopApprovalHash':'d'*64,'targetHash':'e'*64,
                'cgroupEmpty':True,'originalLedgerBytesPreserved':True}
            expected={'method':'CONTROLLED_CRASH_STOP','drainStatus':'UNPROVEN',
                      **{key:adoption[key] for key in ('checkpointDigest','stopApprovalHash','targetHash')}}
            stored={'first-stop-adoption.json':adoption,'plan.json':plan,
                'transaction-receipt.json':{'schema':'r16.maintenance-completion.v3','status':'MAINTENANCE_COMMITTED','businessAcceptance':False,'firstStop':expected}}
            entry.read_json=lambda path:copy.deepcopy(stored[path.name]);entry.secure_read=lambda *args:raw
            self.assertEqual(entry.first_stop_evidence(plan,ph),expected)
            receipt=entry.receipt_projection(ph)
            self.assertFalse(receipt['businessAcceptance']);self.assertEqual(receipt['receipt']['firstStop'],expected)
            self.assertTrue(receipt['receipt']['firstStopForceUsed'])
            stored['transaction-receipt.json']['firstStop']={**expected,'drainStatus':'DRAINED'}
            with self.assertRaisesRegex(Exception,'FIRST_STOP_COMPLETION_RECEIPT_DRIFT'):entry.receipt_projection(ph)
            # Import the actual generated JS entry and exercise its real pure
            # metadata validator. No runFixedMaintenance/root path is executed.
            script="import assert from 'node:assert/strict';\nimport {firstStopEvidence} from "+json.dumps((out/'run.mjs').as_uri())+";\n"
            script+='const plan='+json.dumps(plan)+';const adoption='+json.dumps(adoption)+';const expected='+json.dumps(expected)+';\n'
            script+="assert.deepEqual(firstStopEvidence(adoption,plan),expected);\n"
            script+="for(const patch of [{drainStatus:'DRAINED'},{successorPlanHash:'f'.repeat(64)},{successorCapsuleHash:'f'.repeat(64)},{checkpointDigest:'bad'},{originalLedgerBytesPreserved:false}])assert.throws(()=>firstStopEvidence({...adoption,...patch},plan),{code:'FIRST_STOP_RECEIPT_BINDING_DRIFT'});\n"
            result=subprocess.run(['node','--input-type=module','-'],input=script.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr.decode())
            text=(out/'run.mjs').read_text()
            self.assertIn("name==='receipt'?{...v,firstStop,firstStopForceUsed:true,businessAcceptance:false}:v",text)
            self.assertIn('journal:protectedJournal(firstStop)',text)
    def test_generated_local_bootstrap_requires_remote_adoption_before_service_install_or_start(self):
        for accept in (True,False):
            with self.subTest(accept=accept),tempfile.TemporaryDirectory(prefix='r8-bootstrap-route-') as temp:
                out=Path(temp)/'candidate';build.build(self.SOURCE,out,'1'*64)
                entry=module('r8_generated_bootstrap_route_'+str(accept),out/'os_entry.py')
                raw=(out/'SOURCE_FREEZE.json').read_bytes();freeze=json.loads(raw);capsule=build.sha(raw)
                entry.ROOT=out/'root';entry.STATE=out/'state';entry.FREEZE=out/'freeze.json';entry.UNIT_FILE=out/'unit.service'
                events=[];stored={}
                entry.root=lambda *args:None;entry.now_ms=lambda:1000;entry.mkdir=lambda path:None
                entry.verify_capsule=lambda h:(freeze,{},raw)
                entry.install_capsule=lambda *args:{'createdAt':1000,'state':'COPIED'}
                entry.load_q=lambda:object()
                def ensure(path,value,*args):
                    stored[str(path)]=value
                    if path==entry.UNIT_FILE:events.append('install-unit')
                entry.ensure_file=ensure
                def rpc(q,op,h='',data=None):
                    events.append(op)
                    if op=='admission':return {'capsuleHash':capsule,'unused':True,'expiresAt':1801000}
                    if op=='admit':return {'planHash':h}
                    if op=='adopt-first-stop':
                        return {'schema':h_module.ADOPTION_SCHEMA,'status':'SUCCESSOR_FENCE_ADOPTED_SOURCE_APP_STOPPED' if accept else 'BLOCKED',
                            'successorPlanHash':h,'successorCapsuleHash':capsule}
                    raise AssertionError(op)
                h_module=h;entry.cloud_rpc=rpc
                def read(path,*args):
                    if path.name=='context.json':
                        plan=json.loads(stored[str(entry.STATE/'plan.json')])
                        return {'schema':'r16.native-recovery-context.v3','planHash':entry.digest(plan),'artifactsHash':'a'*64}
                    return json.loads(stored[str(path)])
                entry.read_json=read
                def command(argv,*args,**kwargs):
                    if 'start' in argv:events.append('start-maintenance')
                    return b'{}'
                entry.command=command
                entry.checkpoint_bootstrap=lambda record,state,**fields:record.update(state=state,**fields)
                entry.await_receipt=lambda *args:{'fixture':'accepted'}
                if accept:
                    self.assertEqual(entry.bootstrap_locked('bootstrap-local',capsule),{'fixture':'accepted'})
                    self.assertLess(events.index('adopt-first-stop'),events.index('install-unit'))
                    self.assertLess(events.index('install-unit'),events.index('start-maintenance'))
                    self.assertIn(str(entry.STATE/'first-stop-adoption.json'),stored)
                    # Once source App has handed off and maintenance can have
                    # progressed to TARGET/running, resubmission reuses the
                    # exact persisted adoption and only reconciles startIntent.
                    entry.STATE.mkdir()
                    for name in ('plan.json','first-stop-adoption.json'):
                        (entry.STATE/name).write_bytes(stored[str(entry.STATE/name)])
                    entry.recover_json=read
                    entry.install_capsule=lambda *args:{'createdAt':1000,'state':'SERVICE_START_SUBMITTED','startIntent':True}
                    entry.reconcile_service=lambda plan_hash:events.append('reconcile-start-read-only')
                    self.assertEqual(entry.bootstrap_locked('bootstrap-local',capsule),{'fixture':'accepted'})
                    self.assertEqual(events.count('adopt-first-stop'),1)
                    self.assertEqual(events.count('start-maintenance'),1)
                    self.assertIn('reconcile-start-read-only',events)
                else:
                    with self.assertRaisesRegex(Exception,'FIRST_STOP_ADOPTION_REFUSED'):entry.bootstrap_locked('bootstrap-local',capsule)
                    self.assertNotIn('install-unit',events);self.assertNotIn('start-maintenance',events)
    def test_generated_cloud_helper_executes_only_exact_newly_admitted_plan_delegation(self):
        import importlib.machinery
        with tempfile.TemporaryDirectory(prefix='r8-successor-helper-') as temp:
            out=Path(temp)/'candidate';build.build(self.SOURCE,out,'1'*64)
            entry=module('r8_generated_helper_test',out/'os_entry.py')
            freeze_raw=(out/'SOURCE_FREEZE.json').read_bytes();ph='a'*64;calls=[]
            files={name:b'isolated-root-source' for name in ('bootstrap.py','common_safe.py','native_entry.py','stop_driver.py','linux_backend.py','ledger_checkpoint.py','handoff.py','TARGET.json')}
            manifest={'schema':'r16.first-stop-capsule.v1','policyExceptionProposalHash':build.POLICY_EXCEPTION,
                'acceptedPolicyException':True,'productionStopAlreadyAuthorized':False,'files':{name:build.sha(raw) for name,raw in files.items()}}
            raw=build.canonical(manifest);stop_hash=build.sha(raw)
            plan={'firstStopCapsuleHash':stop_hash,'firstStopPolicyExceptionProposalHash':build.POLICY_EXCEPTION}
            admission={'unused':False,'planHash':ph,'capsuleHash':build.sha(freeze_raw),'expiresAt':999999}
            entry.root=lambda *args:None;entry.installed_context=lambda **kwargs:({},copy.deepcopy(plan),ph)
            entry.read_json=lambda path:copy.deepcopy(admission);entry.now_ms=lambda:100
            def read(path,*args):
                if path.name=='SOURCE_FREEZE.json':return freeze_raw
                if path.name=='CAPSULE.json':return raw
                return files[path.name]
            entry.secure_read=read
            class Loader:
                def create_module(self,spec):return None
                def exec_module(self,native):
                    native.adopt_from_successor_plan=lambda cap,p:(calls.append((cap,p)) or {'delegated':True})
            spec=importlib.machinery.ModuleSpec('r8_isolated_native_callee',Loader())
            with mock.patch.object(entry.importlib.util,'spec_from_file_location',return_value=spec):
                self.assertEqual(entry.cloud_helper(['adopt-first-stop',ph],{}),{'delegated':True})
                self.assertEqual(calls,[(stop_hash,ph)])
                for variant in ('unused','wrong-plan','expired','data','code'):
                    old=copy.deepcopy(admission)
                    if variant=='unused':admission['unused']=True
                    if variant=='wrong-plan':admission['planHash']='f'*64
                    if variant=='expired':admission['expiresAt']=99
                    if variant=='code':files['native_entry.py']=b'changed'
                    with self.assertRaises(Exception):entry.cloud_helper(['adopt-first-stop',ph],{'extra':True} if variant=='data' else {})
                    admission.clear();admission.update(old)
                    if variant=='code':files['native_entry.py']=b'isolated-root-source'
                self.assertEqual(len(calls),1)
    def test_reviewed_source_fork_and_real_baseline_adoption(self):
        before={p.name:build.sha(p.read_bytes()) for p in (self.SOURCE/'quiescence.py',self.SOURCE/'os_entry.py',self.SOURCE/'SOURCE_FREEZE.json')}
        with tempfile.TemporaryDirectory(prefix='r8-successor-source-') as temp:
            out=Path(temp)/'candidate';result=build.build(self.SOURCE,out,'1'*64)
            self.assertTrue(result['payloadPinsUnchanged']);self.assertTrue(result['targetReleaseUnchanged'])
            q=module('r8_successor_test_quiescence',out/'quiescence.py');entry=module('r8_successor_test_entry',out/'os_entry.py')
            self.assertEqual(entry.ROOT,h.SUCCESSOR_ROOT);self.assertEqual(entry.STATE,h.SUCCESSOR_STATE)
            self.assertEqual(entry.Q_SHA,build.sha((out/'quiescence.py').read_bytes()))
            self.assertEqual(q.DROPIN_NAME,'93-r16-maintenance-recovery-r8.conf')
            ph='a'*64;fh=q.sha(q.fence_bytes(ph));rows={}
            for unit,host in q.ROLE_HOST.items():
                app=unit==h.UNIT;phase='SOURCE' if unit in q.ROLE_SELECTORS else 'STATIC'
                rows[unit]=q.Snapshot(unit,host,'inactive' if app else 'active','dead' if app else 'running',0 if app else 123,0,0 if app else 111,0,() if app else (123,),0,tuple(q.expected_code_pins(unit,phase).items()),fh if app else None,app,False,'no','15',phase)
            class Backend:
                def inspect(self,unit,plan_hash=''):return rows[unit]
            controller=q.Controller(Backend())
            with self.assertRaisesRegex(Exception,'PREEXISTING_FENCE_OR_UNIT_DRIFT'):controller.baseline(ph)
            receipt={'schema':h.ADOPTION_SCHEMA,'status':'SUCCESSOR_FENCE_ADOPTED_SOURCE_APP_STOPPED',
                'successorPlanHash':ph,'successorCapsuleHash':'b'*64,'stopApprovalHash':'c'*64,'targetHash':'d'*64,
                'checkpointDigest':'e'*64,'successorFenceSha256':fh,'cgroupEmpty':True,'originalLedgerBytesPreserved':True,'drainStatus':'UNPROVEN'}
            actual=controller.baseline(ph,adoption=receipt)
            self.assertEqual(actual[h.UNIT].fence_hash,fh);self.assertTrue(actual[h.UNIT].fence_effective)
            # Execute the generated entry's real baseline caller with only OS,
            # protected-read and file-write primitives replaced by isolated
            # in-memory fixtures. Real generated Controller.baseline runs.
            freeze_raw=(out/'SOURCE_FREEZE.json').read_bytes()
            receipt['successorCapsuleHash']=build.sha(freeze_raw)
            entry.root=lambda *args:None
            entry.installed_context=lambda **kwargs:({}, {'capsuleHash':build.sha(freeze_raw),'sourceFreezeHash':build.sha(freeze_raw)}, ph)
            entry.load_q=lambda:q
            entry.read_json=lambda path:copy.deepcopy(receipt)
            entry.secure_read=lambda *args:freeze_raw
            q.RealBackend=Backend
            journals=[]
            class NoFile:
                def exists(self):return False
            class MemoryEntryJournal:
                def __init__(self,path):self.path=NoFile();journals.append(self)
                def new(self,plan_hash,baseline):self.plan_hash=plan_hash;self.baseline=baseline
            entry.Journal=MemoryEntryJournal
            self.assertEqual(entry.os_action('baseline')['status'],'BASELINE_SAVED')
            self.assertEqual(journals[-1].baseline[h.UNIT]['fence_hash'],fh)
            self.assertTrue(journals[-1].baseline[h.UNIT]['fence_effective'])
            for bad in ({**receipt,'successorPlanHash':'f'*64},{**receipt,'drainStatus':'DRAINED'}):
                with self.assertRaises(Exception):controller.baseline(ph,adoption=bad)
            rows[h.UNIT]=copy.copy(rows[h.UNIT]);object.__setattr__(rows[h.UNIT],'fence_effective',False)
            with self.assertRaisesRegex(Exception,'ADOPTED_APP_STATE_DRIFT'):controller.baseline(ph,adoption=receipt)
            os_source=(out/'os_entry.py').read_text()
            self.assertIn("baseline(h, adoption=adoption)",os_source)
            self.assertIn("first-stop-adoption.json",os_source)
            for name in ('io.mjs','run.mjs','context.mjs','publication.mjs'):
                text=(out/name).read_text();self.assertNotIn('/r16-maintenance/recovery-r6',text)
                self.assertNotIn('r16-maintenance-os-r6',text)
            self.assertIn("native.adopt_from_successor_plan(stop_hash,h)",os_source)
            self.assertLess(os_source.index("cloud_rpc(q,'adopt-first-stop',h,{})"),os_source.index('ensure_file(UNIT_FILE, UNIT_BYTES'))
            frozen=json.loads(freeze_raw)
            self.assertEqual(frozen['planTemplate']['firstStopCapsuleHash'],'1'*64)
            self.assertEqual(frozen['planTemplate']['firstStopPolicyExceptionProposalHash'],build.POLICY_EXCEPTION)
            second=Path(temp)/'second';self.assertEqual(build.build(self.SOURCE,second,'1'*64),result)
            for path in out.rglob('*'):
                if path.is_file() and path.suffix!='.pyc':self.assertEqual(path.read_bytes(),(second/path.relative_to(out)).read_bytes())
        self.assertEqual(before,{p.name:build.sha(p.read_bytes()) for p in (self.SOURCE/'quiescence.py',self.SOURCE/'os_entry.py',self.SOURCE/'SOURCE_FREEZE.json')})

class ActualStarterTests(unittest.TestCase):
    def setup_observer(self):
        import linux_backend as lb
        approval,b,record,t=stopped();target=approval['target'];pid=54321;start='987654'
        raw=b'isolated-source-byte-fixture'
        source_hashes={rel:h.sha(raw) for rel in lb.SOURCE_HASHES}
        props={'Id':h.UNIT,'MainPID':str(pid),'ControlPID':'0','ActiveState':'active','SubState':'running',
               'InvocationID':'c'*32,'ControlGroup':lb.CGROUP,'NRestarts':str(target['nRestarts']),
               'NeedDaemonReload':'no','RefuseManualStart':'no','SendSIGKILL':'no','KillSignal':'15','LimitCORE':'0','DropInPaths':''}
        class System:
            clock=0
            def require_root(self):pass
            def monotonic(self):return self.clock
            def sleep(self,seconds):self.clock+=seconds
            def source_read(self,path):return raw
            def kernel_read(self,path):
                if path.endswith('/boot_id'):return target['bootId'].encode()
                if path.endswith('/cgroup'):return ('0::'+lb.CGROUP).encode()
                if path.endswith('/cmdline'):return b'\0'.join(x.encode() for x in lb.ARGV)+b'\0'
                raise AssertionError(path)
        class Reader:
            def capture_baseline(self,observed):
                assert observed['pid']==pid and observed['startTicks']==start and observed['invocationId']==props['InvocationID']
                return {key:copy.deepcopy(approval[key]) for key in ('expectedOriginalUnknown','expectedLeaseBindings','expectedSemanticBindingsDigest')}
        class Backend:
            system=System();checkpointer=Reader()
            def properties(self):return copy.deepcopy(props)
            def _kernel_group(self):return [pid],False,False
            def _proc(self,observed_pid):return start if observed_pid==pid else None
        backend=Backend()
        return approval,backend,props,lb,source_hashes,h.sha(raw)
    def test_actual_root_starter_observer_validates_new_identity_and_semantic_readback(self):
        a,b,p,lb,pins,launcher=self.setup_observer()
        with mock.patch.object(lb,'SOURCE_HASHES',pins),mock.patch.object(lb,'LAUNCHER_SHA',launcher):
            result=h.RootOriginalStarter(b).verify_restored(a)
        self.assertTrue(result['originalUnknownPreserved']);self.assertTrue(result['singletonCgroup'])
        self.assertEqual(result['semanticBindingsDigest'],a['expectedSemanticBindingsDigest'])
    def test_actual_observer_rejects_invocation_restart_membership_and_semantics_drift(self):
        for variant in ('invocation','restart','members','semantics','fence','freeze-requested'):
            with self.subTest(variant=variant):
                a,b,p,lb,pins,launcher=self.setup_observer()
                if variant=='invocation':p['InvocationID']=a['target']['invocationId']
                if variant=='restart':p['NRestarts']='99'
                if variant=='members':b._kernel_group=lambda:([54321,777],False,False)
                if variant=='freeze-requested':b._kernel_group=lambda:([54321],False,True)
                if variant=='semantics':b.checkpointer.capture_baseline=lambda target:{'expectedOriginalUnknown':{},'expectedLeaseBindings':{},'expectedSemanticBindingsDigest':'0'*64}
                if variant=='fence':p['DropInPaths']='/run/systemd/system/'+h.UNIT+'.d/92-r16-first-stop-r8.conf'
                with mock.patch.object(lb,'SOURCE_HASHES',pins),mock.patch.object(lb,'LAUNCHER_SHA',launcher):
                    with self.assertRaises(Exception):h.RootOriginalStarter(b).verify_restored(a)
    def test_actual_observer_bounds_wait_for_nonstarted_original(self):
        a,b,p,lb,pins,launcher=self.setup_observer();p.update(ActiveState='inactive',SubState='dead',MainPID='0')
        with self.assertRaisesRegex(Exception,'ORIGINAL_START_NOT_CONFIRMED'):h.RootOriginalStarter(b).verify_restored(a)
        self.assertLessEqual(b.system.clock,10.1)

if __name__=='__main__':unittest.main()
