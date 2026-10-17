import contextlib
import fcntl
from dataclasses import replace
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import types
import unittest
from unittest import mock

HERE=Path(__file__).parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
e=module('r3_os_entry_tested',HERE/'os_entry.py')
q=module('r3_frozen_quiescence_tested',HERE/'quiescence.py')
REAL_OWNER_PUBLICATION=e.await_owner_publication
REAL_AWAIT_RECEIPT=e.await_receipt


class Crash(BaseException): pass


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.state=self.base/'state';self.code=self.base/'code';self.source=self.base/'source';self.freeze=self.base/'etc/freeze.json'
        self.state.mkdir();self.code.mkdir();self.source.mkdir()
        self.commands=[];self.effects=[];self.rows={};self.at=1000000;self.crash=None;self.hang=set();self.failed=set()
        for i,(unit,host) in enumerate(q.ROLE_HOST.items()):
            phase='SOURCE' if unit in q.ROLE_SELECTORS else 'STATIC'
            self.rows[unit]=q.Snapshot(unit,host,'active','running',100+i,0,1000+i,0,(100+i,),0,tuple(q.expected_code_pins(unit,phase).items()),None,False,send_sigkill='no',kill_signal='15',code_phase=phase)
        outer=self
        class FakeReal:
            def __init__(self): self._admitted=None
            def _bind_admitted(self,p): self._admitted=p
            def inspect(self,u,h=''): return outer.rows[u]
            def effect(self,op,u,h):
                outer.effects.append((op,u))
                # A real effect must always have a durable root journal INTENT.
                js=e.read_json(e.STATE/('cloud-os-journal.json' if e.socket.gethostname()==e.CLOUD else 'os-journal.json'))
                outer.assertEqual(js['pending']['operation'],op);outer.assertEqual(js['pending']['unit'],u)
                if (op,u) in outer.failed: raise q.Refused('SYNTHETIC_EFFECT_FAILED')
                row=outer.rows[u]
                if op=='fence': outer.rows[u]=replace(row,fence_hash=q.sha(q.fence_bytes(h)),fence_effective=True)
                elif op=='unfence':
                    if row.fence_hash!=q.sha(q.fence_bytes(h)): raise q.Refused('FOREIGN_FENCE_REFUSED')
                    outer.rows[u]=replace(row,fence_hash=None,fence_effective=False)
                elif op=='stop' and u not in outer.hang: outer.rows[u]=replace(row,active='inactive',sub='dead',main_pid=0,main_start=0,control_pid=0,control_start=0,members=())
                elif op=='start': outer.rows[u]=replace(row,active='active',sub='running',main_pid=900,main_start=9000,members=(900,))
                if outer.crash==(op,u): raise Crash()
            def fence(self,u,h): return FakeReal.effect(self,'fence',u,h)
            def unfence(self,u,h): return FakeReal.effect(self,'unfence',u,h)
            def stop(self,u,h): return FakeReal.effect(self,'stop',u,h)
            def start(self,u,h): return FakeReal.effect(self,'start',u,h)
        self.Fake=FakeReal
        patches=[mock.patch.object(e,'ROOT',self.code),mock.patch.object(e,'STATE',self.state),mock.patch.object(e,'SOURCE',self.source),mock.patch.object(e,'FREEZE',self.freeze),mock.patch.object(e,'UNIT_FILE',self.base/'etc/systemd/system'/e.UNIT),mock.patch.object(e,'HELPER',self.base/'usr/libexec/helper'),mock.patch.object(e,'SUDOERS',self.base/'etc/sudoers.d/helper'),mock.patch.object(e,'root'),mock.patch.object(e,'now_ms',side_effect=lambda:self.at),mock.patch.object(e,'secure_read',side_effect=self.fixture_read),mock.patch.object(e,'mkdir',side_effect=lambda p:Path(p).mkdir(mode=0o700,parents=True,exist_ok=True)),mock.patch.object(e,'load_q',return_value=q),mock.patch.object(e,'await_owner_publication'),mock.patch.object(e,'await_receipt',side_effect=lambda p,h:{'status':'MAINTENANCE_COMMITTED','planHash':h,'terminal':True,'businessAcceptance':False}),mock.patch.object(q,'RealBackend',FakeReal),mock.patch.object(e.subprocess,'run',side_effect=AssertionError('REAL_SUBPROCESS_PROHIBITED'))]
        for patch in patches: patch.start();self.addCleanup(patch.stop)
        self.template={'schema':'r16.native-recovery-maintenance.plan.v3','osScope':e.SCOPE,'sourcePublicConfigDigest':'1'*64,'grantHash':'2'*64,'sourceDeliveryHash':'3'*64,'sourceDeliveryRevision':16,'targetReleaseId':'fixed-target','targetNativeVersion':'fixed-native','packageInventoryHash':'4'*64}
        self.manifest={'schema':'r16.native-recovery-source-freeze.v3','files':{},'payloadFiles':{},'planTemplate':self.template}
        self.capsule=e.sha(e.canonical(self.manifest))
        self.plan={**self.template,'capsuleHash':self.capsule,'sourceFreezeHash':self.capsule,'nonce':'a'*32,'approvedAt':self.at,'expiresAt':self.at+300000,'rollbackDeadline':self.at+1800000}
        self.h=e.plan_hash(self.plan)
        self.write(self.state/'capsule.json',self.manifest);self.write(self.state/'capsule-digest.json',{'capsuleHash':self.capsule});self.write(self.code/'SOURCE_FREEZE.json',self.manifest);self.write(self.state/'plan.json',self.plan)

    def fixture_read(self,p,max_bytes=e.MAX_JSON,source=False):
        p=Path(p)
        if p.is_symlink(): raise e.Refused('FILE_REFUSED')
        raw=p.read_bytes()
        if len(raw)>max_bytes: raise e.Refused('FILE_REFUSED')
        return raw
    def write(self,p,value): p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(e.canonical(value))
    def action(self,op): return e.os_action(op)
    def baseline(self):
        cloud={'status':'CLOUD_BASELINE_SAVED','planHash':self.h,'baseline':{u:e.snapshot_json(self.rows[u]) for u in ('r16-app.service','r16-bridge.service')}}
        with mock.patch.object(e,'cloud_rpc',return_value=cloud): return self.action('baseline')
    def quiesce(self): self.baseline();return self.action('quiesce')
    def journal(self): return e.read_json(self.state/'os-journal.json')

    def test_complete_fixed_roles_quiesce_observe_activate(self):
        self.assertEqual(self.quiesce()['status'],'OS_QUIESCENT_FIXED_ROLES_ONLY')
        self.assertEqual(self.action('observe')['planHash'],self.h)
        result=self.action('activate');self.assertEqual(result['status'],'OS_ACTIVE');self.assertFalse(result['businessReadinessClaim'])
        self.assertEqual([u for op,u in self.effects if op=='stop'],list(q.STOP_ORDER))
        self.assertEqual([u for op,u in self.effects if op=='start'],list(q.START_ORDER))
        self.assertTrue(all(row.active=='active' for row in self.rows.values()))
        status=self.action('status');self.assertEqual(status['status'],'ACTUAL_FIXED_ROLES_RUNNING');self.assertEqual(len(status['actors']),4)
        self.assertFalse(status['businessReadinessClaim'])

    def test_status_checks_fresh_running_pids_not_original_baseline(self):
        self.quiesce();self.action('activate')
        u=q.START_ORDER[0];self.rows[u]=replace(self.rows[u],main_pid=991,main_start=992,members=(991,))
        self.assertEqual(self.action('status')['status'],'ACTUAL_FIXED_ROLES_RUNNING')
        self.rows[u]=replace(self.rows[u],members=())
        with self.assertRaisesRegex(e.Refused,'FIXED_ROLE_NOT_RUNNING'): self.action('status')

    def test_once_quiesce_cannot_repeat(self):
        self.quiesce();count=len(self.effects)
        self.assertEqual(self.action('quiesce')['status'],'OS_QUIESCENT_FIXED_ROLES_ONLY')
        self.assertEqual(len(self.effects),count)

    def test_crash_after_stop_before_reply_never_replays_stop(self):
        self.baseline();u=q.STOP_ORDER[0];self.crash=('stop',u)
        with self.assertRaises(Crash): self.action('quiesce')
        self.assertEqual(self.journal()['pending']['operation'],'stop')
        self.crash=None;result=self.action('resume')
        self.assertEqual(result['status'],'OS_ACTIVE')
        self.assertEqual(self.effects.count(('stop',u)),1)
        self.assertTrue(any(x['state']=='READBACK_ONLY' for x in self.journal()['events']))

    def test_crash_after_start_readback_does_not_repeat_start(self):
        self.quiesce();u=q.START_ORDER[0];self.crash=('start',u)
        with self.assertRaises(Crash): self.action('activate')
        self.crash=None;result=self.action('resume')
        self.assertEqual(result['status'],'OS_ACTIVE');self.assertEqual(self.effects.count(('start',u)),1)

    def test_unknown_start_not_accepted_does_not_retry(self):
        self.quiesce();u=q.START_ORDER[0];self.failed.add(('start',u))
        self.assertEqual(self.action('activate')['status'],'RESTORE_PARTIAL')
        self.failed.clear();self.action('resume')
        self.assertEqual(self.effects.count(('start',u)),1)

    def test_partial_activation_can_requiesce_once_before_rollback(self):
        self.quiesce();u=q.START_ORDER[1];self.failed.add(('start',u))
        self.assertEqual(self.action('activate')['status'],'RESTORE_PARTIAL');self.failed.clear()
        with mock.patch.object(e,'cloud_rpc',return_value={'cycle':1}): result=self.action('requiesce')
        self.assertEqual(result['status'],'OS_QUIESCENT_FIXED_ROLES_ONLY')
        self.assertEqual(self.journal()['cycle'],1)
        self.assertTrue(all(row.stopped() for row in self.rows.values()))
        self.assertEqual(self.action('activate')['status'],'OS_ACTIVE')
        with mock.patch.object(e,'cloud_rpc'),self.assertRaisesRegex(e.Refused,'RECOVERY_CYCLE_ALREADY_USED'): self.action('requiesce')

    def test_recovery_window_does_not_allow_forward_quiesce_after_expiry(self):
        self.quiesce();self.at=self.plan['expiresAt']+1
        with self.assertRaisesRegex(e.Refused,'PLAN_EXPIRED'): self.action('quiesce')
        self.assertEqual(self.action('resume')['status'],'OS_ACTIVE')
        self.at=self.plan['rollbackDeadline']
        with self.assertRaisesRegex(e.Refused,'PLAN_EXPIRED'): self.action('resume')

    def test_plan_template_hash_scope_nonce_windows_are_bound(self):
        for field,value in [('grantHash','bad'),('osScope','new'),('capsuleHash','0'*64),('nonce','short'),('expiresAt',self.at+300001),('rollbackDeadline',self.at+1800001)]:
            with self.subTest(field=field),self.assertRaises(e.Refused): e.validate_plan({**self.plan,field:value},self.template,self.capsule)
        with self.assertRaises(e.Refused): e.validate_plan({**self.plan,'callerApproved':True},self.template,self.capsule)

    def test_source_drift_refuses_before_os_effect(self):
        (self.code/'SOURCE_FREEZE.json').write_bytes(b'{}')
        with self.assertRaisesRegex(e.Refused,'CAPSULE_DRIFT'): self.baseline()
        self.assertEqual(self.effects,[])

    def test_pending_journal_fsynced_bytes_recovered_before_effect(self):
        self.baseline();j=self.journal();j['pending']={'operation':'stop','unit':q.STOP_ORDER[0],'sequence':0,'cycle':0}
        self.write(self.state/'.os-journal.json.pending',j)
        self.action('resume')
        self.assertFalse((self.state/'.os-journal.json.pending').exists())
        self.assertFalse(any(op=='stop' for op,_ in self.effects))

    def test_cloud_admit_once_same_plan_idempotent_and_no_extension(self):
        self.write(self.state/'admission.json',{'capsuleHash':self.capsule,'expiresAt':self.at+1800000,'unused':True})
        (self.state/'plan.json').unlink()
        self.assertFalse(e.cloud_admit('admit',self.h,self.plan)['alreadyAdmitted'])
        self.assertTrue(e.cloud_admit('admit',self.h,self.plan)['alreadyAdmitted'])
        altered={**self.plan,'nonce':'b'*32}
        with self.assertRaisesRegex(e.Refused,'CLOUD_ONCE_ADMISSION_USED'): e.cloud_admit('admit',e.digest(altered),altered)
        self.assertFalse(e.read_json(self.state/'admission.json')['unused'])

    def test_cloud_different_capsule_expiry_and_deadline_rejected(self):
        self.write(self.state/'admission.json',{'capsuleHash':self.capsule,'expiresAt':self.at+50000,'unused':True})
        with self.assertRaises(e.Refused): e.cloud_admit('admission','0'*64,None)
        with self.assertRaisesRegex(e.Refused,'CLOUD_PLAN_DRIFT'): e.cloud_admit('admit',self.h,self.plan)
        self.at+=50000
        with self.assertRaisesRegex(e.Refused,'CLOUD_ADMISSION_EXPIRED'): e.cloud_admit('admission',self.capsule,None)

    def test_cloud_role_and_shell_path_refused(self):
        for args in [['stop','r16-owner.service',self.h],['rm','/etc/passwd',self.h],['inspect','r16-app.service;id',self.h],['commit','0'*64]]:
            with self.subTest(args=args),self.assertRaises(e.Refused): e.cloud_helper(args,None)
        self.assertEqual(self.effects,[])

    def test_assert_cloud_requires_both_roles_really_stopped_and_fenced(self):
        for u in ('r16-app.service','r16-bridge.service'):
            self.rows[u]=replace(self.rows[u],active='inactive',sub='dead',main_pid=0,main_start=0,members=(),fence_hash=q.sha(q.fence_bytes(self.h)),fence_effective=True)
        self.assertEqual(len(e.assert_cloud_quiescent()['actors']),2)
        self.rows['r16-app.service']=replace(self.rows['r16-app.service'],members=(123,))
        with self.assertRaisesRegex(e.Refused,'CLOUD_NOT_QUIESCENT'): e.assert_cloud_quiescent()

    def test_cloud_publication_dispatch_has_only_fixed_node_command(self):
        with mock.patch.object(e,'command',return_value=b'{"status":"SYNTHETIC"}') as run:
            result=e.cloud_helper(['commit',self.h],{'publication':{'fixed':True}})
            self.assertEqual(result['status'],'SYNTHETIC');self.assertEqual(run.call_args.args[0],('/opt/r16/runtime/node-v24.15.0/bin/node',str(self.code/'cloud.mjs'),'commit'))

    def test_ssh_admission_uses_exact_helper_no_generic_sudo(self):
        with mock.patch.object(e,'command',return_value=b'{}') as run:
            e.cloud_rpc(q,'admit',self.h,self.plan)
            argv=run.call_args.args[0];self.assertEqual(argv[:-1],q.SSH)
            self.assertEqual(argv[-1],'/usr/bin/sudo -n '+str(e.HELPER)+' admit '+self.h)
            self.assertEqual(json.loads(run.call_args.args[1]),self.plan)

    def test_atomic_exclusive_and_source_path_traversal_failclosed(self):
        p=self.state/'once';e.atomic(p,b'one',exclusive=True)
        with self.assertRaises(FileExistsError): e.atomic(p,b'two',exclusive=True)
        self.assertEqual(p.read_bytes(),b'one')
        for path in ['/etc/passwd','../other','a/../b','a//b','a\\b']:
            with self.assertRaises(e.Refused): e.safe_rel(path)

    def test_node_canonical_utf16_order_and_safe_integer(self):
        self.assertEqual(e.canonical({'\ue000':1,'\U00010000':2}),'{"𐀀":2,"":1}'.encode())
        with self.assertRaises(e.Refused): e.canonical({'n':9007199254740992})

    def test_main_no_root_refuses_before_reading_input_or_commands(self):
        with mock.patch.object(e,'root',side_effect=e.Refused('ROOT_REQUIRED')),mock.patch.object(sys,'argv',['os_entry.py','cloud-helper','admit',self.h]),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(e.main(),78);self.assertEqual(json.loads(out.getvalue())['code'],'ROOT_REQUIRED')

    def test_bootstrap_unit_and_fixed_helper_have_no_auto_enable_or_generic_root_command(self):
        unit=e.UNIT_BYTES.decode();self.assertIn('ExecStart=/usr/bin/node /usr/lib/r16-maintenance/recovery-r6/run.mjs\n',unit)
        self.assertIn('LoadCredentialEncrypted=release-signing-key:',unit);self.assertIn('LoadCredentialEncrypted=issuer-signing-key:',unit)
        self.assertNotIn('ConditionPathExists=!',unit);self.assertIn('Restart=no',unit);self.assertNotIn('[Install]',unit)
        self.assertIn(' cloud-helper "$@"',e.HELPER_BYTES.decode());self.assertNotIn('python3 *',e.SUDOERS_BYTES.decode())

    def capsule_fixture(self):
        shutil.rmtree(self.state);shutil.rmtree(self.code)
        sources={'os_entry.py':b'synthetic entry source','quiescence.py':(HERE/'quiescence.py').read_bytes(),'run.mjs':b'synthetic transaction','context.mjs':b'synthetic context','cloud.mjs':b'synthetic cloud'}
        inv={'bin/tool':{'mode':0o755,'sha256':e.sha(b'fake executable'),'bytes':15},'lib/code.mjs':{'mode':0o644,'sha256':e.sha(b'fake code'),'bytes':9}}
        files={'payload/bin/tool':b'fake executable','payload/lib/code.mjs':b'fake code','metadata/PAYLOAD_INVENTORY.json':e.canonical(inv)}
        manifest={'schema':'r16.native-recovery-source-freeze.v3','files':{k:e.sha(v) for k,v in sources.items()},'payloadFiles':{k:e.sha(v) for k,v in files.items()},'planTemplate':self.template}
        for name,raw in sources.items(): (self.source/name).write_bytes(raw)
        for name,raw in files.items(): p=self.source/'package'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        raw=e.canonical(manifest);(self.source/'SOURCE_FREEZE.json').write_bytes(raw)
        return manifest,e.sha(raw),raw

    def test_cloud_native_bootstrap_installs_complete_sealed_capsule_and_fixed_sudoers(self):
        manifest,h,raw=self.capsule_fixture()
        with mock.patch.object(e,'command',return_value=b'') as run:
            result=e.bootstrap('bootstrap-cloud',h)
        self.assertEqual(result['status'],'CLOUD_BOOTSTRAPPED');self.assertFalse(result['productionBusinessChanged'])
        self.assertEqual((self.code/'SOURCE_FREEZE.json').read_bytes(),raw)
        for rel,pin in manifest['files'].items(): self.assertEqual(e.sha((self.code/rel).read_bytes()),pin)
        self.assertEqual((self.state/'package/payload/bin/tool').stat().st_mode&0o777,0o755)
        self.assertEqual((self.state/'package/payload/lib/code.mjs').stat().st_mode&0o777,0o644)
        self.assertEqual(e.HELPER.read_bytes(),e.HELPER_BYTES);self.assertEqual(e.SUDOERS.read_bytes(),e.SUDOERS_BYTES)
        run.assert_called_once_with(('/usr/sbin/visudo','-cf',str(e.SUDOERS)))
        expiry=result['expiresAt'];self.at+=1000
        with mock.patch.object(e,'command',return_value=b''): self.assertEqual(e.bootstrap('bootstrap-cloud',h)['expiresAt'],expiry)

    def test_native_local_bootstrap_generates_short_plan_and_starts_only_once_unit(self):
        manifest,h,raw=self.capsule_fixture();invhash=manifest['payloadFiles']['metadata/PAYLOAD_INVENTORY.json']
        def cmd(argv,data=b'',timeout=30):
            self.commands.append(tuple(argv))
            if argv==('/usr/bin/node',str(self.code/'context.mjs')):
                self.assertTrue(self.freeze.parent.is_dir(), 'metadata directory must exist before context command')
                plan=e.read_json(self.state/'plan.json')
                self.write(self.state/'context.json',{'schema':'r16.native-recovery-context.v3','planHash':e.digest(plan),'artifactsHash':'5'*64})
                self.write(self.freeze,{'schema':'r16.maintenance-source-freeze.v3','files':{str(self.code/k):v for k,v in manifest['files'].items()},'artifactsHash':'5'*64,'rollbackDeadline':plan['rollbackDeadline'],'capsuleHash':h})
            return b'{}'
        def rpc(_q,op,key='',data=None):
            if op=='admission': return {'capsuleHash':h,'unused':True,'expiresAt':self.at+1800000}
            return {'planHash':e.digest(data)}
        with mock.patch.object(e,'command',side_effect=cmd),mock.patch.object(e,'cloud_rpc',side_effect=rpc): result=e.bootstrap('bootstrap-local',h)
        self.assertEqual(result['status'],'MAINTENANCE_COMMITTED')
        plan=e.read_json(self.state/'plan.json');self.assertEqual(len(plan['nonce']),32)
        self.assertEqual(plan['expiresAt']-plan['approvedAt'],300000)
        self.assertEqual(e.UNIT_FILE.read_bytes(),e.UNIT_BYTES)
        self.assertEqual(self.commands[-1],('/usr/bin/systemctl','start','--no-block',e.UNIT))
        self.assertFalse(any('enable' in argv for argv in self.commands))

    def test_capsule_wrong_hash_and_source_byte_drift_rejected_before_install(self):
        manifest,h,raw=self.capsule_fixture()
        with self.assertRaisesRegex(e.Refused,'SOURCE_FREEZE_DRIFT'): e.verify_capsule('0'*64)
        (self.source/'cloud.mjs').write_bytes(b'drift')
        with self.assertRaisesRegex(e.Refused,'SOURCE_BYTE_DRIFT'): e.verify_capsule(h)
        self.assertFalse(self.state.exists());self.assertFalse(e.HELPER.exists())

    def test_capsule_extra_payload_and_symlink_refused(self):
        manifest,h,raw=self.capsule_fixture();(self.source/'package/metadata/extra').write_bytes(b'extra')
        with self.assertRaisesRegex(e.Refused,'PACKAGE_INVENTORY_DRIFT'): e.verify_capsule(h)
        (self.source/'package/metadata/extra').unlink();(self.source/'package/payload/bin/tool').unlink();(self.source/'package/payload/bin/tool').symlink_to('/etc/passwd')
        with self.assertRaises(e.Refused): e.bootstrap('bootstrap-cloud',h)

    def test_cloud_effect_stop_lost_reply_rejected_on_second_stop(self):
        u='r16-app.service'
        with mock.patch.object(e.socket,'gethostname',return_value=e.CLOUD):
            e.cloud_helper(['baseline',self.h],None)
            e.cloud_helper(['fence',u,self.h],None);self.crash=('stop',u)
            with self.assertRaises(Crash): e.cloud_helper(['stop',u,self.h],None)
            self.crash=None
            with self.assertRaisesRegex(e.Refused,'UNRESOLVED_OS_EFFECT'): e.cloud_helper(['stop',u,self.h],None)
            e.cloud_helper(['unfence',u,self.h],None)
            e.cloud_helper(['start',u,self.h],None)
        self.assertEqual(self.effects.count(('stop',u)),1);self.assertEqual(self.effects.count(('start',u)),1)

    def test_same_transaction_service_can_resume_but_terminal_cannot_restart(self):
        group='0::/system.slice/'+e.UNIT+'\n'
        with mock.patch.object(e.Path,'read_text',return_value=group):
            self.assertEqual(e.service_admit()['status'],'ONCE_TRANSACTION_ADMITTED')
            self.at=self.plan['expiresAt']+1
            self.assertEqual(e.service_admit()['status'],'SAME_TRANSACTION_RESUME_ADMITTED')
            self.write(self.state/'transaction-receipt.json',{'status':'SYNTHETIC_TERMINAL'})
            with self.assertRaisesRegex(e.Refused,'TRANSACTION_ALREADY_TERMINAL'): e.service_admit()

    def test_continue_only_starts_same_fixed_unit_with_existing_plan(self):
        self.write(self.state/'service-attempted.json',{'planHash':self.h})
        self.write(self.state/'context.json',{'planHash':self.h})
        e.UNIT_FILE.parent.mkdir(parents=True);e.UNIT_FILE.write_bytes(e.UNIT_BYTES)
        with mock.patch.object(e,'command',return_value=b'') as run:
            self.assertEqual(e.continue_transaction()['status'],'MAINTENANCE_COMMITTED')
            run.assert_called_once_with(('/usr/bin/systemctl','start','--no-block',e.UNIT))
            run.reset_mock();self.write(self.state/'transaction-receipt.json',{'schema':'r16.maintenance-completion.v3','status':'MAINTENANCE_COMMITTED','businessAcceptance':False})
            self.assertTrue(e.continue_transaction()['readOnly']);run.assert_not_called()

    def test_continue_submission_leaves_mutator_lock_free_for_real_execstartpre_admission(self):
        self.write(self.state/'service-attempted.json',{'planHash':self.h})
        self.write(self.state/'context.json',{'planHash':self.h})
        e.UNIT_FILE.parent.mkdir(parents=True);e.UNIT_FILE.write_bytes(e.UNIT_BYTES)
        admitted=[]
        def command(argv,*args,**kwargs):
            self.assertEqual(argv,('/usr/bin/systemctl','start','--no-block',e.UNIT))
            # This nested call opens a fresh fd and really flocks entry.lock,
            # exactly where the service's separate ExecStartPre would lock it.
            with mock.patch.object(e.Path,'read_text',return_value='0::/system.slice/'+e.UNIT+'\n'):
                admitted.append(e.execute(['service-admit'])['status'])
            self.write(self.state/'transaction-receipt.json',self.terminal_receipt())
            return b''
        with mock.patch.object(e,'command',side_effect=command),mock.patch.object(e,'await_receipt',side_effect=REAL_AWAIT_RECEIPT):
            result=e.execute(['continue'])
        self.assertEqual(admitted,['SAME_TRANSACTION_RESUME_ADMITTED']);self.assertTrue(result['terminal']);self.assertEqual(result['status'],'MAINTENANCE_COMMITTED')

    def test_live_readonly_proofs_work_under_mutator_lock_but_mutator_is_excluded(self):
        fd=os.open(self.state/'entry.lock',os.O_WRONLY|os.O_CREAT,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            self.assertEqual(e.execute(['status'])['status'],'ACTUAL_FIXED_ROLES_RUNNING')
            for u in ('r16-app.service','r16-bridge.service'):
                self.rows[u]=replace(self.rows[u],active='inactive',sub='dead',main_pid=0,main_start=0,members=(),fence_hash=q.sha(q.fence_bytes(self.h)),fence_effective=True)
            self.assertEqual(e.execute(['assert-cloud-quiescent'])['status'],'CLOUD_OS_QUIESCENT')
            with self.assertRaises(BlockingIOError): e.execute(['baseline'])
        finally: os.close(fd)

    def test_fixed_cloud_candidate_path_selected_by_hostname(self):
        with mock.patch.object(e.socket,'gethostname',return_value=e.CLOUD): self.assertEqual(e.candidate_source(),e.CLOUD_SOURCE)
        with mock.patch.object(e.socket,'gethostname',return_value=e.LOCAL): self.assertEqual(e.candidate_source(),self.source)

    def test_bootstrap_cloud_crash_points_complete_exact_missing_files_without_new_window(self):
        real=e.ensure_file
        for cut in ['source','payload','admission','helper','sudoers','freeze']:
            with self.subTest(cut=cut):
                self.capsule_reset();manifest,h,raw=self.capsule_fixture();approved=self.at;hit=[False]
                targets={'source':self.code/'os_entry.py','payload':self.state/'package/payload/bin/tool','admission':self.state/'admission.json','helper':e.HELPER,'sudoers':e.SUDOERS,'freeze':self.freeze}
                def ensure(path,data,mode=0o600):
                    real(path,data,mode)
                    if Path(path)==targets[cut] and not hit[0]: hit[0]=True;raise Crash()
                with mock.patch.object(e,'ensure_file',side_effect=ensure),mock.patch.object(e,'command',return_value=b''):
                    with self.assertRaises(Crash): e.bootstrap('bootstrap-cloud',h)
                self.at+=1000
                with mock.patch.object(e,'command',return_value=b''): result=e.bootstrap('bootstrap-cloud',h)
                self.assertTrue(hit[0]);self.assertEqual(result['expiresAt'],approved+1800000)
                self.assertEqual((self.state/'package/payload/bin/tool').read_bytes(),b'fake executable')

    def capsule_reset(self):
        for p in [self.state,self.code]:
            if p.exists(): shutil.rmtree(p)
            p.mkdir()
        for p in [self.freeze,e.UNIT_FILE,e.HELPER,e.SUDOERS]:
            if p.exists(): p.unlink()

    def test_bootstrap_local_copy_plan_context_admit_unit_start_crashes_preserve_original_plan(self):
        real=e.ensure_file
        for cut in ['source','payload','plan','context','admit','unit','reload','start']:
            with self.subTest(cut=cut):
                self.capsule_reset();manifest,h,raw=self.capsule_fixture();approved=self.at;hit=[False];cloud={'capsuleHash':h,'unused':True,'expiresAt':self.at+1800000};calls=[]
                targets={'source':self.code/'os_entry.py','payload':self.state/'package/payload/bin/tool','plan':self.state/'plan.json','unit':e.UNIT_FILE}
                def ensure(path,data,mode=0o600):
                    real(path,data,mode)
                    if cut in targets and Path(path)==targets[cut] and not hit[0]: hit[0]=True;raise Crash()
                def cmd(argv,data=b'',timeout=30):
                    calls.append(tuple(argv))
                    if argv==('/usr/bin/node',str(self.code/'context.mjs')):
                        plan=e.read_json(self.state/'plan.json')
                        self.write(self.state/'context.json',{'schema':'r16.native-recovery-context.v3','planHash':e.digest(plan),'artifactsHash':'5'*64})
                        if cut=='context' and not hit[0]: hit[0]=True;raise Crash()
                        self.write(self.freeze,{'schema':'r16.maintenance-source-freeze.v3','files':{str(self.code/k):v for k,v in manifest['files'].items()},'artifactsHash':'5'*64,'rollbackDeadline':plan['rollbackDeadline'],'capsuleHash':h})
                    if argv[:2]==('/usr/bin/systemctl','show'): return ('Id='+e.UNIT+'\nActiveState=activating\nSubState=start\nMainPID=100\nControlPID=0\n').encode()
                    if cut=='reload' and tuple(argv)==('/usr/bin/systemctl','daemon-reload') and not hit[0]: hit[0]=True;raise Crash()
                    if cut=='start' and tuple(argv)==('/usr/bin/systemctl','start','--no-block',e.UNIT) and not hit[0]: hit[0]=True;raise Crash()
                    return b'{}'
                def rpc(_q,op,key='',data=None):
                    if op=='admission': return dict(cloud)
                    cloud.update(unused=False,planHash=e.digest(data))
                    if cut=='admit' and not hit[0]: hit[0]=True;raise Crash()
                    return {'planHash':e.digest(data)}
                with mock.patch.object(e,'ensure_file',side_effect=ensure),mock.patch.object(e,'command',side_effect=cmd),mock.patch.object(e,'cloud_rpc',side_effect=rpc):
                    with self.assertRaises(Crash): e.bootstrap('bootstrap-local',h)
                old=e.read_json(self.state/'plan.json') if (self.state/'plan.json').exists() else None
                self.at+=1000
                with mock.patch.object(e,'command',side_effect=cmd),mock.patch.object(e,'cloud_rpc',side_effect=rpc): result=e.bootstrap('bootstrap-local',h)
                plan=e.read_json(self.state/'plan.json');self.assertTrue(hit[0]);self.assertEqual(plan['approvedAt'],approved);self.assertEqual(plan['expiresAt'],approved+300000)
                if old: self.assertEqual(plan,old)
                starts=[x for x in calls if x==('/usr/bin/systemctl','start','--no-block',e.UNIT)]
                self.assertEqual(len(starts),1)
                if cut=='start': self.assertEqual(result['status'],'MAINTENANCE_COMMITTED')

    def test_bootstrap_reentry_never_resets_used_admission_or_overwrites_foreign_source(self):
        self.capsule_reset();manifest,h,raw=self.capsule_fixture()
        with mock.patch.object(e,'command',return_value=b''): e.bootstrap('bootstrap-cloud',h)
        admission=e.read_json(self.state/'admission.json');admission.update(unused=False,planHash='6'*64);self.write(self.state/'admission.json',admission)
        self.at+=1000
        with mock.patch.object(e,'command',return_value=b''): e.bootstrap('bootstrap-cloud',h)
        self.assertEqual(e.read_json(self.state/'admission.json'),admission)
        (self.code/'os_entry.py').write_bytes(b'foreign')
        with mock.patch.object(e,'command'),self.assertRaisesRegex(e.Refused,'FOREIGN_INSTALLED_BYTES'): e.bootstrap('bootstrap-cloud',h)
        self.assertEqual((self.code/'os_entry.py').read_bytes(),b'foreign')

    def test_cloud_admit_crash_after_consume_completes_only_same_digest_missing_plan(self):
        self.write(self.state/'admission.json',{'capsuleHash':self.capsule,'expiresAt':self.at+1800000,'unused':False,'planHash':self.h})
        (self.state/'plan.json').unlink();self.at=self.plan['expiresAt']+1
        self.assertTrue(e.cloud_admit('admit',self.h,self.plan)['alreadyAdmitted'])
        self.assertEqual(e.read_json(self.state/'plan.json'),self.plan)
        self.assertFalse(e.read_json(self.state/'admission.json')['unused'])

    def test_just_in_time_native_app_fences_remain_when_owner_publication_is_old(self):
        self.quiesce()
        with mock.patch.object(e,'await_owner_publication',side_effect=e.Refused('OWNER_PUBLICATION_NOT_CURRENT')):
            result=self.action('activate')
        self.assertEqual(result['status'],'RESTORE_PARTIAL')
        self.assertEqual(self.rows['r16-owner.service'].active,'active')
        for u in ['r16-native.service','r16-app.service']:
            self.assertNotIn(('unfence',u),self.effects);self.assertNotIn(('start',u),self.effects);self.assertTrue(self.rows[u].fence_effective)

    def test_real_owner_barrier_binds_cache_proposal_and_published_public_config(self):
        public={'grant':{'body':{'id':'same'}},'release':{'body':{'id':'target'}},'versions':{'native':'target'}}
        config={'schema':1,'data':{'kind':'r16.owner.configuration.v1','delivery':{'revision':17,'envelope':{'body':{'schema':'r16.configuration-delivery.v1','revision':17,'publicConfig':public}}}}}
        proposal={'release':public['release'],'versions':public['versions']};plan={**self.plan,'grantHash':e.digest(public['grant'])}
        paths={Path('/var/lib/r16-owner/configuration/state.json'):config,Path('/etc/r16-owner/release-proposal.json'):proposal,Path('/run/r16-owner/public-config.json'):public}
        with mock.patch.object(e,'read_json',side_effect=lambda p,*args:paths[p]): REAL_OWNER_PUBLICATION(plan)
        paths[Path('/run/r16-owner/public-config.json')]={'old':True}
        with mock.patch.object(e,'read_json',side_effect=lambda p,*args:paths[p]),mock.patch.object(e.time,'monotonic',side_effect=[0,16]):
            with self.assertRaisesRegex(e.Refused,'OWNER_PUBLICATION_NOT_CURRENT'): REAL_OWNER_PUBLICATION(plan)
        paths[Path('/etc/r16-owner/release-proposal.json')]={'release':{},'versions':public['versions']}
        with mock.patch.object(e,'read_json',side_effect=lambda p,*args:paths[p]),self.assertRaisesRegex(e.Refused,'OWNER_PUBLICATION_BINDING_REFUSED'): REAL_OWNER_PUBLICATION(plan)

    def test_immutable_partial_pending_prefix_completes_but_foreign_prefix_refuses(self):
        path=self.state/'source.mjs';pending=self.state/'.source.mjs.pending';raw=b'approved exact source bytes'
        pending.write_bytes(raw[:9]);pending.chmod(0o644)
        e.ensure_file(path,raw,0o644)
        self.assertEqual(path.read_bytes(),raw);self.assertFalse(pending.exists())
        other=self.state/'other.mjs';temp=self.state/'.other.mjs.pending';temp.write_bytes(b'foreign prefix');temp.chmod(0o644)
        with self.assertRaisesRegex(e.Refused,'PENDING_BYTES_CONFLICT'): e.ensure_file(other,raw,0o644)
        self.assertFalse(other.exists());self.assertEqual(temp.read_bytes(),b'foreign prefix')

    def test_original_baseline_requires_non_app_roles_running_before_any_effect(self):
        u='r16-native.service';self.rows[u]=replace(self.rows[u],active='inactive',sub='dead',main_pid=0,main_start=0,members=())
        with self.assertRaisesRegex(e.Refused,'SOURCE_ROLES_NOT_RUNNING'): self.baseline()
        self.assertEqual(self.effects,[]);self.assertFalse((self.state/'os-journal.json').exists())

    def stopped_app(self):
        u='r16-app.service';self.rows[u]=replace(self.rows[u],active='inactive',sub='dead',main_pid=0,main_start=0,members=())

    def add_activation_scope(self):
        self.template['activationScope']='START_REVIEWED_TARGET_APP_IF_SOURCE_ALREADY_STOPPED'
        self.manifest['planTemplate']=self.template;self.capsule=e.sha(e.canonical(self.manifest))
        self.plan.update(activationScope=self.template['activationScope'],capsuleHash=self.capsule,sourceFreezeHash=self.capsule);self.h=e.plan_hash(self.plan)
        self.write(self.state/'capsule.json',self.manifest);self.write(self.state/'capsule-digest.json',{'capsuleHash':self.capsule});self.write(self.code/'SOURCE_FREEZE.json',self.manifest);self.write(self.state/'plan.json',self.plan)

    def test_naturally_stopped_source_app_is_saved_and_abort_restores_stopped_not_four_active(self):
        self.stopped_app();self.quiesce();self.action('resume')
        self.assertNotIn(('stop','r16-app.service'),self.effects);self.assertNotIn(('start','r16-app.service'),self.effects)
        self.assertTrue(self.rows['r16-app.service'].stopped());self.assertEqual(self.action('status')['status'],'ACTUAL_FIXED_ROLES_EXPECTED_STATE')

    def test_stopped_source_app_target_activation_requires_exact_future_scope(self):
        self.stopped_app();self.quiesce();u='r16-app.service'
        self.rows[u]=replace(self.rows[u],code_phase='TARGET',code_hashes=tuple(q.expected_code_pins(u,'TARGET').items()))
        self.assertEqual(self.action('activate')['status'],'RESTORE_PARTIAL');self.assertNotIn(('start',u),self.effects)

    def test_explicit_target_activation_then_rollback_restores_original_stopped_app(self):
        self.add_activation_scope();self.stopped_app();self.quiesce();u='r16-app.service'
        self.rows[u]=replace(self.rows[u],code_phase='TARGET',code_hashes=tuple(q.expected_code_pins(u,'TARGET').items()))
        self.assertEqual(self.action('activate')['status'],'OS_ACTIVE');self.assertIn(('start',u),self.effects)
        self.assertEqual(self.action('status')['status'],'ACTUAL_FIXED_ROLES_RUNNING')
        with mock.patch.object(e,'cloud_rpc',return_value={'status':'RECOVERY_CYCLE_STARTED'}): self.action('requiesce')
        self.rows[u]=replace(self.rows[u],code_phase='SOURCE',code_hashes=tuple(q.expected_code_pins(u,'SOURCE').items()))
        self.assertEqual(self.action('resume')['status'],'OS_ACTIVE');self.assertTrue(self.rows[u].stopped())
        self.assertEqual(self.effects.count(('start',u)),1);self.assertEqual(self.action('status')['status'],'ACTUAL_FIXED_ROLES_EXPECTED_STATE')

    def terminal_receipt(self,status='MAINTENANCE_COMMITTED'):
        return {'schema':'r16.maintenance-completion.v3','status':status,'configurationRevision':17,'completedAt':self.at,'businessAcceptance':False,'readback':{'mustNotBeProjected':'private fixture'},'rawJournal':'private fixture'}

    def test_baseline_drift_abort_before_service_changes_is_real_terminal_receipt(self):
        self.write(self.state/'transaction-receipt.json',self.terminal_receipt('ABORTED_BEFORE_SERVICE_CHANGES'))
        with mock.patch.object(e,'command') as run:
            result=e.receipt_status(self.h);run.assert_not_called()
        self.assertTrue(result['terminal']);self.assertEqual(result['status'],'ABORTED_BEFORE_SERVICE_CHANGES');self.assertFalse(result['businessAcceptance'])

    def test_historical_receipt_after_deadline_is_readonly_bounded_and_omits_private_fields(self):
        self.write(self.state/'transaction-receipt.json',self.terminal_receipt())
        self.at=self.plan['rollbackDeadline']+1000
        with mock.patch.object(e,'command') as run:
            result=e.execute(['receipt']);run.assert_not_called()
        self.assertEqual(result['planHash'],self.h);self.assertTrue(result['terminal']);self.assertTrue(result['readOnly']);self.assertFalse(result['operationAuthorityExtended'])
        self.assertNotIn('readback',result['receipt']);self.assertNotIn('rawJournal',result['receipt']);self.assertNotIn('private fixture',e.canonical(result).decode())
        with self.assertRaisesRegex(e.Refused,'PLAN_EXPIRED'): self.action('resume')

    def test_receipt_poll_returns_actual_terminal_without_any_restart(self):
        clock=[0.0];commands=[]
        def sleep(dt):
            clock[0]+=dt
            if clock[0]>=.5: self.write(self.state/'transaction-receipt.json',self.terminal_receipt('ROLLED_BACK_TO_R15_WITH_NEWER_REVISION'))
        def command(argv,*args,**kwargs):
            commands.append(tuple(argv));return ('Id='+e.UNIT+'\nActiveState=activating\nSubState=start\nMainPID=100\nControlPID=0\n').encode()
        with mock.patch.object(e.time,'monotonic',side_effect=lambda:clock[0]),mock.patch.object(e.time,'sleep',side_effect=sleep),mock.patch.object(e,'command',side_effect=command): result=REAL_AWAIT_RECEIPT(self.plan,self.h)
        self.assertEqual(result['status'],'ROLLED_BACK_TO_R15_WITH_NEWER_REVISION');self.assertTrue(result['terminal']);self.assertLess(clock[0],1)
        self.assertTrue(all(x[:2]==('/usr/bin/systemctl','show') for x in commands))

    def test_receipt_poll_pending_has_fixed_bound_and_failed_unit_reports_recovery_required(self):
        clock=[0.0]
        activating=('Id='+e.UNIT+'\nActiveState=activating\n').encode()
        with mock.patch.object(e.time,'monotonic',side_effect=lambda:clock[0]),mock.patch.object(e.time,'sleep',side_effect=lambda dt:clock.__setitem__(0,clock[0]+dt)),mock.patch.object(e,'command',return_value=activating): result=REAL_AWAIT_RECEIPT(self.plan,self.h,maximum=180)
        self.assertEqual(clock[0],180);self.assertEqual(result['status'],'PENDING_NO_TERMINAL_RECEIPT');self.assertTrue(result['waitBoundReached']);self.assertFalse(result['terminal'])
        failed=('Id='+e.UNIT+'\nActiveState=failed\n').encode()
        with mock.patch.object(e,'command',return_value=failed): result=REAL_AWAIT_RECEIPT(self.plan,self.h)
        self.assertEqual(result['status'],'RECOVERY_REQUIRED_NO_TERMINAL_RECEIPT');self.assertFalse(result['terminal'])

    def test_receipt_poll_remaining_deadline_caps_wait_and_wrong_receipt_refuses(self):
        clock=[0.0];self.at=self.plan['rollbackDeadline']-1000
        with mock.patch.object(e.time,'monotonic',side_effect=lambda:clock[0]),mock.patch.object(e.time,'sleep',side_effect=lambda dt:clock.__setitem__(0,clock[0]+dt)),mock.patch.object(e,'command',return_value=('Id='+e.UNIT+'\nActiveState=activating\n').encode()): result=REAL_AWAIT_RECEIPT(self.plan,self.h)
        self.assertEqual(clock[0],1);self.assertTrue(result['waitBoundReached'])
        self.write(self.state/'transaction-receipt.json',{'schema':'r16.maintenance-completion.v3','status':'ARBITRARY_PRIVATE_RESULT'})
        with self.assertRaisesRegex(e.Refused,'TERMINAL_RECEIPT_REFUSED'): e.receipt_projection(self.h)


    def test_baseline_binds_exact_plan_for_every_real_backend_inspection(self):
        observed=[];original=self.Fake.inspect;outer=self
        def strict(backend,u,h=''):
            outer.assertEqual(h,outer.h,'cloud helper refuses empty/mismatched plan binding')
            observed.append((u,h));return original(backend,u,h)
        with mock.patch.object(self.Fake,'inspect',strict):self.baseline()
        self.assertEqual(set(u for u,h in observed),set(q.ROLE_HOST))

    def test_exact_plan_binding_through_full_stop_observe_activation_and_status(self):
        observed=[];original=self.Fake.inspect;outer=self
        def strict(backend,u,h=''):
            outer.assertEqual(h,outer.h,'every production OS read must use the admitted plan')
            observed.append((u,h));return original(backend,u,h)
        with mock.patch.object(self.Fake,'inspect',strict):
            self.assertEqual(self.quiesce()['status'],'OS_QUIESCENT_FIXED_ROLES_ONLY')
            self.assertEqual(self.action('observe')['planHash'],self.h)
            self.assertEqual(self.action('activate')['status'],'OS_ACTIVE')
            self.assertEqual(self.action('status')['status'],'ACTUAL_FIXED_ROLES_RUNNING')
        self.assertGreater(len(observed),len(q.ROLE_HOST)*4)

    def test_graceful_stop_can_finish_after_fifteen_seconds_without_force_or_retry(self):
        self.hang.add(q.STOP_ORDER[0]);clock=[0.0];controller=q.Controller
        def sleep(seconds):
            clock[0]+=seconds
            if clock[0]>=20:
                u=q.STOP_ORDER[0];self.rows[u]=replace(self.rows[u],active='inactive',sub='dead',main_pid=0,main_start=0,control_pid=0,control_start=0,members=())
        with mock.patch.object(q,'Controller',side_effect=lambda backend:controller(backend,now=lambda:clock[0],sleep=sleep)):
            self.assertEqual(self.quiesce()['status'],'OS_QUIESCENT_FIXED_ROLES_ONLY')
        self.assertGreaterEqual(clock[0],20)
        self.assertEqual(self.effects.count(('stop',q.STOP_ORDER[0])),1)

    def test_baseline_rejects_invalid_plan_before_inspection(self):
        with self.assertRaisesRegex(q.Refused,'PLAN_HASH_REQUIRED'):q.Controller(self.Fake()).baseline('wrong')


    def test_baseline_real_exclusive_link_crash_pair_recovers_exact_new_journal(self):
        path=self.state/'cloud-os-journal.json';pending=self.state/'.cloud-os-journal.json.pending'
        rows={u:e.snapshot_json(self.rows[u]) for u in ('r16-app.service','r16-bridge.service')}
        old=e.os.unlink
        def crash(path,*args,**kwargs):
            if Path(path)==pending:raise Crash()
            return old(path,*args,**kwargs)
        with mock.patch.object(e.os,'unlink',side_effect=crash),self.assertRaises(Crash):e.Journal(path).new(self.h,rows)
        self.assertEqual(path.stat().st_nlink,2);self.assertEqual(path.stat().st_ino,pending.stat().st_ino)
        real_stat=e.os.fstat;real_lstat=Path.lstat
        class RootMetadata:
            def __init__(self,value):self.value=value
            def __getattr__(self,name):return 0 if name=='st_uid' else getattr(self.value,name)
        with mock.patch.object(e.os,'fstat',side_effect=lambda fd:RootMetadata(real_stat(fd))),mock.patch.object(Path,'lstat',lambda p:RootMetadata(real_lstat(p))):
            journal=e.Journal(path);value=journal.read()
        self.assertEqual(value['planHash'],self.h);self.assertFalse(pending.exists());self.assertEqual(path.stat().st_nlink,1)
        self.assertEqual(value['events'],[]);self.assertFalse(self.effects)

    def test_baseline_pending_pair_with_third_link_or_non_new_state_refuses(self):
        path=self.state/'cloud-os-journal.json';pending=self.state/'.cloud-os-journal.json.pending'
        rows={u:e.snapshot_json(self.rows[u]) for u in ('r16-app.service','r16-bridge.service')}
        e.Journal(path).new(self.h,rows);os.link(path,pending);third=self.state/'foreign-link';os.link(path,third)
        with self.assertRaisesRegex(e.Refused,'JOURNAL_PENDING_PAIR_REFUSED'):e.Journal(path).read()
        self.assertTrue(pending.exists());self.assertEqual(path.stat().st_nlink,3)

    def test_pending_pair_wrong_plan_or_mode_is_preserved_not_cleaned(self):
        real_stat=e.os.fstat;real_lstat=Path.lstat
        class RootMetadata:
            def __init__(self,value):self.value=value
            def __getattr__(self,name):return 0 if name=='st_uid' else getattr(self.value,name)
        rows={u:e.snapshot_json(self.rows[u]) for u in ('r16-app.service','r16-bridge.service')}
        for label,h,mode in (('wrong-plan','0'*64,0o600),('wrong-mode',self.h,0o644)):
            with self.subTest(label=label):
                path=self.state/(label+'.json');pending=self.state/('.'+label+'.json.pending')
                e.Journal(path).new(h,rows);path.chmod(mode);os.link(path,pending)
                before=path.read_bytes()
                with mock.patch.object(e.os,'fstat',side_effect=lambda fd:RootMetadata(real_stat(fd))),mock.patch.object(Path,'lstat',lambda p:RootMetadata(real_lstat(p))),self.assertRaisesRegex(e.Refused,'JOURNAL_PENDING_PAIR_REFUSED'):e.Journal(path).read()
                self.assertEqual(path.read_bytes(),before);self.assertTrue(pending.exists());self.assertEqual(path.stat().st_nlink,2)

    def test_cloud_baseline_saves_both_roles_before_any_fence_and_idempotent_exact(self):
        self.stopped_app()
        with mock.patch.object(e.socket,'gethostname',return_value=e.CLOUD):
            value=e.execute(['cloud-helper','baseline',self.h])
            raw=(self.state/'cloud-os-journal.json').read_bytes()
            self.assertEqual(set(value['baseline']),{'r16-app.service','r16-bridge.service'})
            self.assertEqual(e.execute(['cloud-helper','baseline',self.h]),value)
            self.assertEqual((self.state/'cloud-os-journal.json').read_bytes(),raw)
            js=e.read_json(self.state/'cloud-os-journal.json');self.assertEqual(js['events'],[]);self.assertIsNone(js['pending'])
            e.cloud_helper(['fence','r16-app.service',self.h],None)
            self.assertEqual(set(e.read_json(self.state/'cloud-os-journal.json')['originalBaseline']),set(value['baseline']))
        self.assertEqual(self.effects,[('fence','r16-app.service')])

    def test_cloud_baseline_drift_or_partial_existing_map_is_never_overwritten(self):
        with mock.patch.object(e.socket,'gethostname',return_value=e.CLOUD):
            e.cloud_helper(['baseline',self.h],None)
            original=(self.state/'cloud-os-journal.json').read_bytes()
            u='r16-app.service';self.rows[u]=replace(self.rows[u],main_start=9999)
            with self.assertRaisesRegex(e.Refused,'CLOUD_BASELINE_READBACK_DRIFT'):e.cloud_helper(['baseline',self.h],None)
            self.assertEqual((self.state/'cloud-os-journal.json').read_bytes(),original)
            js=e.read_json(self.state/'cloud-os-journal.json');del js['originalBaseline'][u];self.write(self.state/'cloud-os-journal.json',js)
            with self.assertRaisesRegex(e.Refused,'CLOUD_BASELINE_READBACK_DRIFT'):e.cloud_helper(['baseline',self.h],None)
        self.assertFalse(self.effects)

    def test_cloud_fence_cannot_create_partial_or_missing_baseline(self):
        with mock.patch.object(e.socket,'gethostname',return_value=e.CLOUD):
            with self.assertRaisesRegex(e.Refused,'REMOTE_COMPLETE_BASELINE_REQUIRED'):e.cloud_helper(['fence','r16-app.service',self.h],None)
        self.assertFalse((self.state/'cloud-os-journal.json').exists());self.assertFalse(self.effects)

    def test_local_baseline_requires_exact_cloud_sample_before_local_save(self):
        cloud={'status':'CLOUD_BASELINE_SAVED','planHash':self.h,'baseline':{u:e.snapshot_json(self.rows[u]) for u in ('r16-app.service','r16-bridge.service')}}
        cloud['baseline']['r16-app.service']['main_start']+=1
        with mock.patch.object(e,'cloud_rpc',return_value=cloud),self.assertRaisesRegex(e.Refused,'CLOUD_BASELINE_SAMPLE_DRIFT'):self.action('baseline')
        self.assertFalse((self.state/'os-journal.json').exists());self.assertFalse(self.effects)

    def test_local_repeated_baseline_detects_drift_without_overwrite(self):
        self.baseline();raw=(self.state/'os-journal.json').read_bytes()
        self.rows['r16-owner.service']=replace(self.rows['r16-owner.service'],main_start=90000)
        with self.assertRaisesRegex(e.Refused,'BASELINE_READBACK_DRIFT'):self.baseline()
        self.assertEqual((self.state/'os-journal.json').read_bytes(),raw);self.assertFalse(self.effects)

    def test_source_stopped_app_must_still_be_stopped_after_unfence(self):
        for drift in ({'active':'active','sub':'running','main_pid':900,'main_start':9000,'members':(900,)},
                      {'control_pid':800,'control_start':8000}, {'members':(800,)},
                      {'pending_job':True}, {'daemon_reload_needed':True}, {'code_phase':'TARGET'}):
            with self.subTest(drift=drift):
                self.stopped_app();self.quiesce();old=self.Fake.unfence;outer=self
                def change(backend,u,h):
                    old(backend,u,h)
                    if u=='r16-app.service':outer.rows[u]=replace(outer.rows[u],**drift)
                clock=[0.0]
                with mock.patch.object(self.Fake,'unfence',change),mock.patch.object(e.time,'monotonic',side_effect=lambda:clock[0]),mock.patch.object(e.time,'sleep',side_effect=lambda dt:clock.__setitem__(0,clock[0]+dt)):value=self.action('resume')
                self.assertEqual(value['status'],'RESTORE_PARTIAL');self.assertIn('r16-app.service',value['unconfirmedUnits'])
                self.assertNotIn(('start','r16-app.service'),self.effects)
                # Each subcase is a separate fresh synthetic transaction.
                (self.state/'os-journal.json').unlink();self.effects.clear()
                for i,(u,host) in enumerate(q.ROLE_HOST.items()):
                    phase='SOURCE' if u in q.ROLE_SELECTORS else 'STATIC'
                    self.rows[u]=q.Snapshot(u,host,'active','running',100+i,0,1000+i,0,(100+i,),0,tuple(q.expected_code_pins(u,phase).items()),None,False,send_sigkill='no',kill_signal='15',code_phase=phase)

    def test_stop_waits_for_final_job_settlement_without_repeating_stop(self):
        u=q.STOP_ORDER[0];clock=[0.0];controller=q.Controller;outer=self
        old=self.Fake.stop
        def stopped_job(backend,unit,h):
            old(backend,unit,h)
            if unit==u:outer.rows[u]=replace(outer.rows[u],pending_job=True)
        def sleep(seconds):
            clock[0]+=seconds
            if clock[0]>=.1:self.rows[u]=replace(self.rows[u],pending_job=False)
        with mock.patch.object(self.Fake,'stop',stopped_job),mock.patch.object(q,'Controller',side_effect=lambda backend:controller(backend,now=lambda:clock[0],sleep=sleep)):
            self.assertEqual(self.quiesce()['status'],'OS_QUIESCENT_FIXED_ROLES_ONLY')
        self.assertEqual(self.effects.count(('stop',u)),1);self.assertGreaterEqual(clock[0],.1)

    def test_permanent_stop_job_refuses_at_graceful_deadline_no_replay(self):
        u=q.STOP_ORDER[0];clock=[0.0];controller=q.Controller;outer=self;old=self.Fake.stop
        def stopped_job(backend,unit,h):
            old(backend,unit,h)
            if unit==u:outer.rows[u]=replace(outer.rows[u],pending_job=True)
        with mock.patch.object(self.Fake,'stop',stopped_job),mock.patch.object(q,'Controller',side_effect=lambda backend:controller(backend,now=lambda:clock[0],sleep=lambda seconds:clock.__setitem__(0,clock[0]+seconds))),self.assertRaisesRegex(q.Refused,'GRACEFUL_STOP_INCOMPLETE'):
            self.quiesce()
        self.assertEqual(self.effects.count(('stop',u)),1)

    def test_start_waits_for_job_settlement_without_second_start(self):
        self.stopped_app();self.quiesce();u='r16-owner.service';old=self.Fake.start;outer=self;waits=[]
        def started_job(backend,unit,h):
            old(backend,unit,h)
            if unit==u:outer.rows[u]=replace(outer.rows[u],pending_job=True)
        def settle(seconds):waits.append(seconds);self.rows[u]=replace(self.rows[u],pending_job=False)
        with mock.patch.object(self.Fake,'start',started_job),mock.patch.object(e.time,'sleep',side_effect=settle):
            self.assertEqual(self.action('resume')['status'],'OS_ACTIVE')
        self.assertTrue(waits);self.assertEqual(self.effects.count(('start',u)),1)

    def test_recovery_cannot_return_os_active_after_deadline_crossed_in_read(self):
        self.stopped_app();self.quiesce();old=self.Fake.inspect;outer=self;clock=[1.0]
        def slow(backend,unit,h=''):
            result=old(backend,unit,h)
            if unit=='r16-owner.service':outer.at=outer.plan['rollbackDeadline'];clock[0]+=1800
            return result
        with mock.patch.object(self.Fake,'inspect',slow),mock.patch.object(e.time,'monotonic',side_effect=lambda:clock[0]):self.assertEqual(self.action('resume')['status'],'RESTORE_PARTIAL')
        self.assertFalse(any(op in ('start','unfence') for op,u in self.effects))

    def test_pending_job_refuses_baseline_before_any_effect(self):
        self.rows['r16-app.service']=replace(self.rows['r16-app.service'],pending_job=True)
        with self.assertRaisesRegex(q.Refused,'PREEXISTING_FENCE_OR_UNIT_DRIFT'):self.baseline()
        self.assertFalse(self.effects)


class BootstrapEnvironmentTests(unittest.TestCase):
    def test_mutating_launcher_reports_pending_and_recovery_with_nonzero_exit(self):
        for action in ('bootstrap-local','continue'):
            for status in ('PENDING_NO_TERMINAL_RECEIPT','RECOVERY_REQUIRED_NO_TERMINAL_RECEIPT'):
                before=os.umask(0o077)
                try:
                    with mock.patch.object(e,'root'),mock.patch.object(e.sys,'argv',['os_entry.py',action]),mock.patch.object(e,'execute',return_value={'status':status,'terminal':False}),contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(e.main(),75)
                finally:os.umask(before)

    def test_terminal_and_readonly_observations_do_not_masquerade_as_pending_mutators(self):
        for action,result in [('bootstrap-local',{'status':'ABORTED_BEFORE_SERVICE_CHANGES','terminal':True}),('receipt',{'status':'RECOVERY_REQUIRED_NO_TERMINAL_RECEIPT','terminal':False})]:
            before=os.umask(0o077)
            try:
                with mock.patch.object(e,'root'),mock.patch.object(e.sys,'argv',['os_entry.py',action]),mock.patch.object(e,'execute',return_value=result),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(e.main(),0)
            finally:os.umask(before)

    def test_fixed_child_error_code_is_preserved_without_raw_stdout(self):
        result=type('Result',(),{'returncode':78,'stdout':b'{"code":"SOURCE_AUTHORITY_DRIFT"}'})()
        with mock.patch.object(e,'root'),mock.patch.object(e.subprocess,'run',return_value=result):
            with self.assertRaisesRegex(e.Refused,'SOURCE_AUTHORITY_DRIFT'):e.command(('/fixed',))

    def test_private_child_error_text_is_not_propagated(self):
        for raw in (b'private raw text',b'{"code":"not an allowed error code"}'):
            result=type('Result',(),{'returncode':78,'stdout':raw})()
            with mock.patch.object(e,'root'),mock.patch.object(e.subprocess,'run',return_value=result):
                with self.assertRaisesRegex(e.Refused,'FIXED_COMMAND_FAILED'):e.command(('/fixed',))

    def test_recursive_root_directories_all_use_explicit_0700(self):
        import stat,types
        entries={'/':0o755,'/a':0o755};created=[]
        class VirtualPath:
            def __init__(self,p):self.p=str(p)
            @property
            def parts(self):return Path(self.p).parts
            def __truediv__(self,bit):return VirtualPath(self.p.rstrip('/')+'/'+bit)
            def mkdir(self,*,mode):
                if self.p in entries:raise FileExistsError()
                entries[self.p]=mode;created.append((self.p,mode))
            def lstat(self):return types.SimpleNamespace(st_mode=stat.S_IFDIR|entries[self.p],st_uid=0)
        with mock.patch.object(e,'Path',VirtualPath):e.mkdir('/a/b/c')
        self.assertEqual(created,[('/a/b',0o700),('/a/b/c',0o700)])
        entries['/a']=0o775
        with mock.patch.object(e,'Path',VirtualPath),self.assertRaisesRegex(e.Refused,'ROOT_DIRECTORY_REFUSED'):e.mkdir('/a/b/c')

class PublicManifestReaderTests(unittest.TestCase):
    """Actual read loop on temporary files under fixed-path metadata fixtures.

    No root/production/config/command access. Fixture UID adaptation changes
    only ownership, preserving real inode/length/mode/timestamps and bytes.
    """
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.files={};self.parent_mode=0o755;self.override={};self.named_override={};self.read_calls=0
        self.backend=q.RealBackend.__new__(q.RealBackend)
    def put(self,name,raw):
        path=self.base/str(len(self.files));path.write_bytes(raw);path.chmod(0o644);self.files[name]=path;return path
    @contextlib.contextmanager
    def reader(self,*,chunk=65536,truncate=False):
        outer=self;real_open=os.open;real_read=os.read;real_fstat=os.fstat
        class RootMetadata:
            def __init__(self,value,changes=None):self.value=value;self.st_uid=0;self.__dict__.update(changes or {})
            def __getattr__(self,name):return getattr(self.value,name)
        class FixedPath:
            def __init__(self,value):self.value=str(value)
            @property
            def parts(self):return Path(self.value).parts
            def __truediv__(self,part):return FixedPath(self.value.rstrip('/')+'/'+part)
            def lstat(self):
                if self.value in outer.files:return RootMetadata(outer.files[self.value].lstat(),outer.named_override)
                return types.SimpleNamespace(st_mode=stat.S_IFDIR|outer.parent_mode,st_uid=0)
        def opened(filename,flags):
            outer.assertIn(filename,outer.files,'no production path may be opened')
            outer.assertTrue(flags&os.O_NOFOLLOW);outer.assertTrue(flags&os.O_NONBLOCK)
            return real_open(outer.files[filename],flags)
        def read(fd,length):
            outer.read_calls+=1
            if truncate and outer.read_calls>1:return b''
            return real_read(fd,min(length,chunk))
        with mock.patch.object(q,'Path',FixedPath),mock.patch.object(q.os,'open',side_effect=opened),mock.patch.object(q.os,'fstat',side_effect=lambda fd:RootMetadata(real_fstat(fd),outer.override)),mock.patch.object(q.os,'read',side_effect=read):
            yield self.backend._read_regular
    def test_app_and_native_source_and_target_real_observed_sizes_exceed_old_256k(self):
        for directory in (q.SOURCE_RELEASE,q.TARGET_RELEASE):
            for role,size in (('app',572939),('native',1183523)):
                name=directory+'/'+role+'-manifest.json';raw=b'x'*size;self.put(name,raw)
                with self.reader() as read:self.assertEqual(read(name),raw)
        self.assertEqual(len(q.PUBLIC_ROLE_MANIFESTS),4)
    def test_manifest_eight_mib_exact_bound_passes_one_byte_more_refuses(self):
        name=q.SOURCE_RELEASE+'/native-manifest.json';path=self.put(name,b'')
        with path.open('r+b') as file:file.truncate(q.ROLE_MANIFEST_MAX_BYTES)
        with self.reader() as read:self.assertEqual(len(read(name)),q.ROLE_MANIFEST_MAX_BYTES)
        with path.open('r+b') as file:file.truncate(q.ROLE_MANIFEST_MAX_BYTES+1)
        before=self.read_calls
        with self.reader() as read,self.assertRaisesRegex(q.Refused,'OS_FILE_REFUSED'):read(name)
        self.assertEqual(self.read_calls,before,'oversize metadata must refuse before reading')
    def test_other_os_files_keep_256k_bound_including_selectors_and_code(self):
        for name in ('/etc/r16-cloud/app-host.json','/run/r16-owner/public-config.json',q.SOURCE_RELEASE+'/app/app-runner.mjs','/run/systemd/system/r16-app.service.d/'+q.DROPIN_NAME):
            path=self.put(name,b'x'*q.OS_FILE_MAX_BYTES)
            with self.reader() as read:self.assertEqual(len(read(name)),q.OS_FILE_MAX_BYTES)
            with path.open('ab') as file:file.write(b'x')
            with self.reader() as read,self.assertRaisesRegex(q.Refused,'OS_FILE_REFUSED'):read(name)
    def test_suffix_lookalike_alias_or_unapproved_role_does_not_expand_bound(self):
        for name in ('/other/app-manifest.json',q.SOURCE_RELEASE+'/bridge-manifest.json',q.SOURCE_RELEASE+'/../r16-daily-20261012-r15/app-manifest.json',q.SOURCE_RELEASE+'/app-manifest.json.backup'):
            self.put(name,b'x'*(q.OS_FILE_MAX_BYTES+1))
            with self.reader() as read,self.assertRaisesRegex(q.Refused,'OS_FILE_REFUSED'):read(name)
    def test_short_regular_reads_are_accumulated_to_exact_file_length(self):
        name=q.SOURCE_RELEASE+'/native-manifest.json';raw=b'x'*1183523;self.put(name,raw)
        with self.reader(chunk=4096) as read:self.assertEqual(read(name),raw)
        self.assertGreater(self.read_calls,100)
    def test_truncated_read_replaced_path_or_changed_metadata_refuses(self):
        name=q.SOURCE_RELEASE+'/app-manifest.json';path=self.put(name,b'x'*572939)
        with self.reader(truncate=True) as read,self.assertRaisesRegex(q.Refused,'OS_FILE_DRIFT'):read(name)
        for field,value in (('st_ino',path.stat().st_ino+1),('st_mtime_ns',1),('st_ctime_ns',1),('st_uid',1000),('st_mode',stat.S_IFREG|0o600)):
            self.named_override={field:value}
            with self.reader() as read,self.assertRaisesRegex(q.Refused,'OS_FILE_DRIFT'):read(name)
    def test_large_public_file_still_needs_safe_parents_owner_inode_and_mode(self):
        name=q.SOURCE_RELEASE+'/app-manifest.json';self.put(name,b'x'*572939)
        for field,value in (('st_uid',1000),('st_nlink',2),('st_mode',stat.S_IFREG|0o666),('st_mode',stat.S_IFIFO|0o644)):
            self.override={field:value}
            with self.reader() as read,self.assertRaisesRegex(q.Refused,'OS_FILE_REFUSED'):read(name)
        self.override={};self.parent_mode=0o775
        with self.reader() as read,self.assertRaisesRegex(q.Refused,'OS_PATH_REFUSED'):read(name)
    def test_large_role_manifests_pass_actual_selector_scope_and_version_and_code_pin_checks(self):
        for unit,(role,selector,public) in q.ROLE_SELECTORS.items():
            for phase,directory in (('SOURCE',q.SOURCE_RELEASE),('TARGET',q.TARGET_RELEASE)):
                pins=q.expected_code_pins(unit,phase);files={p[len(directory)+1:]:h for p,h in pins.items() if p.startswith(directory+'/')}
                files.update({'fixture/dependency-'+str(i)+'.mjs':'a'*64 for i in range(14000 if role=='native' else 7000)})
                manifest={'schema':'r16.runtime-code.v1','role':role,'files':files};raw=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode();self.assertGreater(len(raw),262144)
                manifest_name=directory+'/'+role+'-manifest.json';self.put(manifest_name,raw)
                self.put(selector,json.dumps({'schema':'r16.'+role+'-host.v1','publicConfiguration':public,'codeManifest':manifest_name}).encode())
                versions=copy_versions={r:dict(v) for r,v in q.ROLE_VERSIONS.items()};versions[role][phase]=q.sha(raw)
                with mock.patch.object(q,'ROLE_VERSIONS',copy_versions),self.reader() as read:
                    selected,actual=q.selected_code_pins(unit,read);self.assertEqual(selected,phase);self.assertEqual(actual,pins)
                bad={r:dict(v) for r,v in versions.items()};bad[role][phase]='0'*64
                with mock.patch.object(q,'ROLE_VERSIONS',bad),self.reader() as read,self.assertRaisesRegex(q.Refused,'ROLE_MANIFEST_VERSION_DRIFT'):q.selected_code_pins(unit,read)
                required=next(name for name in files if name in {p[len(directory)+1:] for p in pins if p.startswith(directory+'/')});manifest['files'][required]='0'*64
                corrupt=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode();self.files[manifest_name].write_bytes(corrupt);versions[role][phase]=q.sha(corrupt)
                with mock.patch.object(q,'ROLE_VERSIONS',versions),self.reader() as read,self.assertRaisesRegex(q.Refused,'ROLE_MANIFEST_CODE_PIN_DRIFT'):q.selected_code_pins(unit,read)

class StableManagerAndExpiryTests(unittest.TestCase):
    def setUp(self):
        self.backend=q.RealBackend.__new__(q.RealBackend);self.backend.host=q.LOCAL;self.backend._admitted=None
        self.unit='r16-owner.service';self.h='a'*64;self.shows=[];self.clock=1.0;self.effect=[]
        self.data={'Id':self.unit,'ActiveState':'active','SubState':'running','MainPID':'200','ControlPID':'0',
                   'ControlGroup':'/system.slice/'+self.unit,'NRestarts':'0','Restart':'no','RefuseManualStart':'no',
                   'DropInPaths':'','NeedDaemonReload':'no','SendSIGKILL':'no','KillSignal':'15','Job':''}
        self.read=b'code';self.pins={'/fixed/code.py':q.sha(self.read)}
        def regular(name):
            if name==q.dropin(self.unit):raise FileNotFoundError()
            return self.read
        self.patches=[mock.patch.object(self.backend,'_root'),mock.patch.object(self.backend,'_local'),
            mock.patch.object(self.backend,'_read_regular',side_effect=regular),
            mock.patch.object(q,'selected_code_pins',return_value=('STATIC',self.pins)),
            mock.patch.object(self.backend,'_start',side_effect=lambda pid,group:1000 if pid else 0),
            mock.patch.object(self.backend,'_members',return_value=(200,)),
            mock.patch.object(self.backend,'_run',return_value=b'{"type":"a(sbbsi)","data":[]}'),
            mock.patch.object(q.time,'sleep'),mock.patch.object(q.time,'monotonic',side_effect=lambda:self.clock),
            mock.patch.object(q.subprocess,'run',side_effect=AssertionError('REAL_SUBPROCESS_PROHIBITED'))]
        for patch in self.patches:patch.start();self.addCleanup(patch.stop)
        self.manager=mock.patch.object(self.backend,'_manager',return_value=self.data).start();self.addCleanup(mock.patch.stopall)

    def test_torn_mainpid_membership_retries_only_after_lifecycle_change(self):
        stopped={**self.data,'ActiveState':'inactive','SubState':'dead','MainPID':'0','ControlGroup':''}
        self.manager.side_effect=[self.data,stopped,stopped,stopped]
        with mock.patch.object(self.backend,'_members',return_value=()):row=self.backend.inspect(self.unit,self.h)
        self.assertTrue(row.stopped());self.assertEqual(self.manager.call_count,4)

    def test_torn_controlpid_membership_resamples_only_manager_proven_change(self):
        before={**self.data,'ControlPID':'201'}
        self.manager.side_effect=[before,self.data,self.data,self.data]
        self.assertEqual(self.backend.inspect(self.unit,self.h).control_pid,0)
        self.assertEqual(self.manager.call_count,4)

    def test_disappeared_proc_with_manager_transition_can_be_resampled(self):
        stopped={**self.data,'ActiveState':'inactive','SubState':'dead','MainPID':'0','ControlGroup':''}
        self.manager.side_effect=[self.data,stopped,stopped,stopped]
        with mock.patch.object(self.backend,'_start',side_effect=lambda pid,group:(_ for _ in ()).throw(q.Refused('PID_IDENTITY_UNAVAILABLE')) if pid else 0),mock.patch.object(self.backend,'_members',return_value=()):
            self.assertTrue(self.backend.inspect(self.unit,self.h).stopped())

    def test_stable_mainpid_outside_cgroup_is_not_retried_or_suppressed(self):
        with mock.patch.object(self.backend,'_members',return_value=()),self.assertRaisesRegex(q.Refused,'MAIN_PID_OUTSIDE_CGROUP'):self.backend.inspect(self.unit,self.h)
        self.assertEqual(self.manager.call_count,2)

    def test_stable_proc_group_mismatch_and_pid_reuse_remain_hard_errors(self):
        for error in ('PID_CGROUP_DRIFT','PID_REUSED_DURING_INSPECTION'):
            with self.subTest(error=error),mock.patch.object(self.backend,'_start',side_effect=q.Refused(error)),self.assertRaisesRegex(q.Refused,error):self.backend.inspect(self.unit,self.h)
        with mock.patch.object(self.backend,'_start',side_effect=[1000,0,1001]),self.assertRaisesRegex(q.Refused,'PID_REUSED_DURING_INSPECTION'):self.backend.inspect(self.unit,self.h)

    def test_policy_drift_is_not_mistaken_for_lifecycle_race(self):
        self.manager.side_effect=[self.data,{**self.data,'MainPID':'0','Restart':'always'}]
        with self.assertRaisesRegex(q.Refused,'MANAGER_POLICY_DRIFT'):self.backend.inspect(self.unit,self.h)

    def test_repeated_manager_transition_is_bounded_and_never_mutates(self):
        self.manager.side_effect=[{**self.data,'NRestarts':str(i)} for i in range(6)]
        with self.assertRaisesRegex(q.Refused,'MANAGER_LIFECYCLE_UNSTABLE'):self.backend.inspect(self.unit,self.h)
        self.assertEqual(self.manager.call_count,6)

    def test_cgroup_members_second_read_must_match(self):
        with mock.patch.object(self.backend,'_members',side_effect=[(200,),(200,201)]),self.assertRaisesRegex(q.Refused,'CGROUP_MEMBERSHIP_DRIFT'):self.backend.inspect(self.unit,self.h)

    def test_stable_job_is_exposed_and_missing_job_field_refuses(self):
        self.manager.return_value={**self.data,'Job':'42 /org/freedesktop/systemd1/job/42'}
        self.assertTrue(self.backend.inspect(self.unit,self.h).pending_job)
        self.manager.return_value={**self.data,'Job':'0'};self.assertFalse(self.backend.inspect(self.unit,self.h).pending_job)
        # Actual manager parser, not a defaulting synthetic dictionary.
        raw='\n'.join(k+'='+v for k,v in self.data.items() if k!='Job').encode()
        with mock.patch.object(self.backend,'_run',return_value=raw),self.assertRaisesRegex(q.Refused,'MANAGER_METADATA_INCOMPLETE'):q.RealBackend._manager(self.backend,self.unit)

    def permit(self,state='ABORT_RESTORING'):
        p=q._Permit(q._BRAND,self.h,10.0,{});p.state=state;self.backend._admitted=p;return p

    def test_expired_restore_permit_has_no_bypass(self):
        self.permit();self.clock=10
        with self.assertRaisesRegex(q.Refused,'ADMISSION_EXPIRED'):self.backend._require_admitted(self.h)

    def test_slow_stop_and_start_inspection_cannot_cross_last_effect_deadline(self):
        for operation in ('stop','start'):
            self.permit();self.clock=1
            row=q.Snapshot(self.unit,q.LOCAL,'active','running',200,0,1000,0,(200,),0,(),
                           q.sha(q.fence_bytes(self.h)) if operation=='stop' else None,operation=='stop',send_sigkill='no',kill_signal='15')
            def slow(*args):self.clock=10;return row
            with mock.patch.object(self.backend,'inspect',side_effect=slow),mock.patch.object(self.backend,'_run',wraps=q.RealBackend._run.__get__(self.backend)) as run,self.assertRaisesRegex(q.Refused,'ADMISSION_EXPIRED'):getattr(self.backend,operation)(self.unit,self.h)
            self.assertEqual(run.call_count,1)

    def test_unlink_guard_is_after_slow_fence_read(self):
        self.permit()
        def slow(name):self.clock=10;return q.fence_bytes(self.h)
        with mock.patch.object(self.backend,'_read_regular',side_effect=slow),mock.patch.object(q.os,'unlink') as unlink,self.assertRaisesRegex(q.Refused,'ADMISSION_EXPIRED'):self.backend.unfence(self.unit,self.h)
        unlink.assert_not_called()

    def test_daemon_reload_guard_is_immediately_before_subprocess(self):
        self.permit();self.clock=10
        with self.assertRaisesRegex(q.Refused,'ADMISSION_EXPIRED'):q.RealBackend._run(self.backend,('/usr/bin/systemctl','daemon-reload'))

    def test_fence_file_create_rechecks_after_directory_checks(self):
        self.permit('FENCING')
        def slow(*args):self.clock=10
        with mock.patch.object(self.backend,'_mkdir_root',side_effect=slow),mock.patch.object(q.Path,'exists',return_value=False),mock.patch.object(q.os,'open') as opened,self.assertRaisesRegex(q.Refused,'ADMISSION_EXPIRED'):self.backend.fence(self.unit,self.h)
        opened.assert_not_called()

if __name__=='__main__': unittest.main()
