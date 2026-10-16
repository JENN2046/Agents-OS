import ast,copy,importlib.util,json,sys,tempfile,unittest,subprocess,shutil
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

HISTORICAL_READER = HERE/'fixtures/R6_BEFORE_STABLE_SAMPLING_quiescence.py.txt'
HISTORICAL_ENTRY = HERE/'fixtures/R6_BEFORE_STABLE_SAMPLING_os_entry.py.txt'
HISTORICAL_SOURCE_PINS = {'quiescence.py': '48e46644ae56c72229d90f7031a8c0fea682f635a20d0114c8e54dff7e4409ff', 'os_entry.py': '1b0fe40afb73e5c2833ed9ac4266de258953b9d2fef6d4b1025a70efe9c951c1', 'run.mjs': '0fe10a99ad06b991ca962ceadaf759fbc974980e1072dcbe2f5f84f26ab6ba9f', 'io.mjs': '0f0c1007dc33e6abaf5359954f4d1b6af0add79d3e3493eb1015e1792b3134b2'}

def frozen_r6_fixture_bytes(name):
    """Reconstruct only the reviewed old reader fragment, then recheck old pin.

    Keeps R6_SOURCE_PINS historical and immutable while engineering source has
    the repaired reader. This is test-only, never an installer/build override.
    """
    # Exact public pre-change bytes from reviewed Git 2f2dffd (Q/entry) and
    # 7c53be2 (transport); future runtime
    # changes cannot silently rewrite the historical R6/R3 fixture authority.
    fixture={'quiescence.py':HISTORICAL_READER,'os_entry.py':HISTORICAL_ENTRY,
             'run.mjs':HERE/'fixtures/R6_BEFORE_TRANSPORT_TIMEOUT_run.mjs.txt',
             'io.mjs':HERE/'fixtures/R6_BEFORE_TRANSPORT_TIMEOUT_io.mjs.txt'}.get(name)
    raw=(fixture if fixture else HERE.parent/'release-r6'/name).read_bytes()
    if fixture and build.sha(raw)!=HISTORICAL_SOURCE_PINS[name]:raise AssertionError('HISTORICAL_SOURCE_FIXTURE_DRIFT')
    if name=='quiescence.py' and build.sha(raw)==build.REPAIRED_READER_SHA:
        patch=json.loads((HERE/'fixtures/R6_PRE_MANIFEST_READER_FIX.json').read_bytes())
        if patch['oldReaderSha256']!=build.ORIGINAL_READER_SHA or patch['newReaderSha256']!=build.REPAIRED_READER_SHA:raise AssertionError('FROZEN_READER_FIXTURE_DRIFT')
        text=raw.decode();nodes=ast.parse(text)
        method=next(n for c in nodes.body if isinstance(c,ast.ClassDef) and c.name=='RealBackend' for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='_read_regular')
        current=''.join(text.splitlines(keepends=True)[method.lineno-1:method.end_lineno])
        text=build.replace_once(text,current,patch['oldReadRegularMethod'])
        text=build.replace_once(text,patch['newConstantBlock'],'');raw=text.encode()
    elif name=='os_entry.py':
        text=raw.decode();current='Q_SHA = '+repr(build.REPAIRED_READER_SHA)
        if current in text:raw=build.replace_once(text,current,'Q_SHA = '+repr(build.ORIGINAL_READER_SHA)).encode()
    return raw

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
                raw=frozen_r6_fixture_bytes(name)
                if build.sha(raw)!=pin:raise AssertionError('FROZEN_R6_REPOSITORY_SOURCE_DRIFT: '+name)
                target=cls.SOURCE/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);target.chmod(0o644)
            inert=b'{"schema":"isolated-inert-source-build-fixture","production":false}'
            payload=cls.SOURCE/'package/metadata/ISOLATED.json';payload.parent.mkdir(parents=True);payload.write_bytes(inert)
            freeze={'schema':'r16.native-recovery-source-freeze.v3',**pins,
                    'payloadFiles':{'metadata/ISOLATED.json':build.sha(inert)}}
            (cls.SOURCE/'SOURCE_FREEZE.json').write_bytes(build.canonical(freeze));(cls.SOURCE/'SOURCE_FREEZE.json').chmod(0o644)
        except BaseException:
            cls.source_temp.cleanup();raise
    @classmethod
    def tearDownClass(cls):cls.source_temp.cleanup()
    def r3_fixture(self,base):
        source=base/'source';shutil.copytree(self.SOURCE,source)
        package=source/'package';payload=package/'payload/bin/tool';payload.parent.mkdir(parents=True);payload.write_bytes(b'isolated executable fixture');payload.chmod(0o755)
        inventory={'bin/tool':{'mode':0o755,'bytes':payload.stat().st_size,'sha256':build.sha(payload.read_bytes())}}
        inv=package/'metadata/PAYLOAD_INVENTORY.json';inv.write_bytes(build.canonical(inventory));inv.chmod(0o644)
        freeze=json.loads((source/'SOURCE_FREEZE.json').read_bytes())
        freeze['payloadFiles']={str(p.relative_to(package)):build.sha(p.read_bytes()) for p in package.rglob('*') if p.is_file()}
        freeze['planTemplate']['packageInventoryHash']=build.sha(build.canonical({name:row['sha256'] for name,row in inventory.items()}))
        (source/'SOURCE_FREEZE.json').write_bytes(build.canonical(freeze))
        for path in source.rglob('*'):
            if path.is_dir():path.chmod(0o755)
            elif path!=payload:path.chmod(0o644)
        source.chmod(0o755)
        return source,build.sha((source/'SOURCE_FREEZE.json').read_bytes())
    def test_repaired_r3_explicit_override_builds_all_sources_payload_and_exact_new_paths(self):
        with tempfile.TemporaryDirectory(prefix='r8-repaired-build-') as tmp:
            base=Path(tmp);source,pin=self.r3_fixture(base);before={str(p.relative_to(source)):(build.sha(p.read_bytes()),p.stat().st_mode&0o777) for p in source.rglob('*') if p.is_file()}
            out=base/'new-r3'
            with mock.patch.object(build,'FROZEN_R6_FREEZE_SHA',pin):result=build.build_repaired_r3(source,out,'1'*64,HISTORICAL_READER)
            entry=module('r8_r3_repaired_entry_fixture',out/'os_entry.py');q=module('r8_r3_repaired_reader_fixture',out/'quiescence.py')
            self.assertEqual(str(entry.SOURCE),build.R3_SOURCE);self.assertEqual(str(entry.CLOUD_SOURCE),build.R3_CLOUD)
            self.assertEqual(entry.ROOT,h.SUCCESSOR_ROOT);self.assertEqual(entry.STATE,h.SUCCESSOR_STATE)
            self.assertEqual(entry.Q_SHA,build.sha((out/'quiescence.py').read_bytes()));self.assertEqual(q.ROLE_MANIFEST_MAX_BYTES,8388608)
            self.assertEqual(q.DROPIN_NAME,'93-r16-maintenance-recovery-r8.conf');self.assertEqual(q.OS_FILE_MAX_BYTES,262144)
            freeze=json.loads((out/'SOURCE_FREEZE.json').read_bytes());original=json.loads((source/'SOURCE_FREEZE.json').read_bytes())
            self.assertEqual(freeze['payloadFiles'],original['payloadFiles']);self.assertTrue(result['targetAndTrustTemplateUnchanged'])
            self.assertTrue(result['newNativeApprovalRequired']);self.assertFalse(result['oldPlanAuthorityExtended'])
            for name,sha in freeze['files'].items():self.assertEqual(build.sha((out/name).read_bytes()),sha)
            for name,sha in freeze['payloadFiles'].items():self.assertEqual(build.sha((out/'package'/name).read_bytes()),sha)
            self.assertEqual((out/'package/payload/bin/tool').stat().st_mode&0o777,0o755)
            self.assertEqual(before,{str(p.relative_to(source)):(build.sha(p.read_bytes()),p.stat().st_mode&0o777) for p in source.rglob('*') if p.is_file()})
    def test_repaired_r3_refuses_unpinned_base_or_arbitrary_replacement_before_output(self):
        with tempfile.TemporaryDirectory(prefix='r8-repaired-refuse-') as tmp:
            base=Path(tmp);source,pin=self.r3_fixture(base);out=base/'out';reader=HISTORICAL_READER
            with self.assertRaisesRegex(ValueError,'ORIGINAL_FROZEN_R6_CAPSULE_REQUIRED'):build.build_repaired_r3(source,out,'1'*64,reader)
            bad=base/'wrong-reader.py';bad.write_bytes(reader.read_bytes()+b'\n');bad.chmod(0o644)
            with mock.patch.object(build,'FROZEN_R6_FREEZE_SHA',pin),self.assertRaisesRegex(ValueError,'EXACT_REPAIRED_READER_REQUIRED'):build.build_repaired_r3(source,out,'1'*64,bad)
            self.assertFalse(out.exists())
            freeze=json.loads((source/'SOURCE_FREEZE.json').read_bytes());freeze['files']['quiescence.py']='0'*64;(source/'SOURCE_FREEZE.json').write_bytes(build.canonical(freeze))
            changed=build.sha((source/'SOURCE_FREEZE.json').read_bytes())
            with mock.patch.object(build,'FROZEN_R6_FREEZE_SHA',changed),self.assertRaisesRegex(ValueError,'ORIGINAL_READER_PIN_REQUIRED'):build.build_repaired_r3(source,out,'1'*64,reader)
            self.assertFalse(out.exists())
    def test_repaired_r3_validates_whole_original_source_and_payload_set_modes_and_bytes(self):
        for drift in ('source','extra','missing','bytes','mode','symlink'):
            with tempfile.TemporaryDirectory(prefix='r8-repaired-drift-') as tmp:
                base=Path(tmp);source,pin=self.r3_fixture(base);out=base/'out';payload=source/'package/payload/bin/tool'
                if drift=='source':(source/'run.mjs').write_bytes(b'corrupt code')
                elif drift=='extra':(source/'package/metadata/extra').write_bytes(b'extra')
                elif drift=='missing':payload.unlink()
                elif drift=='bytes':payload.write_bytes(b'corrupt bytes')
                elif drift=='mode':payload.chmod(0o644)
                else:payload.unlink();payload.symlink_to(source/'run.mjs')
                with mock.patch.object(build,'FROZEN_R6_FREEZE_SHA',pin),self.assertRaises(ValueError):build.build_repaired_r3(source,out,'1'*64,HISTORICAL_READER)
                self.assertFalse(out.exists())
    def test_repaired_r3_copy_phase_drift_never_publishes_source_freeze(self):
        with tempfile.TemporaryDirectory(prefix='r8-repaired-copy-fault-') as tmp:
            base=Path(tmp);source,pin=self.r3_fixture(base);out=base/'out';original=build._regular_bytes;calls=[]
            def drift(path,*args,**kwargs):
                raw=original(path,*args,**kwargs)
                if path==source/'package/payload/bin/tool':
                    calls.append(path)
                    if len(calls)==2:return raw+b'changed during copy'
                return raw
            with mock.patch.object(build,'FROZEN_R6_FREEZE_SHA',pin),mock.patch.object(build,'_regular_bytes',side_effect=drift),self.assertRaisesRegex(ValueError,'PACKAGE_COPY_INPUT_CHANGED'):build.build_repaired_r3(source,out,'1'*64,HISTORICAL_READER)
            self.assertFalse((out/'SOURCE_FREEZE.json').exists());self.assertFalse((out/'package/payload/bin/tool').exists())
    def test_repaired_r3_never_overwrites_nonempty_output_and_default_builder_stays_r2(self):
        with tempfile.TemporaryDirectory(prefix='r8-repaired-output-') as tmp:
            base=Path(tmp);source,pin=self.r3_fixture(base);out=base/'occupied';out.mkdir();(out/'audit').write_bytes(b'preserve')
            with mock.patch.object(build,'FROZEN_R6_FREEZE_SHA',pin),self.assertRaisesRegex(ValueError,'EMPTY_NEW_OUTPUT_REQUIRED'):build.build_repaired_r3(source,out,'1'*64,HISTORICAL_READER)
            self.assertEqual((out/'audit').read_bytes(),b'preserve')
            empty=base/'empty';empty.mkdir();link=base/'symlink-output';link.symlink_to(empty,target_is_directory=True)
            with mock.patch.object(build,'FROZEN_R6_FREEZE_SHA',pin),self.assertRaisesRegex(ValueError,'EMPTY_NEW_OUTPUT_REQUIRED'):build.build_repaired_r3(source,link,'1'*64,HISTORICAL_READER)
            self.assertEqual(list(empty.iterdir()),[])
            old=base/'old-default';build.build(self.SOURCE,old,'1'*64)
            entry=module('r8_default_source_still_r2',old/'os_entry.py')
            self.assertEqual(str(entry.SOURCE),build.NEW_SOURCE);self.assertEqual(str(entry.CLOUD_SOURCE),build.NEW_CLOUD)
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
