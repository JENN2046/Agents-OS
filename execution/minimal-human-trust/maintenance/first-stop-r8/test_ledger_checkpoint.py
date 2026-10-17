"""Offline synthetic signatures/files only. Never production root/state/SSH."""
import base64
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from contextlib import ExitStack,contextmanager
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

spec=importlib.util.spec_from_file_location('ledger_checkpoint_tested',Path(__file__).with_name('ledger_checkpoint.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def b64(raw): return base64.urlsafe_b64encode(raw).decode().rstrip('=')
def key(k): return b64(k.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo))
def sign(body,k): return {'body':copy.deepcopy(body),'signature':b64(k.sign(b'R16-SIGNED\0'+m.canonical(body).encode()))}
def raw(value): return m.canonical(value).encode()
@contextmanager
def fixture_metadata_uid(uid=1000):
    """Only private temporary-tree calls enter this adapter, never production.

    GitHub's runner UID differs from the fixed service UID. Keep every real
    inode/mode/time field; translate UID only in this fixture's OS test seam.
    Runtime reader and its UID-1000 guard are unchanged.
    """
    real_fstat=os.fstat;real_stat=os.stat
    class Metadata:
        def __init__(self,actual):self.actual=actual;self.st_uid=uid
        def __getattr__(self,name):return getattr(self.actual,name)
    with patch.object(m.os,'fstat',side_effect=lambda fd:Metadata(real_fstat(fd))),patch.object(m.os,'stat',side_effect=lambda *args,**kwargs:Metadata(real_stat(*args,**kwargs))):
        yield
def registered(app_identity=(1,2)):
    value={'schema':'r16.cloud-ledger-registration.v1','grantId':'r16-projects-daily','phase':'SEALED','specs':copy.deepcopy(m.REGISTRY_SPECS),'identities':[{'role':'app','dev':app_identity[0],'ino':app_identity[1]},{'role':'bridge','dev':9,'ino':8},{'role':'gateway','dev':9,'ino':9}]}
    return value,m.bytehash(raw(value))
def fixture():
    issuer=Ed25519PrivateKey.generate();release=Ed25519PrivateKey.generate()
    peers={r:Ed25519PrivateKey.generate() for r in ('app','bridge','native')}
    workspace={'id':'synthetic-ws','root':'/synthetic/workspace','dev':1,'ino':2}
    g=sign({'schema':'r16.workspace.v1','id':'r16-projects-daily','version':1,'createdAt':1,'workspace':workspace,'actions':['list_workspaces'],'channel':'main','peers':{r:{'id':r+'-synthetic','publicKey':key(k)} for r,k in peers.items()}},issuer)
    versions={r:'1'*64 for r in peers};versions['app']=m.digest({'role':'app','files':{}})
    r=sign({'schema':'r16.release.v1','id':'r16-daily-20261012-r15','issuedAt':1,'notAfter':99999999,'versions':versions,'actions':['list_workspaces'],'formats':['r16.workspace.v1'],'permissionVersion':1},release)
    pub={'grant':g,'release':r,'issuerPublicKey':key(issuer),'releasePublicKey':key(release),'peers':g['body']['peers'],'versions':versions,'channel':'main'}
    target={'unit':m.UNIT,'host':m.HOST,'pid':4343,'startTicks':'123456','bootId':'00000000-1111-2222-3333-444444444444','cgroup':m.CGROUP,'invocationId':'a'*32,'nRestarts':0}
    files={};pins=copy.deepcopy(m.PINS)
    def put(name,data): files[name]={'bytes':raw(data),'regular':True,'symlink':False,'uid':1000,'nlink':1,'mode':0o600}
    def state(data): return {'schema':1,'revision':1,'maxNow':20,'data':data}
    host={'kind':'r16.app-workspace.v1','projects':[],'operations':[],'allocations':[],'status':'recovery_pending'}
    for project,pin in pins.items():
        p={'id':project,'workspaceId':workspace['id'],'root':workspace['root']+'/'+project}
        lease=sign({'schema':'r16.lease.v1','phase':'PREPARED','grantId':g['body']['id'],'grantVersion':1,'grantHash':m.digest(g),'project':p,'channel':'main','versions':versions,'actions':['list_workspaces'],'generation':pin['generation'],'previousGeneration':pin['generation']-1,'issuedAt':10,'expiresAt':3600010,'renewAt':2700010,'requestId':'synthetic-'+project,'releaseHash':m.digest(r)},issuer)
        activation=sign({'schema':'r16.activation.v1','grantId':g['body']['id'],'grantVersion':1,'projectId':project,'generation':pin['generation'],'leaseHash':m.digest(lease),'evidenceHash':'2'*64,'activatedAt':11},issuer)
        op=sign({'schema':'r16.operation.v1','id':pin['operationId'],'grantId':g['body']['id'],'projectId':project,'generation':pin['generation'],'leaseHash':m.digest(lease),'channel':'main','action':'list_workspaces','payloadHash':'3'*64},peers['app'])
        pin['operationHash']=m.digest(op)
        host['projects'].append({'project':p,'initialized':True,'transition':None,'retirement':{'lease':lease}})
        host['operations'].append({'id':pin['operationId'],'projectId':project,'status':'UNKNOWN','resultHash':None,'operation':op})
        participant={'kind':'r16.participant.v1','role':'app','grant':g,'version':1,'lastGeneration':pin['generation'],'active':{'lease':lease,'activation':activation},'closing':lease,'pending':None,'fresh':None,'operations':[{'id':pin['operationId'],'projectId':project,'generation':pin['generation'],'hash':pin['operationHash'],'status':'UNKNOWN','resultHash':None}],'closed':[],'stopped':[]}
        put('host/project-'+project+'/state.json',state(participant))
    put('host/state.json',state(host))
    for parent in ['host','host/project-p2vox','host/project-pmog2']:
        put(parent+'/.lock',{'schema':1,'pid':target['pid'],'start':target['startTicks'],'nonce':'synthetic-offline-lock'})
        put(parent+'/archive-offline.json',{'id':'historical','status':'KNOWN','hash':'4'*64})
    return {'schema':'r16.source-app-durable-checkpoint.v1','completeRegisteredFileSet':True,'otherWriterPids':[],'files':files},target,pub,pins,issuer,peers

def add_history(c,target,pub,issuer,peers):
    """Nine registered stores matching old-core reachable phase shapes.

    Synthetic IDs/keys/operation data only. No live state is imported here.
    """
    host=m.parse(c['files']['host/state.json']['bytes']);g=pub['grant']['body']
    def put(name,value):c['files'][name]={'bytes':raw(value),'regular':True,'symlink':False,'uid':1000,'nlink':1,'mode':0o600}
    ids=[]
    for index,(gen,count) in enumerate([(83,0),(6,12),(4,12),(7,18),(2,0),(1,0),(1,0)]):
        pid=('pending-history-' if index>=5 else 'history-')+str(index);ids.append(pid)
        p={'id':pid,'workspaceId':g['workspace']['id'],'root':g['workspace']['root']+'/'+pid}
        l=sign({'schema':'r16.lease.v1','phase':'PREPARED','grantId':g['id'],'grantVersion':1,'grantHash':m.digest(pub['grant']),'project':p,'channel':'main','versions':pub['versions'],'actions':g['actions'],'generation':gen,'previousGeneration':gen-1,'issuedAt':10,'expiresAt':3600010,'renewAt':2700010,'requestId':'request-'+pid,'releaseHash':m.digest(pub['release'])},issuer)
        a=sign({'schema':'r16.activation.v1','grantId':g['id'],'grantVersion':1,'projectId':pid,'generation':gen,'leaseHash':m.digest(l),'evidenceHash':'2'*64,'activatedAt':11},issuer)
        state={'kind':'r16.participant.v1','role':'app','grant':pub['grant'],'version':1,'lastGeneration':gen,'active':{'lease':l,'activation':a} if index<4 else None,'pending':None,'closing':l if index==0 else None,'operations':[],'closed':[],'stopped':[],'archiveHead':None,'fresh':None,'challenge':None}
        reg={'project':p,'initialized':True,'transition':None,'retirement':{'lease':l} if index==0 else None}
        if index>=4:
            stopped=sign({'schema':'r16.stopped.v1','role':'app','peerId':g['peers']['app']['id'],'grantId':g['id'],'grantVersion':1,'projectId':pid,'generation':gen,'leaseHash':m.digest(l),'requestId':l['body']['requestId'],'durableClosed':True,'pending':0,'resultsHash':m.digest([])},peers['app'])
            state['stopped']=[stopped];put('host/project-'+pid+'/archive-stop-'+m.digest(l)+'.json',stopped)
            closed=sign({'schema':'r16.closed.v1','grantId':g['id'],'projectId':pid,'generation':gen,'leaseHash':m.digest(l),'evidenceHash':'2'*64,'closedAt':12},issuer)
            reg['closedGeneration']=gen;put('host/archive-app-close-'+pid+'-'+str(gen)+'.json',closed)
        if index==6:
            reg['transition']={'request':{'schema':'r16.prepare.v1','requestId':'next-'+pid,'grantId':g['id'],'grantVersion':1,'project':p,'channel':'main','versions':pub['versions'],'actions':g['actions'],'issuedAt':20},'proofs':None,'submitted':False,'lease':None,'activation':None}
        for i in range(count):
            oid=pid+'-operation-'+str(i)
            op=sign({'schema':'r16.operation.v1','id':oid,'grantId':g['id'],'projectId':pid,'generation':gen,'leaseHash':m.digest(l),'channel':'main','action':g['actions'][0],'payloadHash':'3'*64},peers['app'])
            host['data']['operations'].append({'id':oid,'projectId':pid,'operation':op,'status':'KNOWN','resultHash':'4'*64})
            state['operations'].append({'id':oid,'projectId':pid,'generation':gen,'hash':m.digest(op),'status':'KNOWN','outcome':'COMPLETED','resultHash':'4'*64})
        host['data']['projects'].append(reg)
        put('host/project-'+pid+'/state.json',{'schema':1,'revision':1,'maxNow':20,'data':state})
        put('host/project-'+pid+'/.lock',{'schema':1,'pid':target['pid'],'start':target['startTicks'],'nonce':'synthetic-offline-lock'})
    put('host/state.json',host)
    return ids

class SemanticTests(unittest.TestCase):
    def setUp(self): self.c,self.t,self.p,self.pins,self.issuer,self.peers=fixture()
    def validate(self): return m._validate(self.c,self.t,self.p,100,m.digest(self.p),m.digest(self.p['grant']),self.pins)
    def edit(self,name,fn):
        value=json.loads(self.c['files'][name]['bytes']);fn(value);self.c['files'][name]['bytes']=raw(value)
    def test_valid_signed_originals_returns_only_hashes_counts_and_bindings(self):
        result=self.validate();self.assertEqual(result['attestation']['originalUnknownCount'],2)
        self.assertEqual(result['attestation']['drainStatus'],'UNPROVEN');self.assertNotIn('files',result)
        self.assertNotIn('"signature":',json.dumps(result));self.assertNotIn('"bytes":',json.dumps(result))
    def test_fixed_production_anchor_rejects_even_valid_synthetic_signatures(self):
        with self.assertRaisesRegex(m.Refused,'PUBLIC_TRUST_ROOT_DRIFT'): m.validate_checkpoint(self.c,self.t,self.p,100)
    def test_bad_original_signature(self):
        self.edit('host/state.json',lambda v:v['data']['operations'][0]['operation'].update(signature='A'*86))
        with self.assertRaisesRegex(m.Refused,'BAD_SIGNATURE'): self.validate()
    def test_wrong_issuer_cannot_sign_lease(self):
        evil=Ed25519PrivateKey.generate()
        self.edit('host/project-p2vox/state.json',lambda v:v['data']['active'].update(lease=sign(v['data']['active']['lease']['body'],evil)))
        with self.assertRaises(m.Refused): self.validate()
    def test_activation_wrong_generation(self):
        def mutate(v):
            a=v['data']['active']['activation']['body'];a['generation']+=1;v['data']['active']['activation']=sign(a,self.issuer)
        self.edit('host/project-p2vox/state.json',mutate)
        with self.assertRaisesRegex(m.Refused,'ORIGINAL_ACTIVATION_DRIFT'): self.validate()
    def test_signed_lease_wrong_release(self):
        def mutate(v):
            b=v['data']['active']['lease']['body'];b['releaseHash']='0'*64
            new=sign(b,self.issuer);v['data']['active']['lease']=new;v['data']['closing']=new
        self.edit('host/project-p2vox/state.json',mutate)
        with self.assertRaisesRegex(m.Refused,'ORIGINAL_LEASE_BINDING_DRIFT'): self.validate()
    def test_pending_or_changed_closing_refused(self):
        for field,value in [('pending',{}),('closing',{})]:
            with self.subTest(field=field):
                self.setUp();self.edit('host/project-p2vox/state.json',lambda v:v['data'].update({field:value}))
                with self.assertRaises(m.Refused):self.validate()
    def test_legitimate_not_yet_drained_original_lease_has_no_closing(self):
        self.edit('host/project-pmog2/state.json',lambda v:v['data'].update(closing=None))
        result=self.validate();self.assertIsNone(result['expectedLeaseBindings']['pmog2']['closingLeaseHash'])
    def test_dead_or_reused_old_writer_lock_uses_derived_proof_without_changing_bytes(self):
        self.edit('host/project-pmog2/.lock',lambda v:v.update(pid=777,start='888'))
        original=self.c['files']['host/project-pmog2/.lock']['bytes']
        for observed in (None,'999'):
            with patch.object(m,'_start',side_effect=FileNotFoundError if observed is None else lambda pid:observed):
                self.c['staleLockProofs']=m._stale_lock_proofs(self.c['files'],self.t)
            self.validate();self.assertEqual(self.c['files']['host/project-pmog2/.lock']['bytes'],original)
        with patch.object(m,'_start',return_value='888'):
            with self.assertRaisesRegex(m.Refused,'FOREIGN_STORE_WRITER'):m._stale_lock_proofs(self.c['files'],self.t)
    def test_stale_lock_proof_cannot_bind_wronghash_boot_pid_or_live_start(self):
        self.edit('host/project-pmog2/.lock',lambda v:v.update(pid=777,start='888'))
        row=self.c['files']['host/project-pmog2/.lock']
        proof={'lockSha256':m.bytehash(row['bytes']),'pid':777,'startTicks':'888','observedStartTicks':None,'bootId':self.t['bootId']}
        for field,value in [('lockSha256','0'*64),('pid',666),('bootId','other'),('observedStartTicks','888')]:
            self.c['staleLockProofs']={'host/project-pmog2/.lock':{**proof,field:value}}
            with self.assertRaisesRegex(m.Refused,'FOREIGN_STORE_WRITER'):self.validate()
    def test_legitimate_missing_lock_derived_proof_preserves_missing_file(self):
        del self.c['files']['host/project-pmog2/.lock']
        dirs={'host':(1,2),'host/project-p2vox':(1,3),'host/project-pmog2':(1,4)}
        for phase in ('BASELINE_NOT_DRAIN_PROOF','FROZEN','EXITED'):
            self.c['missingLockProofs']=m._missing_lock_proofs(self.c['files'],dirs,self.t,phase)
            result=self.validate();self.assertEqual(result['attestation']['missingLockProofs']['host/project-pmog2/.lock']['capturePhase'],phase)
            self.assertNotIn('host/project-pmog2/.lock',self.c['files'])
    def test_missing_lock_proof_wrong_state_boot_directory_or_phase_refused(self):
        del self.c['files']['host/project-pmog2/.lock'];proof=m._missing_lock_proofs(self.c['files'],{'host/project-pmog2':(1,4)},self.t,'FROZEN')['host/project-pmog2/.lock']
        for field,value in [('stateSha256','0'*64),('dirIno',0),('dirDev',-1),('targetBootId','other'),('capturePhase','DRAINED')]:
            self.c['missingLockProofs']={'host/project-pmog2/.lock':{**proof,field:value}}
            with self.assertRaisesRegex(m.Refused,'REGISTERED_WRITER_LOCK_UNPROVEN'):self.validate()
    def test_old_unknown_changed_outcome_refused(self):
        self.edit('host/project-pmog2/state.json',lambda v:v['data']['operations'][0].update(resultHash='a'*64))
        with self.assertRaisesRegex(m.Refused,'PARTICIPANT_ORIGINAL_DRIFT'):self.validate()
    def test_every_persistent_collection_refuses_other_unknown_or_inflight(self):
        for parent in ('host','host/project-p2vox','host/project-pmog2'):
            for field in ('operations','controls','allocations'):
                for status in ('UNKNOWN','INFLIGHT'):
                    with self.subTest(parent=parent,field=field,status=status):
                        self.setUp();self.edit(parent+'/state.json',lambda v:v['data'].setdefault(field,[]).append({'id':'other','status':status}))
                        with self.assertRaises(m.Refused):self.validate()
    def test_malformed_or_unreviewed_persistent_collection_status_refuses(self):
        for parent in ('host','host/project-p2vox'):
            for field,value in [('allocations','corrupt'),('controls',{}),('controls',[{'status':'KNOWN'}]),('operations',[{'id':'other','status':'CREATED'}]),('allocations',[{'id':'other','status':'CREATED'}])]:
                self.setUp();self.edit(parent+'/state.json',lambda v:v['data'].update({field:value}))
                with self.assertRaises(m.Refused):self.validate()
    def test_archived_unresolved_work_is_also_refused(self):
        for status in ('UNKNOWN','INFLIGHT'):
            self.c['files']['host/archive-offline.json']['bytes']=raw({'deep':[{'status':status}]})
            with self.assertRaises(m.Refused):self.validate()
    def test_foreign_registration_uninitialized_transition_and_projectroot(self):
        for field,value in [('initialized',False),('transition',{}),('project',{'id':'p2vox','workspaceId':'other','root':'/outside'})]:
            self.setUp();self.edit('host/state.json',lambda v:v['data']['projects'][0].update({field:value}))
            with self.assertRaises(m.Refused):self.validate()
    def test_duplicate_or_missing_registration(self):
        for replacement in ([],[{'project':{'id':'p2vox'}},{'project':{'id':'p2vox'}}]):
            self.setUp();self.edit('host/state.json',lambda v:v['data'].update(projects=replacement))
            with self.assertRaises(m.Refused):self.validate()
    def test_foreign_lock_missingstore_wronguid_mode_hardlink_refused(self):
        for kind in ('lock','missing','uid','mode','nlink','symlink'):
            self.setUp()
            if kind=='lock':self.edit('host/.lock',lambda v:v.update(pid=111))
            elif kind=='missing':del self.c['files']['host/project-p2vox/.lock']
            else:self.c['files']['host/state.json'][kind]={'uid':0,'mode':0o644,'nlink':2,'symlink':True}[kind]
            with self.assertRaises(m.Refused):self.validate()
    def test_unknown_signed_envelope_refused(self):
        self.c['files']['host/archive-offline.json']['bytes']=raw(sign({'schema':'other-signed.v1'},self.issuer))
        with self.assertRaisesRegex(m.Refused,'UNREVIEWED_SIGNED_SCHEMA'):self.validate()
    def test_wrong_grant_or_revoked_version_fails(self):
        self.edit('host/project-p2vox/state.json',lambda v:v['data'].update(version=2))
        with self.assertRaisesRegex(m.Refused,'PARTICIPANT_GRANT_DRIFT'):self.validate()
    def test_no_floats_duplicate_dangerous_keys_or_nonfinite(self):
        for value in (b'{"a":1,"a":2}',b'{"x":1.2}',b'{"x":NaN}',b'{"constructor":1}'):
            with self.assertRaises(m.Refused):m.parse(value)
    def test_boolean_schema_and_version_are_not_integer_one(self):
        for name,change in [('host/state.json',lambda v:v.update(schema=True)),('host/.lock',lambda v:v.update(schema=True)),('host/project-p2vox/state.json',lambda v:v['data'].update(version=True))]:
            self.setUp();self.edit(name,change)
            with self.assertRaises(m.Refused):self.validate()
    def test_canonical_matches_original_node_utf16_and_lone_surrogate(self):
        value={'\ue000':1,'\U00010000':2,'unicode':'\U0001f600','lone':'\ud800','line':'\u2028','minus':0}
        script="const fs=require('fs');const x=JSON.parse(fs.readFileSync(0,'utf8'));function c(x){return x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?'['+x.map(c).join(',')+']':'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+c(x[k])).join(',')+'}'};process.stdout.write(c(x));"
        executable=shutil.which('node');self.assertIsNotNone(executable,'Node is required for the independent canonical comparison')
        result=subprocess.run([executable,'-e',script],input=json.dumps(value).encode(),capture_output=True,check=True)
        self.assertEqual(m.canonical(value).encode(),result.stdout)
    def test_expired_release_and_wrong_app_key_refuse(self):
        with self.assertRaisesRegex(m.Refused,'SOURCE_RELEASE_INVALID'):m._validate(self.c,self.t,self.p,99999999,m.digest(self.p),m.digest(self.p['grant']),self.pins)
        envelope=self.p['grant'];envelope['signature']=b64(self.peers['app'].sign(b'R16-SIGNED\0'+m.canonical(envelope['body']).encode()))
        with self.assertRaisesRegex(m.Refused,'BAD_SIGNATURE'):self.validate()
    def test_archived_crown_raw_signature_and_operation_payload_binding(self):
        payload={'audience':'r16-crown-isolated-session-v1','request_id':'offline','issued_at':1,'expires_at':60001}
        encoded=raw(payload);private=self.peers['app']
        wire={'schema':1,'key_id':m.bytehash(m._b64(key(private))),'payload_b64':base64.b64encode(encoded).decode(),'signature_b64':base64.b64encode(private.sign(encoded)).decode()}
        body=copy.deepcopy(m.parse(self.c['files']['host/state.json']['bytes'])['data']['operations'][0]['operation']['body']);body.update(id='offline',payloadHash=m.digest(payload))
        op=sign(body,private)
        row={'operation':op,'proof':wire}
        self.c['files']['host/archive-app-call-offline.json']=copy.deepcopy(self.c['files']['host/archive-offline.json'])
        self.c['files']['host/archive-app-call-offline.json']['bytes']=raw(row)
        self.validate()
        wire['signature_b64']=base64.b64encode(b'0'*64).decode()
        self.c['files']['host/archive-app-call-offline.json']['bytes']=raw(row)
        with self.assertRaisesRegex(m.Refused,'CROWN_PROOF_INVALID'):self.validate()
    def test_unbound_crown_history_cannot_change_signed_operation_payload(self):
        payload={'audience':'r16-crown-isolated-session-v1','request_id':'offline','issued_at':1,'expires_at':60001}
        encoded=raw(payload);private=self.peers['app']
        wire={'schema':1,'key_id':m.bytehash(m._b64(key(private))),'payload_b64':base64.b64encode(encoded).decode(),'signature_b64':base64.b64encode(private.sign(encoded)).decode()}
        op=sign({'schema':'r16.operation.v1','id':'offline','grantId':'r16-projects-daily','payloadHash':'0'*64},private)
        self.c['files']['host/archive-offline.json']['bytes']=raw({'operation':op,'proof':wire})
        with self.assertRaisesRegex(m.Refused,'CROWN_OPERATION_BINDING_DRIFT'):self.validate()
    def test_cloud_original_accepted_delivery_active_grant_and_revision(self):
        control={'grantId':'r16-projects-daily','grantVersion':1,'status':'ACTIVE','connectRequested':True}
        delivery=sign({'schema':'r16.configuration-delivery.v1','revision':16,'issuedAt':20,'publicConfig':self.p,'control':control},self.issuer)
        accepted={'schema':1,'revision':3,'maxNow':30,'data':{'kind':'r16.cloud-publication.v1','accepted':delivery}}
        cutover={'schema':'r16.cloud-cutover.v1','phase':'ACTIVE','grantId':'r16-projects-daily','releaseId':'r16-daily-20261012-r15'}
        with patch.object(m,'DELIVERY_DIGEST',m.digest(delivery)):
            result=m.validate_cloud_authority(self.p,control,cutover,accepted)
            self.assertTrue(result['oldGrantActive']);self.assertEqual(result['sourceDeliveryRevision'],16)
            for changed in ({**control,'status':'REVOKED'},{**control,'connectRequested':False},{**control,'grantVersion':2},{**control,'grantVersion':True}):
                with self.assertRaises(m.Refused):m.validate_cloud_authority(self.p,changed,cutover,accepted)
            bad=copy.deepcopy(accepted);bad['data']['accepted']['body']['revision']=17
            with self.assertRaises(m.Refused):m.validate_cloud_authority(self.p,control,cutover,bad)
            with self.assertRaises(m.Refused):m.validate_cloud_authority(self.p,control,{**cutover,'releaseId':'other'},accepted)

class HistoricalProjectTests(unittest.TestCase):
    def setUp(self):
        self.c,self.t,self.p,self.pins,self.issuer,self.peers=fixture()
        self.ids=add_history(self.c,self.t,self.p,self.issuer,self.peers)
    validate=SemanticTests.validate
    edit=SemanticTests.edit
    def data(self,pid):return m.parse(self.c['files']['host/project-'+pid+'/state.json']['bytes'])['data']
    def setdata(self,pid,value):self.edit('host/project-'+pid+'/state.json',lambda x:x.update(data=value))
    def test_all_nine_registered_current_retiring_closed_and_unsigned_prepare_are_verified(self):
        before=copy.deepcopy(self.c['files']);original=fixture()
        result=self.validate();att=result['attestation']
        self.assertEqual(att['registeredProjectCount'],9);self.assertEqual(att['drainStatus'],'UNPROVEN')
        self.assertEqual(att['projectPhaseCounts'],{'active':6,'closing':3,'pending':0,'retirement':3,'transition':1})
        self.assertEqual(set(result['expectedLeaseBindings']),set(self.pins));self.assertEqual(result['expectedOriginalUnknown'],{p:{**pin,'status':'UNKNOWN','resultHash':None} for p,pin in self.pins.items()})
        self.assertEqual(self.c['files'],before);self.assertNotIn('files',result)
        for pid in self.ids:self.assertNotIn(pid,m.canonical(att))
    def test_historical_participant_wrong_grant_role_or_version_refused(self):
        for k,v in [('grant',None),('version',True),('role','native')]:
            self.setUp();self.edit('host/project-'+self.ids[1]+'/state.json',lambda x:x['data'].update({k:v}))
            with self.assertRaisesRegex(m.Refused,'PARTICIPANT_GRANT_DRIFT'):self.validate()
    def test_every_historical_collection_rejects_new_unknown_and_inflight(self):
        for pidindex in (0,1,4,6):
            for field in ('operations','allocations','controls'):
                for status in ('UNKNOWN','INFLIGHT'):
                    self.setUp();self.edit('host/project-'+self.ids[pidindex]+'/state.json',lambda x:x['data'].setdefault(field,[]).append({'id':'foreign','status':status}))
                    with self.assertRaises(m.Refused):self.validate()
    def test_historical_signed_active_lease_wrong_project_or_release_or_activation_refused(self):
        for change in ('project','release','activation','signature'):
            self.setUp();pid=self.ids[1];data=self.data(pid);active=data['active']
            if change=='activation':
                b=active['activation']['body'];b['generation']+=1;active['activation']=sign(b,self.issuer)
            elif change=='signature':active['lease']['signature']='A'*86
            else:
                b=active['lease']['body']
                if change=='project':b['project']['id']=self.ids[2]
                else:b['releaseHash']='0'*64
                active['lease']=sign(b,self.issuer)
            self.setdata(pid,data)
            with self.assertRaises(m.Refused):self.validate()
    def test_historical_retirement_cannot_replace_or_advance_the_signed_generation(self):
        pid=self.ids[0];wrong=self.data(self.ids[1])['active']['lease']
        self.edit('host/state.json',lambda x:x['data']['projects'][2].update(retirement={'lease':wrong}))
        with self.assertRaises(m.Refused):self.validate()
    def test_unsigned_prepare_stage_is_not_a_caller_drain_override(self):
        for change in ('submitted','requestScope','activation','lease','proofs'):
            self.setUp()
            def mutate(x):
                tr=x['data']['projects'][-1]['transition']
                if change=='submitted':tr['submitted']=True
                elif change=='requestScope':tr['request']['project']['workspaceId']='other'
                elif change=='activation':tr['activation']=self.data(self.ids[1])['active']['activation']
                elif change=='lease':tr['lease']=self.data(self.ids[1])['active']['lease']
                else:tr['proofs']={}
            self.edit('host/state.json',mutate)
            with self.assertRaises(m.Refused):self.validate()
    def test_unsigned_unsubmitted_historical_versions_preserved_without_authority(self):
        original=self.validate()
        self.edit('host/state.json',lambda x:x['data']['projects'][-1]['transition']['request'].update(versions={r:'0'*64 for r in self.p['versions']}))
        before=copy.deepcopy(self.c['files']);result=self.validate()
        self.assertEqual(self.c['files'],before)
        self.assertEqual(result['expectedSemanticBindingsDigest'],original['expectedSemanticBindingsDigest'])
        self.assertEqual(result['expectedLeaseBindings'],original['expectedLeaseBindings'])
        self.assertNotEqual(result['attestation']['checkpointManifestDigest'],original['attestation']['checkpointManifestDigest'])
        self.assertEqual(result['attestation']['drainStatus'],'UNPROVEN')
    def test_inert_historical_versions_still_need_exact_roles_and_valid_hashes(self):
        versions={r:'0'*64 for r in self.p['versions']}
        malformed=[None,[],{**versions,'foreign':'0'*64},{r:v for r,v in versions.items() if r!='app'}, {**versions,'app':'g'*64},{**versions,'app':'A'*64},{**versions,'app':'0'*63},{**versions,'app':True}]
        for value in malformed:
            self.setUp();self.edit('host/state.json',lambda x:x['data']['projects'][-1]['transition']['request'].update(versions=value))
            with self.assertRaisesRegex(m.Refused,'PROJECT_TRANSITION_REQUEST_DRIFT'):self.validate()
    def test_historical_versions_are_never_accepted_once_any_effect_evidence_exists(self):
        for field in ('submitted','proofs','lease','activation'):
            self.setUp()
            def mutate(x):
                transition=x['data']['projects'][-1]['transition']
                request=transition['request'];request['versions']={r:'0'*64 for r in self.p['versions']}
                if field=='submitted':transition['submitted']=True
                elif field=='proofs':transition['proofs']={r:sign(request,k) for r,k in self.peers.items()}
                else:transition[field]=copy.deepcopy(self.data(self.ids[1])['active'][field])
            self.edit('host/state.json',mutate)
            with self.assertRaisesRegex(m.Refused,'PROJECT_TRANSITION_REQUEST_DRIFT'):self.validate()
    def prepared(self):
        pid=self.ids[1];data=self.data(pid);l=copy.deepcopy(data['active']['lease']['body']);l.update(generation=l['generation']+1,previousGeneration=l['generation'],requestId='new-prepare')
        request={k:l[k] for k in ('requestId','grantId','grantVersion','project','channel','versions','actions','issuedAt')};request['schema']='r16.prepare.v1'
        lease=sign(l,self.issuer);tr={'request':request,'proofs':{r:sign(request,k) for r,k in self.peers.items()},'submitted':True,'lease':lease,'activation':None}
        self.edit('host/state.json',lambda x:x['data']['projects'][3].update(transition=tr))
        data['pending']={'lease':lease,'closed':False,'evidence':None};self.setdata(pid,data)
        return pid,tr
    def test_three_signed_prepare_and_pending_phase_are_verified_not_executed(self):
        self.prepared();result=self.validate();self.assertEqual(result['attestation']['projectPhaseCounts']['pending'],1)
        self.assertEqual(result['attestation']['drainStatus'],'UNPROVEN')
    def test_prepare_proof_role_request_generation_or_pending_binding_drift_rejected(self):
        for change in ('role','request','generation','pending'):
            self.setUp();pid,tr=self.prepared()
            def mutate(x):
                transition=x['data']['projects'][3]['transition']
                if change=='role':transition['proofs']['native']=sign(tr['request'],self.peers['app'])
                elif change=='request':transition['request']['requestId']='another'
                elif change=='generation':
                    l=copy.deepcopy(tr['lease']['body']);l.update(generation=99,previousGeneration=98);transition['lease']=sign(l,self.issuer)
                else:transition['lease']=self.data(self.ids[2])['active']['lease']
            self.edit('host/state.json',mutate)
            with self.assertRaises(m.Refused):self.validate()
    def test_closed_generation_requires_actual_signed_issuer_archive(self):
        pid=self.ids[4];name='host/archive-app-close-'+pid+'-2.json'
        del self.c['files'][name]
        with self.assertRaisesRegex(m.Refused,'PROJECT_CLOSED_PROOF_MISSING'):self.validate()
    def test_stopped_proof_wrong_project_role_generation_or_archive_name_refused(self):
        for change in ('project','role','generation','name'):
            self.setUp();pid=self.ids[4];data=self.data(pid);proof=copy.deepcopy(data['stopped'][0]);b=proof['body']
            if change=='project':b['projectId']=self.ids[5]
            elif change=='role':b['peerId']='foreign-peer'
            elif change=='generation':b['generation']+=1
            else:
                name=next(n for n in self.c['files'] if n.startswith('host/project-'+pid+'/archive-stop-'))
                self.c['files'][name.replace(b['leaseHash'],'0'*64)]=self.c['files'].pop(name)
            if change!='name':data['stopped']=[sign(b,self.peers['app'])];self.setdata(pid,data)
            with self.assertRaises(m.Refused):self.validate()
    def test_known_history_must_match_signed_app_operation_and_result_hash(self):
        for change in ('operationHash','result','generation','outcome','unsigned'):
            self.setUp();pid=self.ids[1];data=self.data(pid);row=data['operations'][0]
            if change=='operationHash':row['hash']='0'*64
            elif change=='result':row['resultHash']='0'*64
            elif change=='generation':row['generation']+=1
            elif change=='outcome':row['outcome']='UNREVIEWED'
            else:row['id']='unregistered-operation'
            self.setdata(pid,data)
            with self.assertRaises(m.Refused):self.validate()
    def archive_history(self):
        pid=self.ids[1];data=self.data(pid);record=data['operations'].pop(0);base='host/project-'+pid
        def put(name,value):self.c['files'][name]={'bytes':raw(value),'regular':True,'symlink':False,'uid':1000,'nlink':1,'mode':0o600}
        put(base+'/archive-operation-'+m.digest(record['id'])+'.json',record)
        generation={'schema':'r16.generation-archive.v1','generation':record['generation'],'previous':None,'records':[{'id':record['id'],'hash':m.digest(record)}]}
        name='generation-'+str(record['generation'])+'-'+m.digest(generation)
        put(base+'/archive-'+name+'.json',generation);data['archiveHead']={'name':name,'hash':m.digest(generation)};self.setdata(pid,data)
        return pid,name,record
    def test_known_generation_archive_chain_and_signed_operation_are_bound(self):
        self.archive_history();self.validate()
    def app_call(self):
        pid=self.ids[1];host=m.parse(self.c['files']['host/state.json']['bytes'])
        row=next(x for x in host['data']['operations'] if x['projectId']==pid)
        body=copy.deepcopy(row['operation']['body']);payload={'audience':'r16-crown-isolated-session-v1','request_id':row['id'],'issued_at':1,'expires_at':60001}
        body['payloadHash']=m.digest(payload);row['operation']=sign(body,self.peers['app'])
        self.c['files']['host/state.json']['bytes']=raw(host)
        data=self.data(pid);data['operations'][0]['hash']=m.digest(row['operation']);self.setdata(pid,data)
        encoded=raw(payload);wire={'schema':1,'key_id':m.bytehash(m._b64(key(self.peers['app']))),'payload_b64':base64.b64encode(encoded).decode(),'signature_b64':base64.b64encode(self.peers['app'].sign(encoded)).decode()}
        template=copy.deepcopy(self.c['files']['host/archive-offline.json'])
        call='host/archive-app-call-'+row['id']+'.json';record='host/archive-app-operation-'+row['id']+'.json'
        self.c['files'][call]={**template,'bytes':raw({'operation':row['operation'],'proof':wire})}
        self.c['files'][record]={**template,'bytes':raw(row)}
        return call,record
    def test_original_app_call_pair_and_app_operation_row_can_coexist_same_id(self):
        call,record=self.app_call();self.validate()
        self.assertEqual(set(m.parse(self.c['files'][call]['bytes'])),{'operation','proof'})
        self.assertIn('status',m.parse(self.c['files'][record]['bytes']))
    def test_app_call_filename_signature_payload_and_shape_are_bound(self):
        for change in ('name','signature','payload','shape'):
            self.setUp();call,_=self.app_call()
            if change=='name':self.c['files'][call.replace('app-call-','app-call-foreign-')]=self.c['files'].pop(call)
            elif change=='signature':self.edit(call,lambda x:x['operation'].update(signature='A'*86))
            elif change=='shape':self.edit(call,lambda x:x.update(status='KNOWN'))
            else:
                def mutate(x):
                    body=x['operation']['body'];body['payloadHash']='0'*64;x['operation']=sign(body,self.peers['app'])
                self.edit(call,mutate)
            with self.assertRaises(m.Refused):self.validate()
    def test_app_operation_archive_name_and_record_result_are_bound(self):
        for change in ('name','result'):
            self.setUp();_,record=self.app_call()
            if change=='name':self.c['files'][record.replace('app-operation-','app-operation-foreign-')]=self.c['files'].pop(record)
            else:self.edit(record,lambda x:x.update(resultHash='0'*64))
            with self.assertRaises(m.Refused):self.validate()
    def test_archived_generation_hash_missing_record_and_unsigned_record_are_refused(self):
        for change in ('hash','missing','record','cycle'):
            self.setUp();pid,name,record=self.archive_history();base='host/project-'+pid
            if change=='hash':self.edit(base+'/state.json',lambda x:x['data']['archiveHead'].update(hash='0'*64))
            elif change=='missing':del self.c['files'][base+'/archive-operation-'+m.digest(record['id'])+'.json']
            elif change=='record':self.edit(base+'/archive-operation-'+m.digest(record['id'])+'.json',lambda x:x.update(hash='0'*64))
            else:self.edit(base+'/archive-'+name+'.json',lambda x:x.update(previous={'name':name,'hash':m.digest(x)}))
            with self.assertRaises(m.Refused):self.validate()
    def test_unregistered_store_missing_store_and_duplicate_graph_do_not_become_allowed(self):
        for change in ('unregistered','missing','duplicate','unsafe','foreignRoot'):
            self.setUp();pid=self.ids[0]
            if change=='unregistered':self.c['files']['host/project-unregistered/state.json']=copy.deepcopy(self.c['files']['host/project-'+pid+'/state.json'])
            elif change=='missing':del self.c['files']['host/project-'+pid+'/state.json']
            else:
                def mutate(x):
                    rows=x['data']['projects']
                    if change=='duplicate':rows.append(copy.deepcopy(rows[-1]))
                    elif change=='unsafe':rows[-1]['project']['id']='../escape'
                    else:rows[-1]['project']['root']='/foreign/workspace'
                self.edit('host/state.json',mutate)
            with self.assertRaises(m.Refused):self.validate()
    def test_extra_store_missing_and_stale_locks_require_derived_proofs(self):
        pid=self.ids[4];base='host/project-'+pid;del self.c['files'][base+'/.lock']
        with self.assertRaisesRegex(m.Refused,'REGISTERED_WRITER_LOCK_UNPROVEN'):self.validate()
        self.c['missingLockProofs']=m._missing_lock_proofs(self.c['files'],{base:(1,123)},self.t,'FROZEN');self.validate()
        row=self.c['files']['host/project-'+self.ids[5]+'/.lock'];lock=m.parse(row['bytes']);lock.update(pid=777,start='888');row['bytes']=raw(lock)
        with self.assertRaisesRegex(m.Refused,'FOREIGN_STORE_WRITER'):self.validate()
        with patch.object(m,'_start',side_effect=FileNotFoundError):self.c['staleLockProofs']=m._stale_lock_proofs(self.c['files'],self.t)
        self.validate()

class ReaderTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.addCleanup(self.tmp.cleanup)
    def test_production_capture_denies_nonroot_before_opening_anything(self):
        with patch.object(m.os,'geteuid',return_value=1000),patch.object(m,'read_public',side_effect=AssertionError('must not read')):
            with self.assertRaisesRegex(m.Refused,'FIXED_ROOT_CLOUD_REQUIRED'):m.LedgerCheckpoint().capture({})
    def test_production_capture_denies_wronghost_before_any_protectedread(self):
        with patch.object(m.os,'geteuid',return_value=0),patch.object(m.platform,'node',return_value='fixture'),patch.object(m,'read_public',side_effect=AssertionError('must not read')):
            with self.assertRaisesRegex(m.Refused,'FIXED_ROOT_CLOUD_REQUIRED'):m.LedgerCheckpoint().capture({})
    def test_readonly_readat_real_fixture_preserves_bytes_and_mode(self):
        p=self.root/'state.json';p.write_bytes(b'{"fixture":true}');p.chmod(0o600)
        fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY)
        try:raw,st=m._read_at(fd,p.name,uid=os.geteuid(),mode=0o600)
        finally:os.close(fd)
        self.assertEqual(raw,p.read_bytes());self.assertEqual(stat.S_IMODE(st.st_mode),0o600)
    def test_symlink_hardlink_fifo_and_extra_permissions_refused(self):
        real=self.root/'real';real.write_bytes(b'{}');real.chmod(0o600)
        os.symlink(real,self.root/'symlink');os.link(real,self.root/'hardlink');os.mkfifo(self.root/'fifo',0o600)
        fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY)
        try:
            for name in ('real','symlink','hardlink','fifo'):
                with self.assertRaises((m.Refused,OSError)):m._read_at(fd,name,uid=os.geteuid(),mode=0o600)
        finally:os.close(fd)
    def make_proc(self,fd_target=None,flags='0100000',maps=''):
        proc=self.root/'proc';entry=proc/'999999';(entry/'fd').mkdir(parents=True);(entry/'fdinfo').mkdir()
        (entry/'stat').write_text('999999 (fixture) '+' '.join(['S']+['0']*18+['123']))
        (entry/'maps').write_text(maps)
        if fd_target:
            os.symlink(fd_target,entry/'fd/3');(entry/'fdinfo/3').write_text('flags:\t'+flags+'\n')
        return proc
    def test_foreign_writable_fd_refused_but_readonly_allowed(self):
        file=self.root/'state.json';file.write_bytes(b'{}');st=file.stat();ids={'host/state.json':(st.st_dev,st.st_ino)}
        proc=self.make_proc(file,flags='0100002')
        with self.assertRaisesRegex(m.Refused,'FOREIGN_WRITABLE_FD'):m._scan_writers(ids,{},4343,proc=proc)
        (proc/'999999/fdinfo/3').write_text('flags:\t0100000\n');m._scan_writers(ids,{},4343,proc=proc)
    def test_shared_writable_mapping_even_without_open_fd_refuses(self):
        file=self.root/'state.json';file.write_bytes(b'{}');st=file.stat();dev=f'{os.major(st.st_dev):x}:{os.minor(st.st_dev):x}'
        proc=self.make_proc(maps=f'1-2 rw-s 0 {dev} {st.st_ino} synthetic\n')
        with self.assertRaisesRegex(m.Refused,'FOREIGN_WRITABLE_SHARED_MAPPING'):m._scan_writers({'x':(st.st_dev,st.st_ino)},{},4343,proc=proc)
    def test_foreign_open_directory_capability_refuses(self):
        st=self.root.stat();proc=self.make_proc(self.root)
        with self.assertRaisesRegex(m.Refused,'FOREIGN_STORE_DIRECTORY_FD'):m._scan_writers({}, {'host':(st.st_dev,st.st_ino)},4343,proc=proc)
    def test_unproven_fd_access_refuses(self):
        file=self.root/'state.json';file.write_bytes(b'{}');st=file.stat();proc=self.make_proc(file,flags='not-octal')
        with self.assertRaisesRegex(m.Refused,'FD_ACCESS_UNPROVEN'):m._scan_writers({'x':(st.st_dev,st.st_ino)},{},4343,proc=proc)
    def test_public_cli_has_no_capture_and_exports_no_privatebytes(self):
        r=subprocess.run(['python3','-I','-B',str(Path(m.__file__))],capture_output=True,check=False)
        self.assertEqual(r.returncode,78);self.assertEqual(json.loads(r.stdout)['rawStateExported'],False)
    def tree(self):
        c,t,p,pins,issuer,peers=fixture()
        root=self.root/'host';root.mkdir(mode=0o700)
        for name,row in c['files'].items():
            file=self.root/name;file.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            file.write_bytes(row['bytes']);file.chmod(0o600)
        return root,c,t,p,pins
    def opener(self,root):
        def opened(path,**kwargs):
            self.assertEqual(path,root);return os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        return opened
    def test_real_fixture_complete_tree_reader_and_original_bytes(self):
        root,c,*_=self.tree()
        # Simulate GitHub's logical UID even when this host actually uses 1000.
        # The inner test seam translates only UID, preserving all real fields.
        with fixture_metadata_uid(1001):
            with patch.object(m,'_open_directory',self.opener(root)),fixture_metadata_uid(1000):
                files,ids,dirs=m.read_store_tree(root)
            self.assertEqual(files,c['files']);self.assertEqual(len(ids),9);self.assertEqual(len(dirs),3)
            # Without the test translation, the production UID-1000 guard must
            # reject the same tree observed as UID 1001.
            with patch.object(m,'_open_directory',self.opener(root)):
                with self.assertRaisesRegex(m.Refused,'STORE_DIRECTORY_REFUSED'):m.read_store_tree(root)
    def test_real_tree_temp_extra_directory_and_unreviewed_file_refused(self):
        root,*_=self.tree()
        for name,isdir in [('.next-partial',False),('.reclaim',False),('unregistered',True),('secret-file',False)]:
            file=root/name
            if isdir:file.mkdir(mode=0o700)
            else:file.write_bytes(b'{}');file.chmod(0o600)
            try:
                with patch.object(m,'_open_directory',self.opener(root)),fixture_metadata_uid(1000):
                    with self.assertRaises(m.Refused):m.read_store_tree(root)
            finally:
                if isdir:file.rmdir()
                else:file.unlink()
    def test_directory_and_file_symlink_real_tree_rejected(self):
        root,*_=self.tree();outside=self.root/'outside';outside.mkdir(mode=0o700)
        os.symlink(outside,root/'extra')
        with patch.object(m,'_open_directory',self.opener(root)),fixture_metadata_uid(1000):
            with self.assertRaises(m.Refused):m.read_store_tree(root)
    def test_complete_capture_pipeline_offline_no_realroot_no_proc(self):
        root,c,t,p,pins=self.tree()
        manifest={'role':'app','files':{}}
        def read_public(path):
            if path==m.PUBLIC:return p
            if path==m.SELECTOR:return {'schema':'r16.app-host.v1','publicConfiguration':str(m.PUBLIC),'codeManifest':str(m.SOURCE/'app-manifest.json')}
            return manifest
        dirs={'host':(1,2),'host/project-p2vox':(1,3),'host/project-pmog2':(1,4)}
        with patch.object(m.os,'geteuid',return_value=0),patch.object(m.platform,'node',return_value=m.HOST),patch.object(m,'_target_state',return_value='FROZEN'),patch.object(m,'read_public',side_effect=read_public),patch.object(m,'read_accepted',return_value={}),patch.object(m,'read_registration',return_value=registered()),patch.object(m,'validate_cloud_authority',return_value={'oldGrantActive':True,'sourceDeliveryRevision':16}),patch.object(m,'APP_VERSION',p['versions']['app']),patch.object(m,'PUBLIC_DIGEST',m.digest(p)),patch.object(m,'GRANT_DIGEST',m.digest(p['grant'])),patch.object(m,'PINS',pins),patch.object(m.time,'time',return_value=0.1),patch.object(m,'read_store_tree',return_value=(c['files'],{},dirs)),patch.object(m,'_scan_writers') as scan:
            result=m.LedgerCheckpoint().capture(t)
        self.assertEqual(result['files'],c['files']);self.assertEqual(result['attestation']['capturePhase'],'FROZEN');self.assertEqual(scan.call_count,2)
    def test_capture_rejects_changing_complete_snapshot_before_signatureacceptance(self):
        c,t,p,*_=fixture();manifest={'role':'app','files':{}}
        two=copy.deepcopy(c['files']);two['host/state.json']['bytes']+=b' '
        def read_public(path):
            if path==m.PUBLIC:return p
            if path==m.SELECTOR:return {'schema':'r16.app-host.v1','publicConfiguration':str(m.PUBLIC),'codeManifest':str(m.SOURCE/'app-manifest.json')}
            return manifest
        with patch.object(m.os,'geteuid',return_value=0),patch.object(m.platform,'node',return_value=m.HOST),patch.object(m,'_target_state',return_value='FROZEN'),patch.object(m,'read_public',side_effect=read_public),patch.object(m,'read_accepted',return_value={}),patch.object(m,'read_registration',return_value=registered()),patch.object(m,'validate_cloud_authority',return_value={}),patch.object(m,'APP_VERSION',p['versions']['app']),patch.object(m,'digest',return_value=p['versions']['app']),patch.object(m,'read_store_tree',side_effect=[(c['files'],{},{'host':(1,2)}),(two,{},{'host':(1,2)})]),patch.object(m,'_scan_writers'),patch.object(m,'validate_checkpoint',side_effect=AssertionError('must not validate changed tree')):
            with self.assertRaisesRegex(m.Refused,'CHECKPOINT_CHANGED'):m.LedgerCheckpoint().capture(t)
    def test_missing_lock_full_capture_derives_proof_only_after_twice_writer_scan(self):
        c,t,p,pins,*_=fixture();del c['files']['host/project-pmog2/.lock']
        dirs={'host':(1,2),'host/project-p2vox':(1,3),'host/project-pmog2':(1,4)};manifest={'role':'app','files':{}}
        def read_public(path):
            if path==m.PUBLIC:return p
            if path==m.SELECTOR:return {'schema':'r16.app-host.v1','publicConfiguration':str(m.PUBLIC),'codeManifest':str(m.SOURCE/'app-manifest.json')}
            return manifest
        with patch.object(m.os,'geteuid',return_value=0),patch.object(m.platform,'node',return_value=m.HOST),patch.object(m,'_target_state',return_value='FROZEN'),patch.object(m,'read_public',side_effect=read_public),patch.object(m,'read_accepted',return_value={}),patch.object(m,'read_registration',return_value=registered()),patch.object(m,'validate_cloud_authority',return_value={}),patch.object(m,'APP_VERSION',p['versions']['app']),patch.object(m,'PUBLIC_DIGEST',m.digest(p)),patch.object(m,'GRANT_DIGEST',m.digest(p['grant'])),patch.object(m,'PINS',pins),patch.object(m.time,'time',return_value=0.1),patch.object(m,'read_store_tree',return_value=(c['files'],{},dirs)),patch.object(m,'_scan_writers') as scan:
            result=m.LedgerCheckpoint().capture(t)
        self.assertEqual(scan.call_count,2);self.assertEqual(result['attestation']['missingLockProofs']['host/project-pmog2/.lock']['dirIno'],4)
    def target_state(self,start,members='4343\n',events='frozen 1\npopulated 1\n',exists=True,baseline=False):
        _,target,*_=fixture()
        def read(path,*a,**kw):
            name=str(path)
            if name.endswith('/boot_id'):return target['bootId']+'\n'
            if name.endswith('/cgroup.procs'):
                if members is None:raise FileNotFoundError()
                return members
            if name.endswith('/cgroup.events'):
                if events is None:raise FileNotFoundError()
                return events
            if name.endswith('/cgroup'):return '0::'+m.CGROUP+'\n'
            raise AssertionError('unexpected metadata read')
        start_effect=FileNotFoundError if start is None else lambda pid:start
        with patch.object(m,'_start',side_effect=start_effect),patch.object(m.Path,'read_text',autospec=True,side_effect=read),patch.object(m.Path,'exists',autospec=True,return_value=exists):
            return m._target_state(target,baseline)
    def test_kernel_frozen_required_but_baseline_is_explicit_not_drainproof(self):
        self.assertEqual(self.target_state('123456'),'FROZEN')
        self.assertEqual(self.target_state('123456',events='frozen 0\n',baseline=True),'BASELINE_NOT_DRAIN_PROOF')
        with self.assertRaisesRegex(m.Refused,'KERNEL_FREEZE_UNPROVEN'):self.target_state('123456',events='frozen 0\n')
    def test_after_exit_entire_cgroup_gone_or_empty_is_accepted(self):
        self.assertEqual(self.target_state(None,members=None,events=None,exists=False),'EXITED')
        self.assertEqual(self.target_state(None,members='',events='frozen 0\n'),'EXITED')
    def test_partial_missing_cgroup_metadata_never_proves_exit(self):
        for members,events in [(None,'frozen 0\n'),('',None)]:
            with self.assertRaisesRegex(m.Refused,'CGROUP_OBSERVATION_UNPROVEN'):self.target_state(None,members=members,events=events,exists=True)
    def test_cgroup_gone_cannot_hide_live_or_reused_pid_or_baseline(self):
        for start,baseline in [('123456',False),('999',False),(None,True)]:
            with self.assertRaises(m.Refused):self.target_state(start,members=None,events=None,exists=False,baseline=baseline)
        with self.assertRaisesRegex(m.Refused,'TARGET_IDENTITY_DRIFT'):self.target_state('999')
    def test_extra_member_or_live_fd_can_never_be_missing_lock_proof(self):
        with self.assertRaises(m.Refused):self.target_state('123456',members='4343\n111\n')
        file=self.root/'state.json';file.write_bytes(b'{}');st=file.stat();proc=self.make_proc(file,flags='0100001')
        with self.assertRaisesRegex(m.Refused,'FOREIGN_WRITABLE_FD'):m._scan_writers({'x':(st.st_dev,st.st_ino)},{},4343,proc=proc)
    def registered_capture(self,*,missing=False,wrong_inode=False,changed=False,history=False):
        """Real capture orchestration, real tree reader and signed validation.

        Only fixed production file reads, root context and kernel observations
        are replaced by this local fixture. No actual protected read occurs.
        """
        c,t,p,pins,issuer,peers=fixture()
        if history:add_history(c,t,p,issuer,peers)
        root=self.root/'capture-host';root.mkdir(mode=0o700)
        for name,row in c['files'].items():
            path=root/name.removeprefix('host/');path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            path.write_bytes(row['bytes']);path.chmod(0o600)
        st=root.stat();record,h=registered((st.st_dev,st.st_ino+(1 if wrong_inode else 0)))
        control={'grantId':'r16-projects-daily','grantVersion':1,'status':'ACTIVE','connectRequested':True}
        delivery=sign({'schema':'r16.configuration-delivery.v1','revision':16,'issuedAt':20,'publicConfig':p,'control':control},issuer)
        accepted={'schema':1,'revision':3,'maxNow':30,'data':{'kind':'r16.cloud-publication.v1','accepted':delivery}}
        public={m.PUBLIC:p,m.SELECTOR:{'schema':'r16.app-host.v1','publicConfiguration':str(m.PUBLIC),'codeManifest':str(m.SOURCE/'app-manifest.json')},m.SOURCE/'app-manifest.json':{'role':'app','files':{}},m.CONTROL:control,m.CUTOVER:{'schema':'r16.cloud-cutover.v1','phase':'ACTIVE','grantId':'r16-projects-daily','releaseId':'r16-daily-20261012-r15'}}
        def opened(path,**kwargs):
            self.assertEqual(path,m.STORE)
            return os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        with ExitStack() as stack:
            stack.enter_context(fixture_metadata_uid(1000))
            patches=[patch.object(m.os,'geteuid',return_value=0),patch.object(m.platform,'node',return_value=m.HOST),patch.object(m,'_target_state',return_value='FROZEN'),patch.object(m,'read_public',side_effect=lambda path:copy.deepcopy(public[path])),patch.object(m,'read_accepted',return_value=accepted),patch.object(m,'_open_directory',side_effect=opened),patch.object(m,'PUBLIC_DIGEST',m.digest(p)),patch.object(m,'GRANT_DIGEST',m.digest(p['grant'])),patch.object(m,'APP_VERSION',p['versions']['app']),patch.object(m,'PINS',pins),patch.object(m,'DELIVERY_DIGEST',m.digest(delivery)),patch.object(m.time,'time',return_value=0.1),patch.object(m,'_scan_writers')]
            if missing:patches.append(patch.object(m,'read_registration',side_effect=m.Refused('SEALED_REGISTRATION_MISSING')))
            elif changed:patches.append(patch.object(m,'read_registration',side_effect=[(record,h),({**record,'phase':'PREPARING'},'f'*64)]))
            else:patches.append(patch.object(m,'read_registration',return_value=(record,h)))
            if wrong_inode:patches.append(patch.object(m,'_read_at',side_effect=AssertionError('must reject before private bytes')))
            for item in patches:stack.enter_context(item)
            result=m.LedgerCheckpoint().capture(t)
        return result,h
    def test_registry_real_capture_pipeline_matches_sealed_inode_and_all_signatures(self):
        result,h=self.registered_capture()
        self.assertTrue(result['attestation']['sealedRegistrationVerified'])
        self.assertEqual(result['attestation']['registrationHash'],h)
        self.assertTrue(result['attestation']['signatureVerification']);self.assertEqual(result['attestation']['sourceDeliveryRevision'],16)
    def test_registry_real_capture_pipeline_nine_store_registered_graph(self):
        result,h=self.registered_capture(history=True)
        self.assertTrue(result['attestation']['sealedRegistrationVerified']);self.assertEqual(result['attestation']['registeredProjectCount'],9)
        self.assertEqual(len(result['expectedLeaseBindings']),2);self.assertEqual(result['attestation']['drainStatus'],'UNPROVEN')
    def test_registry_missing_refuses_real_capture(self):
        with self.assertRaisesRegex(m.Refused,'SEALED_REGISTRATION_MISSING'):self.registered_capture(missing=True)
    def test_registry_replaced_host_inode_refuses_before_reading_any_ledger_file(self):
        with self.assertRaisesRegex(m.Refused,'SEALED_APP_DIRECTORY_IDENTITY_DRIFT'):self.registered_capture(wrong_inode=True)
    def test_registry_must_stay_byte_identical_across_both_tree_snapshots(self):
        with self.assertRaisesRegex(m.Refused,'SEALED_REGISTRATION_CHANGED'):self.registered_capture(changed=True)
    def test_registry_exact_scope_phase_grant_and_spec_order(self):
        record,_=registered()
        for field,value in [('phase','PREPARING'),('grantId','other'),('schema','other'),('specs',list(reversed(record['specs']))),('specs',[{**record['specs'][0],'path':'/other'},*record['specs'][1:]])]:
            with self.subTest(field=field,value=value):
                with self.assertRaises(m.Refused):m.registration_bindings({**record,field:value})
        with self.assertRaises(m.Refused):m.registration_bindings({**record,'extra':True})
    def test_registry_identities_exact_three_no_duplicate_role_or_inode_or_boolean(self):
        record,_=registered();rows=record['identities']
        invalid=[
            rows[:2], [rows[0],rows[0],rows[2]],
            [rows[0],{**rows[1],'dev':rows[0]['dev'],'ino':rows[0]['ino']},rows[2]],
            [{**rows[0],'ino':True},*rows[1:]],
            [{**rows[0],'dev':-1},*rows[1:]],
            [{**rows[0],'role':'foreign'},*rows[1:]],
        ]
        for identities in invalid:
            with self.subTest(identities=identities):
                with self.assertRaises(m.Refused):m.registration_bindings({**record,'identities':identities})
    def test_registry_reader_uses_only_original_root_mode_and_fixed_digest_filename(self):
        record,_=registered();payload=raw(record)
        with patch.object(m,'_open_directory',return_value=123) as directory,patch.object(m,'_read_at',return_value=(payload,None)) as read,patch.object(m.os,'close'):
            value,h=m.read_registration()
        directory.assert_called_once_with(m.REGISTRY_DIRECTORY,leaf_uid=0,leaf_mode=0o700)
        read.assert_called_once_with(123,m.digest('r16-projects-daily')+'.json',uid=0,mode=0o600,max_bytes=32767)
        self.assertEqual(value,record);self.assertEqual(h,m.bytehash(payload))


if __name__ == '__main__': unittest.main()
