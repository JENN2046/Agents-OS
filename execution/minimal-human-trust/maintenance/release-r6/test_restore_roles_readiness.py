"""AST-load the actual restoration functions, with synthetic snapshots/time/OS.

No root, SSH, protected state, production services, or source-packaging effects.
The q Snapshot/phase pins are real; backend actions and journal are in memory.
"""
import ast,copy,importlib.util,sys,types,unittest
from dataclasses import replace
from pathlib import Path
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('restore_readiness_q',HERE/'quiescence.py');q=importlib.util.module_from_spec(spec);sys.modules[spec.name]=q;spec.loader.exec_module(q)
def actual_functions(namespace):
    names={'Refused','need','restore_failure_code','restore_row_guard','await_restore_ready','resolve_pending','restore_roles','os_action'}
    tree=ast.parse((HERE/'os_entry.py').read_text());nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RESTORE_FAILURE_CODES' for t in n.targets)]
    assert {n.name for n in nodes if isinstance(n,(ast.FunctionDef,ast.ClassDef))}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(HERE/'os_entry.py')+'::<actual-restoration-functions>','exec'),namespace);return namespace
class Clock:
    def __init__(self):self.at=0.0;self.waits=[]
    def monotonic(self):return self.at
    def sleep(self,seconds):self.waits.append(seconds);self.at+=seconds
