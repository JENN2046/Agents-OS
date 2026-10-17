"""Disposable real Store+SQLite files and explicit fixture-root/OS metadata seams.

No root, production paths, live DB connection, signal, SSH or service is used.
Production collector has no path/UID override; tests replace module constants and
map only requested fixed UID 0/1000 to the temporary fixture owner's real UID.
"""
import copy,hashlib,importlib.util,json,os,shutil,sqlite3,stat,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('native_checkpoint',HERE/'native_checkpoint.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
REAL_UID=os.geteuid();NODE=shutil.which('node')
def procrow(root,pid,ticks='123'):
 p=root/str(pid);p.mkdir(parents=True,exist_ok=True);(p/'stat').write_text(str(pid)+' (fixture) S '+'0 '*18+ticks);(p/'fd').mkdir(exist_ok=True);(p/'fdinfo').mkdir(exist_ok=True);(p/'maps').write_text('');return p
class Admission:
 def __init__(self):self.calls=[];self.refuse=False
 def require(self,h,op):
  n.need(not self.refuse,'TEST_ADMISSION_EXPIRED');self.calls.append((h,op))
class Backend:
 def __init__(self,fixture):self.f=fixture;self.calls=0;self.unsafe=False;self.boolean=False
 def assert_checkpoint_safe(self,h,target):
  self.calls+=1;n.need(not self.unsafe and h==self.f.data['planHash'] and target==self.f.target,'TEST_OS_BOUNDARY_REFUSED')
  return True if self.boolean else None
 def authenticated_app_history(self,h):n.need(h==self.f.data['planHash'],'TEST_PLAN_REFUSED');return copy.deepcopy(self.f.data['history'])
class Fixture:
 def __init__(self,case):
  self.tmp=tempfile.TemporaryDirectory(prefix='native-checkpoint-');case.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.root.chmod(0o700)
  n.need(NODE is not None,'NODE_REQUIRED')
  generated=subprocess.run([NODE,str(HERE/'test_checkpoint_public.mjs'),'--fixture',str(self.root)],capture_output=True,check=True);self.data=json.loads(generated.stdout)
  self.native=Path(self.data['native']);self.store=Path(self.data['dispatch']);self.dbdir=self.root/'db';self.dbdir.mkdir(mode=0o750);self.db=self.dbdir/'projectforge.db'
  # Real SQLite WAL/SHM content generated in a disposable fixture only. Capture
  # never invokes sqlite3, including when these pages are corrupt or opaque.
  conn=sqlite3.connect(self.db);conn.execute('pragma journal_mode=WAL');conn.execute('create table example(id integer primary key,value text)');conn.execute("insert into example(value) values('synthetic-private')");conn.commit()
  wal=Path(str(self.db)+'-wal').read_bytes();shm=Path(str(self.db)+'-shm').read_bytes();conn.close();Path(str(self.db)+'-wal').write_bytes(wal);Path(str(self.db)+'-shm').write_bytes(shm)
  for p in self.dbdir.iterdir():p.chmod(0o644)
  self.target={'pid':777,'startTicks':'123','bootId':'11111111-2222-4333-8444-555555555555'}
  (self.dbdir/(self.db.name+'.r16-writer.lock')).write_text(n.canonical({'schema':1,'pid':777,'start':'123','nonce':'11111111-2222-4333-8444-555555555555'}));(self.dbdir/(self.db.name+'.r16-writer.lock')).chmod(0o600)
  (self.native/'native-writer.lock').write_text(n.canonical({'pid':777,'start':'123','started_at':0}));(self.native/'native-writer.lock').chmod(0o600);(self.native/'.native-writer.guard').write_bytes(b'');(self.native/'.native-writer.guard').chmod(0o600)
  self.pubdir=self.root/'public';self.pubdir.mkdir(mode=0o755);self.public=self.pubdir/'public.json';self.config=self.pubdir/'native-host.json';self.registry=self.pubdir/'native-ledgers.json'
  st=self.store.stat();self.reg={'schema':'r16.native-ledgers.v1','grants':[{'directory':str(self.store),'dev':st.st_dev,'ino':st.st_ino,'grantId':'r16-projects-daily','grantHash':n.digest(self.data['pub']['grant']),'status':'READY'}]}
  self.public.write_text(n.canonical(self.data['pub']));self.config.write_text(n.canonical({'schema':'r16.native-host.v1','databasePath':str(self.db)}));self.registry.write_text(n.canonical(self.reg)+'\n')
  for p in self.pubdir.iterdir():p.chmod(0o644)
  self.checker=self.root/'public-checker.mjs';self.checker.write_text(self.data['fixtureCode']);self.proc=self.root/'proc';self.proc.mkdir(mode=0o700);procrow(self.proc,os.getpid())
  # Explicit fixture-root seam: all subdirectories below this temp root are
  # traversed with actual O_NOFOLLOW fds; /tmp's intentionally writable parent
  # is not represented as a production-approved ancestor.
  def local_open(path,*,uid=None,mode=None):
   path=Path(path);n.need(path.is_relative_to(self.root),'TEST_FIXED_ROOT');fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
   try:
    for part in path.relative_to(self.root).parts:
     child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=child;s=os.fstat(fd);n.need(s.st_uid==REAL_UID and not s.st_mode&0o7022,'DIRECTORY_METADATA_REFUSED')
    s=os.fstat(fd)
    if uid is not None:n.need(s.st_uid==REAL_UID and (mode is None or stat.S_IMODE(s.st_mode)==mode),'STORE_DIRECTORY_REFUSED')
    return fd
   except BaseException:os.close(fd);raise
  original_read=n.read_at
  def local_read(fd,name,*,uid,**kw):return original_read(fd,name,uid=1000,**kw)
  real_fstat=os.fstat;real_stat=os.stat
  # read_native_tree validates logical service UID. This wrapper preserves all
  # other stat fields (including ns) and only maps fixture owner to fixed1000.
  class StatView:
   def __init__(self,s):self.s=s
   def __getattr__(self,k):return 1000 if k=='st_uid' and self.s.st_uid==REAL_UID else getattr(self.s,k)
  for name,value in {'NATIVE_ROOT':self.native,'STORE':self.store,'DATABASE':self.db,'PUBLIC':self.public,'CONFIG':self.config,'REGISTRY':self.registry,'PUBLIC_CHECKER':self.checker,'NODE_BINARIES':{n.HOST:NODE,'VM-0-12-ubuntu':NODE},'PUBLIC_HASH':n.digest(self.data['pub']),'GRANT_HASH':n.digest(self.data['pub']['grant'])}.items():case.enterContext(patch.object(n,name,value))
  case.enterContext(patch.object(n,'open_directory',local_open));case.enterContext(patch.object(n,'read_at',local_read))
  # UID mapping only needed if CI uid !=1000. _read_at sees real uid and does
  # not rely on mapped inode/mode/size. Metadata-negative tests remain actual.
  if REAL_UID!=1000:
   def mapped_fstat(fd):return StatView(real_fstat(fd))
   def mapped_stat(*a,**kw):return StatView(real_stat(*a,**kw))
   # Rather than globally alter os (and subprocess), read tree functions get a
   # private facade; fixture read_at still uses original actual os APIs.
   class OSFacade:
    def __getattr__(self,k):return {'fstat':mapped_fstat,'stat':mapped_stat,'geteuid':lambda:0}.get(k,getattr(os,k))
   case.enterContext(patch.object(n,'os',OSFacade()))
  else:
   class OSFacade:
    def __getattr__(self,k):return (lambda:0) if k=='geteuid' else getattr(os,k)
   case.enterContext(patch.object(n,'os',OSFacade()))
  real_path=Path
  case.enterContext(patch.object(n,'Path',lambda v: self.proc if str(v)=='/proc' else real_path(v)))
  case.enterContext(patch.object(n.platform,'node',lambda:n.HOST))
  self.admission=Admission();self.backend=Backend(self);self.collector=n.NativeCheckpoint(self.admission,self.backend)
 def capture(self):return self.collector.capture(self.data['planHash'],self.target)
class CheckpointTests(unittest.TestCase):
 def fixture(self):return Fixture(self)
 def test_actual_store_sqlite_wal_shm_complete_byte_inventory_without_db_connection(self):
  f=self.fixture();before={p:p.read_bytes() for p in f.native.rglob('*') if p.is_file()};before.update({p:p.read_bytes() for p in f.dbdir.iterdir()});c=f.capture()
  self.assertEqual(c['schema'],'r16.source19-native-checkpoint.v1');self.assertFalse(c['liveDatabaseOpened']);self.assertTrue(c['sqliteFilesEnumerated']);self.assertEqual(c['controlUnknownCount'],1);self.assertEqual(len(c['historicalOperations']),2)
  for p,b in before.items():self.assertEqual(p.read_bytes(),b)
  self.assertEqual(c['files']['database/projectforge.db-wal']['sha256'],hashlib.sha256(Path(str(f.db)+'-wal').read_bytes()).hexdigest());self.assertGreaterEqual(f.backend.calls,3);self.assertNotEqual(c['nativeLedgerRegistration']['registryHash'],n.digest(f.reg));self.assertNotIn('bytes',c['historicalOperations'][0])
 def test_wal_shm_absence_is_explicit_file_set_not_fabricated_empty(self):
  f=self.fixture();Path(str(f.db)+'-wal').unlink();Path(str(f.db)+'-shm').unlink();c=f.capture();self.assertNotIn('database/projectforge.db-wal',c['files']);self.assertNotIn('database/projectforge.db-shm',c['files'])
 def test_unknown_database_file_or_reclaim_refuses(self):
  for name in ['foreign.db','projectforge.db.r16-writer.lock.reclaim']:
   with self.subTest(name=name):
    f=self.fixture();(f.dbdir/name).write_bytes(b'');self.assertRaisesRegex(n.Refused,'DATABASE_FILESET_REFUSED',f.capture)
 def test_symlink_hardlink_and_unsafe_filemode_refuse(self):
  for kind in ['symlink','hardlink','mode']:
   with self.subTest(kind=kind):
    f=self.fixture();p=Path(str(f.db)+'-wal')
    if kind=='symlink':p.unlink();p.symlink_to(f.db)
    elif kind=='hardlink':p.unlink();os.link(f.db,p)
    else:p.chmod(0o666)
    with self.assertRaises((n.Refused,OSError)):f.capture()
 def test_temporary_native_next_reclaim_refuse(self):
  for name in ['.next-uncommitted','.reclaim-old']:
   f=self.fixture();p=f.store/name;p.write_bytes(b'');p.chmod(0o600);self.assertRaisesRegex(n.Refused,'TEMPORARY_STORE_FILE_PRESENT',f.capture)
 def test_registry_devino_missing_or_extra_grant_refuse(self):
  for mutate in [lambda r:r['grants'][0].update(ino=1),lambda r:r.update(grants=[]),lambda r:r['grants'].append(r['grants'][0])]:
   f=self.fixture();r=copy.deepcopy(f.reg);mutate(r);f.registry.write_text(n.canonical(r));self.assertRaises(n.Refused,f.capture)
 def test_unregistered_or_missing_project_directory_refuses(self):
  f=self.fixture();(f.store/'project-foreign').mkdir(mode=0o700);self.assertRaisesRegex(n.Refused,'UNREGISTERED_STORE_DIRECTORY',f.capture)
 def test_current_unknown_or_inflight_drift_refuses_actual_crypto_pipeline(self):
  for status in ['INFLIGHT','CREATED']:
   f=self.fixture();p=f.store/'state.json';s=json.loads(p.read_bytes());s['data']['controls'][0]['status']=status;p.write_text(n.canonical(s));self.assertRaisesRegex(n.Refused,'CURRENT_WORK_UNRESOLVED',f.capture)
 def test_missing_or_wrong_public_signed_app_history_is_not_boolean_evidence(self):
  f=self.fixture();f.backend.authenticated_app_history=lambda h:{'schema':'wrong','verified':True};self.assertRaisesRegex(n.Refused,'AUTHENTICATED_HISTORY_SCOPE',f.capture)
 def test_current_native_issuer_lease_tamper_refuses(self):
  f=self.fixture();p=f.store/'project-p2vox/state.json';s=json.loads(p.read_bytes());s['data']['active']['lease']['signature']='invalid';p.write_text(n.canonical(s));self.assertRaises(n.Refused,f.capture)
 def test_no_root_host_admission_or_actual_os_boundary_never_captures(self):
  f=self.fixture();f.backend.boolean=True;self.assertRaisesRegex(n.Refused,'OS_CHECKPOINT_BOOLEAN_NOT_EVIDENCE',f.capture);f.backend.boolean=False;f.backend.unsafe=True;self.assertRaisesRegex(n.Refused,'TEST_OS_BOUNDARY_REFUSED',f.capture)
 def test_expiry_or_os_change_midscan_refuses_no_result(self):
  f=self.fixture();original=f.backend.assert_checkpoint_safe
  def boundary(h,t):
   if f.backend.calls:f.admission.refuse=True
   return original(h,t)
  f.backend.assert_checkpoint_safe=boundary;self.assertRaisesRegex(n.Refused,'TEST_ADMISSION_EXPIRED',f.capture)
 def test_checkpoint_files_drift_on_second_full_scan_refuses(self):
  f=self.fixture();original=n.read_native_tree;calls=0
  def read(*args,**kwargs):
   nonlocal calls
   calls+=1
   if calls==2:(f.native/'.native-writer.guard').write_bytes(b'changed')
   return original(*args,**kwargs)
  with patch.object(n,'read_native_tree',read):self.assertRaisesRegex(n.Refused,'CHECKPOINT_CHANGED_DURING_CAPTURE',f.capture)
 def test_public_registry_or_config_drift_before_final_read_refuses(self):
  f=self.fixture();original=f.backend.assert_checkpoint_safe
  def boundary(h,t):
   result=original(h,t)
   if f.backend.calls==3:f.registry.write_text(n.canonical(f.reg))
   return result
  f.backend.assert_checkpoint_safe=boundary;self.assertRaisesRegex(n.Refused,'PUBLIC_BINDING_CHANGED_DURING_CAPTURE',f.capture)
 def foreign(self,f,flags='0100002',mapping=False,directory=False):
  p=procrow(f.proc,888)
  if mapping:
   st=f.db.stat();dev=f'{os.major(st.st_dev):02x}:{os.minor(st.st_dev):02x}';(p/'maps').write_text(f'1000-2000 rw-s 00000000 {dev} {st.st_ino} {f.db}\n')
  else:(p/'fd/3').symlink_to(f.dbdir if directory else f.db);(p/'fdinfo/3').write_text('flags:\t'+flags+'\n')
 def test_foreign_actual_file_writable_fd_refuses(self):
  f=self.fixture();self.foreign(f);self.assertRaisesRegex(n.Refused,'FOREIGN_WRITABLE_FD',f.capture)
 def test_reused_target_pid_is_scanned_as_foreign_not_exempt(self):
  f=self.fixture();p=procrow(f.proc,f.target['pid'],ticks='999');(p/'fd/3').symlink_to(f.db);(p/'fdinfo/3').write_text('flags: 0100002\n');self.assertRaisesRegex(n.Refused,'FOREIGN_WRITABLE_FD',f.capture)
 def test_foreign_actual_shared_writable_map_refuses(self):
  f=self.fixture();self.foreign(f,mapping=True);self.assertRaisesRegex(n.Refused,'FOREIGN_WRITABLE_SHARED_MAPPING',f.capture)
 def test_foreign_directory_capability_refuses_even_without_open_database(self):
  f=self.fixture();self.foreign(f,directory=True);self.assertRaisesRegex(n.Refused,'FOREIGN_STORE_DIRECTORY_FD',f.capture)
 def test_foreign_readonly_fd_is_not_misrepresented_as_writer(self):
  f=self.fixture();self.foreign(f,flags='0100000');self.assertTrue(f.capture()['noForeignWriters'])
 def test_foreign_live_lock_even_no_fd_refuses(self):
  f=self.fixture();procrow(f.proc,888,ticks='456');p=f.native/'native-writer.lock';p.write_text(n.canonical({'pid':888,'start':'456','started_at':0}));self.assertRaisesRegex(n.Refused,'FOREIGN_STORE_WRITER',f.capture)
 def test_duplicate_json_keys_and_float_are_not_accepted_as_stable_store(self):
  for raw in [b'{"schema":1,"schema":1}',b'{"value":1.1}']:
   f=self.fixture();(f.store/'state.json').write_bytes(raw);self.assertRaises(n.Refused,f.capture)
class NativePreflightTests(unittest.TestCase):
 def fixture(self):
  f=Fixture(self)
  class Live:
   def __init__(self):self.calls=0;self.bad=False;self.boolean=False
   def assert_native_preflight_safe(self):self.calls+=1;n.need(not self.bad,'LIVE_SOURCE_IDENTITY_REFUSED');return True if self.boolean else None
   def authenticated_app_history(self,h):
    n.need(h is None,'PREFLIGHT_NOT_PLAN_AUTHORITY');return {'schema':'r16.source19-native-transition.public-history-preflight.v1','sourcePublicConfigHash':n.PUBLIC_HASH,'historicalOperations':f.data['history']['historicalOperations'],'atomicStoppedCheckpoint':False,'globalExecution':'UNPROVEN','authority':False}
  f.live=Live();return f
 def test_live_sample_material_not_atomic_b_no_database_or_writer_closure_claim(self):
  f=self.fixture()
  with patch.object(n,'read_database',side_effect=AssertionError('NO_PREFLIGHT_DB_IO')),patch.object(n,'scan_writers',side_effect=AssertionError('NO_FALSE_WRITER_PROOF')):out=n.read_native_preflight(f.admission,f.live)
  self.assertFalse(out['atomicStoppedCheckpoint']);self.assertFalse(out['sqliteFilesEnumerated']);self.assertFalse(out['authority']);self.assertEqual(out['foreignWriterClosure'],'NOT_PROVEN_LIVE_PREFLIGHT');self.assertNotIn('completeRegisteredFileSet',out);self.assertEqual(out['controlUnknownCount'],1);self.assertEqual(f.live.calls,3)
 def test_live_source_actual_identity_or_boolean_refusal_is_not_caught_or_retried(self):
  f=self.fixture();f.live.bad=True;self.assertRaisesRegex(n.Refused,'LIVE_SOURCE_IDENTITY_REFUSED',n.read_native_preflight,f.admission,f.live);self.assertEqual(f.live.calls,1);f.live.bad=False;f.live.boolean=True;self.assertRaisesRegex(n.Refused,'OS_CHECKPOINT_BOOLEAN_NOT_EVIDENCE',n.read_native_preflight,f.admission,f.live)
 def test_new_unknown_and_current_inflight_refuse_live_sample(self):
  for change in [lambda s:s['controls'][0].update(status='INFLIGHT'),lambda s:s['operations'].append({'id':'new','status':'UNKNOWN'})]:
   f=self.fixture();p=f.store/('state.json' if 'controls' in change.__code__.co_consts else 'project-p2vox/state.json');value=json.loads(p.read_bytes());change(value['data']);p.write_text(n.canonical(value));self.assertRaises(n.Refused,n.read_native_preflight,f.admission,f.live)
 def test_live_second_tree_drift_preserves_failure_not_b(self):
  f=self.fixture();original=f.live.assert_native_preflight_safe
  def boundary():
   out=original()
   if f.live.calls==2:(f.native/'.native-writer.guard').write_bytes(b'changed')
   return out
  f.live.assert_native_preflight_safe=boundary;self.assertRaisesRegex(n.Refused,'CHECKPOINT_CHANGED_DURING_CAPTURE',n.read_native_preflight,f.admission,f.live)

class AppPublicTests(unittest.TestCase):
 def test_production_node_binary_map_is_fixed_for_both_verified_hosts(self):
  self.assertEqual(n.NODE_BINARIES,{n.HOST:'/usr/bin/node',n.CLOUD:'/opt/r16/runtime/node-v24.15.0/bin/node'})
 def fixture(self):
  f=Fixture(self);app=f.root/'app/host';regdir=f.root/'app-registry';regdir.mkdir(mode=0o700);regfile=regdir/'sealed.json';st=app.stat()
  specs=[{'role':'app','path':str(app)},{'role':'bridge','path':'/var/lib/r16-bridge/grants/r16-projects-daily/bridge'},{'role':'gateway','path':'/var/lib/r16-bridge/grants/r16-projects-daily/gateway'}]
  reg={'schema':'r16.cloud-ledger-registration.v1','grantId':'r16-projects-daily','phase':'SEALED','specs':specs,'identities':[{'role':'app','dev':st.st_dev,'ino':st.st_ino},{'role':'bridge','dev':st.st_dev,'ino':st.st_ino+1},{'role':'gateway','dev':st.st_dev,'ino':st.st_ino+2}]};regfile.write_text(n.canonical(reg));regfile.chmod(0o600)
  for name,value in {'APP_STORE':app,'CLOUD_PUBLIC':f.public,'APP_REGISTRY_DIRECTORY':regdir,'APP_REGISTRY':regfile,'APP_REGISTRY_SPECS':specs}.items():self.enterContext(patch.object(n,name,value))
  self.enterContext(patch.object(n.platform,'node',lambda:n.CLOUD));f.app=app;f.appreg=regfile;f.appregvalue=reg
  class CloudOS:
   def __init__(self):self.calls=[];self.bad=False;self.boolean=False
   def assert_app_history_safe(self,h):
    self.calls.append(h);n.need(not self.bad,'CLOUD_SOURCE_IDENTITY_DRIFT');return True if self.boolean else None
  f.cloud=CloudOS();return f
 def test_active_preflight_proves_material_but_never_claims_atomic_stopped_authority(self):
  f=self.fixture();before=(f.app/'state.json').read_bytes();out=n.read_app_history_preflight(f.admission,f.cloud);self.assertFalse(out['authority']);self.assertFalse(out['atomicStoppedCheckpoint']);self.assertEqual(len(out['historicalOperations']),2);self.assertNotIn('planHash',out);self.assertEqual((f.app/'state.json').read_bytes(),before);self.assertEqual(f.cloud.calls,[None,None,None])
 def test_stopped_sameplan_reader_returns_only_public_signed_material(self):
  f=self.fixture();out=n.collect_app_history(f.data['planHash'],f.admission,f.cloud);self.assertEqual(out,f.data['history']);self.assertEqual(set(out),{'schema','planHash','sourcePublicConfigHash','historicalOperations'});self.assertTrue(all(h==f.data['planHash'] for h in f.cloud.calls))
 def test_missing_or_invalid_original_app_operation_blocks_before_stopping(self):
  for mutate in [lambda s:s.update(operations=[]),lambda s:s['operations'][0].update(status='KNOWN'),lambda s:s['operations'][0]['operation'].update(signature='invalid')]:
   f=self.fixture();p=f.app/'state.json';value=json.loads(p.read_bytes());mutate(value['data']);p.write_text(n.canonical(value));self.assertRaises(n.Refused,n.read_app_history_preflight,f.admission,f.cloud)
 def test_unsealed_or_wrong_registered_app_root_refuses_before_app_bytes(self):
  f=self.fixture();f.appregvalue['identities'][0]['ino']+=100;f.appreg.write_text(n.canonical(f.appregvalue));original=n.read_at;seen=[]
  def read(fd,name,**kw):seen.append(name);return original(fd,name,**kw)
  with patch.object(n,'read_at',read):self.assertRaisesRegex(n.Refused,'SEALED_APP_DIRECTORY_IDENTITY_DRIFT',n.read_app_history_preflight,f.admission,f.cloud)
  self.assertNotIn('state.json',seen)
 def test_app_bytes_changed_during_public_crypto_refuse(self):
  f=self.fixture();original=f.cloud.assert_app_history_safe
  def boundary(h):
   result=original(h)
   if len(f.cloud.calls)==2:
    p=f.app/'state.json';value=json.loads(p.read_bytes());value['revision']+=1;p.write_text(n.canonical(value))
   return result
  f.cloud.assert_app_history_safe=boundary;self.assertRaisesRegex(n.Refused,'APP_HISTORY_CHANGED_DURING_CAPTURE',n.read_app_history_preflight,f.admission,f.cloud)
 def test_cloud_role_kernel_refusal_or_boolean_never_becomes_evidence(self):
  f=self.fixture();f.cloud.boolean=True;self.assertRaisesRegex(n.Refused,'OS_CHECKPOINT_BOOLEAN_NOT_EVIDENCE',n.read_app_history_preflight,f.admission,f.cloud);f.cloud.boolean=False;f.cloud.bad=True;self.assertRaisesRegex(n.Refused,'CLOUD_SOURCE_IDENTITY_DRIFT',n.collect_app_history,f.data['planHash'],f.admission,f.cloud)
 def test_preflight_admission_expiry_midread_and_root_identity_refuse(self):
  f=self.fixture();f.admission.refuse=True;self.assertRaisesRegex(n.Refused,'TEST_ADMISSION_EXPIRED',n.read_app_history_preflight,f.admission,f.cloud)
  f.admission.refuse=False
  with patch.object(n.os,'geteuid',lambda:1000):self.assertRaisesRegex(n.Refused,'FIXED_ROOT_CLOUD_REQUIRED',n.read_app_history_preflight,f.admission,f.cloud)
if __name__=='__main__':unittest.main()