class Readiness(unittest.TestCase):
    def setUp(self):
        self.clock=Clock();self.h='a'*64;self.plan={'rollbackDeadline':60000,'expiresAt':30000};self.effects=[];self.inspections=[];self.queue={};self.after_unfence=None;self.inspect_failure=None;self.start_failure=None
        self.rows={}
        for i,unit in enumerate(q.START_ORDER):
            phase='SOURCE' if unit in q.ROLE_SELECTORS else 'STATIC'
            self.rows[unit]=q.Snapshot(unit,q.ROLE_HOST[unit],'active','running',100+i,0,1000+i,0,(100+i,),0,tuple(q.expected_code_pins(unit,phase).items()),None,False,send_sigkill='no',kill_signal='15',code_phase=phase)
        self.app='r16-app.service';self.native='r16-native.service';self.rows[self.app]=self.stopped(self.rows[self.app]);original=self.rows.copy()
        self.rows[self.native]=replace(self.stopped(self.rows[self.native]),fence_hash=q.sha(q.fence_bytes(self.h)),fence_effective=True)
        outer=self
        class Journal:
            def __init__(self):self.value={'phase':'QUIESCENT','cycle':0,'planHash':outer.h,'originalBaseline':original,'baseline':original,'events':[],'pending':None};self.saves=0
            def read(self):return self.value
            def save(self):self.saves+=1
            def permit(self,qmod,plan):return types.SimpleNamespace(state=self.value['phase'],expires_at=0)
        self.journal=Journal()
        class Backend:
            def _bind_admitted(self,permit):self.permit=permit
            def inspect(self,unit,h=''):
                outer.inspections.append(unit)
                if outer.inspect_failure and unit==outer.native and any(op=='unfence' for op,u in outer.effects):raise outer.inspect_failure
                queued=outer.queue.get(unit)
                if queued:
                    value=queued.pop(0) if len(queued)>1 else queued[0];outer.rows[unit]=value
                return outer.rows[unit]
            def unfence(self,unit,h):
                outer.assertEqual(h,outer.h);outer.effects.append(('unfence',unit));outer.rows[unit]=replace(outer.rows[unit],fence_hash=None,fence_effective=False)
                if outer.after_unfence:outer.after_unfence(unit)
            def start(self,unit,h):
                outer.assertEqual(h,outer.h);outer.effects.append(('start',unit));outer.journal.value['events'].append({'cycle':0,'unit':unit,'operation':'start','state':'INTENT'})
                if outer.start_failure:raise outer.start_failure
                outer.rows[unit]=outer.running(outer.rows[unit]);outer.queue.pop(unit,None)
        self.backend=Backend()
        self.ns=actual_functions({'time':self.clock,'now_ms':lambda:int(self.clock.at*1000),'snapshot':lambda qmod,row:row,'await_owner_publication':lambda plan:None})
    def stopped(self,row):return replace(row,active='inactive',sub='dead',main_pid=0,main_start=0,control_pid=0,control_start=0,members=())
    def running(self,row):return replace(row,active='active',sub='running',main_pid=900,main_start=9000,members=(900,),fence_hash=None,fence_effective=False,pending_job=False,daemon_reload_needed=False)
    def transient(self,**fields):return replace(self.stopped(self.rows[self.native]),**{'fence_hash':None,'fence_effective':False,**fields})
    def transition(self,*rows):self.after_unfence=lambda unit:self.queue.update({unit:list(rows)}) if unit==self.native else None
    def call(self):return self.ns['restore_roles'](q,self.backend,self.journal,self.plan,self.h)
    def activate(self):
        ns=self.ns;ns.update(root=lambda host:None,LOCAL=q.LOCAL,installed_context=lambda **kw:(None,self.plan,self.h),load_q=lambda:q,Journal=lambda path:self.journal,STATE=Path('/synthetic-state'),durable_backend=lambda qmod,journal:self.backend)
        return ns['os_action']('activate')
    def test_valid_pending_activating_and_reload_after_unfence_settle_running_without_start(self):
        self.transition(self.transient(pending_job=True),self.transient(active='activating',sub='start'),self.transient(daemon_reload_needed=True),self.running(self.rows[self.native]))
        result=self.call();self.assertEqual(result['status'],'OS_ACTIVE');self.assertEqual(result['failureCodes'],{});self.assertNotIn(('start',self.native),self.effects);self.assertEqual(self.effects,[('unfence',self.native)]);self.assertEqual(len(self.clock.waits),3)
    def test_permanent_pending_job_wait_is_bounded_to_15s_and_never_starts(self):
        self.transition(self.transient(pending_job=True));result=self.call()
        self.assertEqual(result['status'],'RESTORE_PARTIAL');self.assertEqual(result['failureCodes'][self.native],'RESTORE_READY_TIMEOUT');self.assertLessEqual(self.clock.at,15.000001);self.assertNotIn(('start',self.native),self.effects)
    def test_rollback_deadline_bounds_wait_and_remains_unchanged(self):
        self.plan['rollbackDeadline']=120;before=copy.deepcopy(self.plan);self.transition(self.transient(active='activating',sub='start',pending_job=True));result=self.call()
        self.assertEqual(result['status'],'RESTORE_PARTIAL');self.assertEqual(result['failureCodes'][self.native],'RECOVERY_WINDOW_EXPIRED');self.assertLessEqual(self.clock.at,.120001);self.assertEqual(before,self.plan);self.assertNotIn(('start',self.native),self.effects)
    def test_unsafe_foreign_fence_bad_code_or_identity_snapshot_refuse_without_wait(self):
        for drift,expected in [({'send_sigkill':'yes'},'UNSAFE_MANAGER_STOP_POLICY'),({'fence_hash':'f'*64},'RESTORE_FOREIGN_FENCE'),({'unit':self.app},'RESTORE_IDENTITY_DRIFT'),({'code_hashes':()},'RESTORE_CODE_DRIFT')]:
            with self.subTest(drift=drift):
                self.setUp();self.transition(self.transient(pending_job=True,**drift));result=self.call();self.assertEqual(result['failureCodes'][self.native],expected);self.assertEqual(self.clock.waits,[]);self.assertNotIn(('start',self.native),self.effects)
    def test_owned_fence_still_present_is_not_polled_or_removed_twice(self):
        row=self.rows[self.native];self.transition(row);result=self.call();self.assertEqual(result['failureCodes'][self.native],'RESTORE_FENCE_REMAINS');self.assertEqual(self.effects,[('unfence',self.native)]);self.assertEqual(self.clock.waits,[])
    def test_typed_inspection_identity_error_is_not_retried(self):
        self.inspect_failure=q.Refused('PID_REUSED_DURING_INSPECTION');result=self.call();self.assertEqual(result['failureCodes'][self.native],'PID_REUSED_DURING_INSPECTION');self.assertEqual(self.inspections.count(self.native),2);self.assertEqual(self.clock.waits,[]);self.assertNotIn(('start',self.native),self.effects)
    def test_prior_start_intent_with_stopped_row_never_replays_start(self):
        self.journal.value['events']=[{'cycle':0,'unit':self.native,'operation':'start','state':'INTENT'}];result=self.call();self.assertEqual(result['failureCodes'][self.native],'UNKNOWN_START_NOT_REPLAYED');self.assertNotIn(('start',self.native),self.effects)
    def test_prior_start_intent_activating_then_running_only_observes(self):
        self.journal.value['events']=[{'cycle':0,'unit':self.native,'operation':'start','state':'INTENT'}];self.transition(self.transient(active='activating',sub='start',pending_job=True),self.running(self.rows[self.native]));result=self.call();self.assertEqual(result['status'],'OS_ACTIVE');self.assertNotIn(('start',self.native),self.effects)
    def test_activate_continues_restore_partial_without_repeated_start(self):
        owner='r16-owner.service';self.rows[owner]=replace(self.stopped(self.rows[owner]),fence_hash=q.sha(q.fence_bytes(self.h)),fence_effective=True)
        self.transition(self.transient(pending_job=True));self.assertEqual(self.activate()['status'],'RESTORE_PARTIAL');self.assertEqual(self.effects.count(('start',owner)),1);before=list(self.effects)
        self.queue.clear();self.rows[self.native]=self.running(self.rows[self.native]);self.after_unfence=None
        self.assertEqual(self.activate()['status'],'OS_ACTIVE');self.assertEqual(self.effects,before);self.assertEqual(self.effects.count(('start',owner)),1);self.assertEqual(self.journal.value['failureCodes'],{})
    def test_activate_partial_does_not_bypass_unknown_start_intent(self):
        self.journal.value.update(phase='RESTORE_PARTIAL',events=[{'cycle':0,'unit':self.native,'operation':'start','state':'INTENT'}]);result=self.activate();self.assertEqual(result['status'],'RESTORE_PARTIAL');self.assertEqual(result['failureCodes'][self.native],'UNKNOWN_START_NOT_REPLAYED');self.assertNotIn(('start',self.native),self.effects)
    def test_start_readback_shares_readiness_budget_and_is_not_repeated(self):
        self.transition(self.transient(pending_job=True),self.transient());result=self.call();self.assertEqual(result['status'],'OS_ACTIVE');self.assertEqual(self.effects.count(('start',self.native)),1);self.assertEqual(len(self.clock.waits),1)
        self.assertEqual(self.call()['status'],'OS_ACTIVE');self.assertEqual(self.effects.count(('start',self.native)),1)
    def test_post_start_pending_readback_does_not_mint_second_15_second_budget(self):
        inspect=self.backend.inspect
        def evolving(unit,h=''):
            row=inspect(unit,h)
            if unit!=self.native or row.fence_hash:return row
            if ('start',unit) in self.effects:return replace(self.running(row),pending_job=True)
            return self.transient(pending_job=self.clock.at<14)
        self.backend.inspect=evolving;result=self.call();self.assertEqual(result['failureCodes'][self.native],'RESTORE_READY_TIMEOUT');self.assertEqual(self.effects.count(('start',self.native)),1);self.assertLessEqual(self.clock.at,15.000001)
    def test_partial_codes_are_fixed_bounded_and_not_raw_exception_text(self):
        self.inspect_failure=q.Refused('secret/path or raw provider response');result=self.call();self.assertEqual(result['failureCodes'][self.native],'RESTORE_BACKEND_REFUSED');self.assertEqual(result['failureCodes'][self.app],'RESTORE_PREDECESSOR_UNCONFIRMED');self.assertLessEqual(len(result['failureCodes']),4);self.assertNotIn('secret',str(result));self.assertEqual(self.journal.value['failureCodes'],result['failureCodes'])
    def test_generic_backend_failures_return_fixed_partial_without_retry_or_raw_text(self):
        for error in (OSError('private filesystem detail'),TimeoutError('private transport detail'),RuntimeError('private backend detail'),ValueError('private decode detail')):
            with self.subTest(error=type(error).__name__):
                self.setUp();self.inspect_failure=error;result=self.call();self.assertEqual(result['status'],'RESTORE_PARTIAL');self.assertEqual(result['failureCodes'][self.native],'RESTORE_BACKEND_REFUSED');self.assertEqual(self.journal.value['phase'],'RESTORE_PARTIAL');self.assertEqual(self.inspections.count(self.native),2);self.assertEqual(self.clock.waits,[]);self.assertNotIn('private',str(result));self.assertNotIn(('start',self.native),self.effects)
    def test_slow_valid_inspection_cannot_cross_deadline_then_start(self):
        self.plan['rollbackDeadline']=10;inspect=self.backend.inspect
        def slow(unit,h=''):
            row=inspect(unit,h)
            if unit==self.native and ('unfence',unit) in self.effects:self.clock.at=.020
            return row
        self.backend.inspect=slow;result=self.call();self.assertEqual(result['failureCodes'][self.native],'RECOVERY_WINDOW_EXPIRED');self.assertNotIn(('start',self.native),self.effects)
if __name__=='__main__':unittest.main()
