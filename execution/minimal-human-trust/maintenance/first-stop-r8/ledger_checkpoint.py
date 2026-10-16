"""Fixed, read-only R15 App attestor. Private bytes never leave returned memory.

No ProtectedStore instance is opened: its constructor would change writer locks.
The public CLI deliberately has no capture option. Only an admitted root caller
may invoke LedgerCheckpoint; this component creates no human authority itself.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

HOST = 'VM-0-12-ubuntu'
UNIT = 'r16-app.service'
CGROUP = '/system.slice/r16-app.service'
STORE = Path('/var/lib/r16-app/grants/r16-projects-daily/host')
PUBLIC = Path('/etc/r16-cloud/public-config.json')
SELECTOR = Path('/etc/r16-cloud/app-host.json')
CONTROL = Path('/etc/r16-cloud/authority-control.json')
CUTOVER = Path('/etc/r16-cloud/cutover.json')
ACCEPTED = Path('/var/lib/r16-cloud/authority/state.json')
REGISTRY_DIRECTORY = Path('/var/lib/r16-cloud/ledger-registry')
REGISTRY_FILE = REGISTRY_DIRECTORY / (hashlib.sha256(b'"r16-projects-daily"').hexdigest()+'.json')
REGISTRY_SPECS = [
 {'role':'app','path':str(STORE)},
 {'role':'bridge','path':'/var/lib/r16-bridge/grants/r16-projects-daily/bridge'},
 {'role':'gateway','path':'/var/lib/r16-bridge/grants/r16-projects-daily/gateway'},
]
SOURCE = Path('/opt/r16/releases/r16-daily-20261012-r15')
PUBLIC_DIGEST = 'be3ff2b5125f8212206d2848bb32889c3c6b50a8ca56aa3b1a4bc4359591bbdb'
GRANT_DIGEST = '00ac437d66143e627132975555d06396d69ff69616f630d19e3622627e15c5e6'
APP_VERSION = '235a5b919c65ac1d73290732d2b2014c24a338cc4b6795a5064e804803ec1e7a'
DELIVERY_DIGEST = '5ee11707da0d3a524550db92f8c0a5a80b7a8dac8c97f5a907b47fc956c6ec44'
PINS = {
 'p2vox': {'operationId':'c434da49-055a-43dc-a3e3-695cce137909','generation':30,'operationHash':'fd13e74ce69cb8ec30817ca0a48631cf3a6b6b2b08a410cc1b442df41992cc1f'},
 'pmog2': {'operationId':'d0364f8b-3a68-4ca2-a396-7953b29cee4c','generation':38,'operationHash':'38f6af1386e78e5d7ccd0710077d6a3a5e753e81722dd10f11a3a2ff9bd85da1'},
}
MAX_FILE = 16 * 1024 * 1024
MAX_BYTES = 64 * 1024 * 1024
MAX_FILES = 100000

class Refused(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)

def need(ok, code):
    if not ok:
        raise Refused(code)

def _string(value):
    # JSON.stringify emits valid surrogate pairs as UTF-8 and lone surrogates as
    # escaped code units. Python's default ensure_ascii=False needs this repair.
    raw = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    return ''.join('\\u%04x' % ord(c) if 0xD800 <= ord(c) <= 0xDFFF else c for c in raw)

def canonical(value):
    if value is None: return 'null'
    if type(value) is bool: return 'true' if value else 'false'
    if type(value) is int:
        need(abs(value) <= 9007199254740991, 'NONCANONICAL_JSON')
        return str(value)
    if isinstance(value, str): return _string(value)
    if isinstance(value, list): return '[' + ','.join(canonical(x) for x in value) + ']'
    need(type(value) is dict and all(isinstance(k, str) and k not in ('__proto__','prototype','constructor') for k in value), 'NONCANONICAL_JSON')
    keys = sorted(value, key=lambda k: k.encode('utf-16-be', 'surrogatepass'))
    return '{' + ','.join(_string(k)+':'+canonical(value[k]) for k in keys) + '}'

def digest(value): return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()
def bytehash(raw): return hashlib.sha256(raw).hexdigest()

def parse(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value, 'CORRUPT_JSON')
            value[key] = item
        return value
    def bad(_): raise Refused('NONCANONICAL_JSON')
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_float=bad, parse_constant=bad)
        canonical(value)
        return value
    except Refused: raise
    except (ValueError, UnicodeError, RecursionError): raise Refused('CORRUPT_JSON') from None

def _b64(value):
    need(isinstance(value, str) and re.fullmatch('[A-Za-z0-9_-]+', value) is not None, 'BAD_SIGNATURE')
    try: raw = base64.urlsafe_b64decode(value+'='*((-len(value)) % 4))
    except ValueError: raise Refused('BAD_SIGNATURE') from None
    need(base64.urlsafe_b64encode(raw).decode().rstrip('=') == value, 'BAD_SIGNATURE')
    return raw

def verified(envelope, key, schema):
    need(type(envelope) is dict and set(envelope) == {'body','signature'} and isinstance(envelope['body'],dict) and envelope['body'].get('schema') == schema, 'SIGNED_ENVELOPE_INVALID')
    try:
        der = _b64(key)
        public = serialization.load_der_public_key(der)
        need(isinstance(public, Ed25519PublicKey) and public.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo) == der, 'BAD_SIGNATURE')
        sig = _b64(envelope['signature']);need(len(sig) == 64, 'BAD_SIGNATURE')
        public.verify(sig, b'R16-SIGNED\0'+canonical(envelope['body']).encode())
    except Refused: raise
    except Exception: raise Refused('BAD_SIGNATURE') from None
    return envelope['body']

def _wrapper(value, kind):
    need(type(value) is dict and set(value) == {'schema','revision','maxNow','data'} and type(value['schema']) is int and value['schema'] == 1 and type(value['revision']) is int and value['revision'] >= 0 and type(value['maxNow']) is int and value['maxNow'] >= 0 and type(value['data']) is dict and value['data'].get('kind') == kind, 'STORE_WRAPPER_INVALID')
    return value['data']

def _public(pub, now, anchor, grant_anchor):
    need(digest(pub) == anchor and digest(pub.get('grant')) == grant_anchor, 'PUBLIC_TRUST_ROOT_DRIFT')
    g = verified(pub['grant'], pub['issuerPublicKey'], 'r16.workspace.v1')
    r = verified(pub['release'], pub['releasePublicKey'], 'r16.release.v1')
    need(g['id'] == 'r16-projects-daily' and g['version'] == 1 and g['channel'] == pub['channel'] == 'main' and g['peers'] == pub['peers'], 'GRANT_SCOPE_DRIFT')
    need(r['id'] == 'r16-daily-20261012-r15' and r['versions'] == pub['versions'] and r['issuedAt'] <= now < r['notAfter'] and set(g['actions']) <= set(r['actions']), 'SOURCE_RELEASE_INVALID')
    return g, r

def _verify_embedded(value, pub, role_hint=None):
    if isinstance(value, list):
        for item in value: _verify_embedded(item, pub, role_hint)
    elif isinstance(value, dict):
        if any(k in value for k in ('payload_b64','signature_b64','key_id')):
            _crown_wire(value,pub)
        if isinstance(value.get('operation'),dict) and isinstance(value.get('proof'),dict) and 'payload_b64' in value['proof']:
            call=_crown_wire(value['proof'],pub)
            op=verified(value['operation'],pub['peers']['app']['publicKey'],'r16.operation.v1')
            need(op.get('id') == call['request_id'] and op.get('payloadHash') == digest(call),'CROWN_OPERATION_BINDING_DRIFT')
        if 'signature' in value or ('body' in value and isinstance(value['body'],dict) and 'schema' in value['body']):
            schema = value.get('body',{}).get('schema')
            issuer = {'r16.workspace.v1','r16.lease.v1','r16.activation.v1','r16.closed.v1','r16.fresh.v1','r16.prepare-status.v1','r16.revocation-status.v1'}
            app = {'r16.operation.v1','r16.workspace-control.v1','r16.workspace-route.v1','r16.fresh-request.v1','r16.revocation-ack.v1'}
            if schema in issuer: key = pub['issuerPublicKey']
            elif schema == 'r16.release.v1': key = pub['releasePublicKey']
            elif schema in app:
                role = value['body'].get('role','app')
                need(role in pub['peers'], 'SIGNED_ROLE_INVALID');key = pub['peers'][role]['publicKey']
            elif schema in {'r16.workspace-control-result.v1'}: key = pub['peers']['native']['publicKey']
            elif schema in {'r16.close.v1','r16.stopped.v1','r16.result.v1'}:
                role = value['body'].get('role');need(role in pub['peers'], 'SIGNED_ROLE_INVALID');key = pub['peers'][role]['publicKey']
            elif schema == 'r16.prepare.v1':
                need(role_hint in pub['peers'], 'PREPARE_SIGNER_UNBOUND');key = pub['peers'][role_hint]['publicKey']
            else: raise Refused('UNREVIEWED_SIGNED_SCHEMA')
            body = verified(value, key, schema)
            if 'grantId' in body: need(body['grantId'] == pub['grant']['body']['id'], 'SIGNED_GRANT_DRIFT')
        for key, item in value.items():
            _verify_embedded(item, pub, key if key in ('app','bridge','native') else role_hint)

def _crown_wire(wire,pub):
    """Old archived call proof, verified as history, never freshly authorized."""
    need(set(wire) == {'schema','key_id','payload_b64','signature_b64'} and type(wire['schema']) is int and wire['schema'] == 1,'CROWN_PROOF_INVALID')
    try:
        der=_b64(pub['peers']['app']['publicKey']);key=serialization.load_der_public_key(der)
        need(isinstance(key,Ed25519PublicKey) and wire['key_id'] == bytehash(der),'CROWN_PROOF_INVALID')
        need(isinstance(wire['payload_b64'],str) and isinstance(wire['signature_b64'],str),'CROWN_PROOF_INVALID')
        payload=base64.b64decode(wire['payload_b64'],validate=True);sig=base64.b64decode(wire['signature_b64'],validate=True)
        need(base64.b64encode(payload).decode() == wire['payload_b64'] and base64.b64encode(sig).decode() == wire['signature_b64'] and len(sig) == 64 and len(payload)<=MAX_FILE,'CROWN_PROOF_INVALID')
        key.verify(sig,payload);body=parse(payload)
        need(raw_equal_canonical(payload,body) and body.get('audience') == 'r16-crown-isolated-session-v1' and isinstance(body.get('request_id'),str) and type(body.get('issued_at')) is int and type(body.get('expires_at')) is int and 0<body['expires_at']-body['issued_at']<=60000,'CROWN_PROOF_INVALID')
        return body
    except Refused: raise
    except Exception: raise Refused('CROWN_PROOF_INVALID') from None

def raw_equal_canonical(raw,value): return raw == canonical(value).encode()

def _validate(checkpoint, target, pub, now, anchor, grant_anchor, pins):
    g, _ = _public(pub, now, anchor, grant_anchor)
    need(checkpoint.get('schema') == 'r16.source-app-durable-checkpoint.v1' and checkpoint.get('completeRegisteredFileSet') is True and checkpoint.get('otherWriterPids') == [], 'INCOMPLETE_CHECKPOINT')
    files = checkpoint['files'];parsed = {name:parse(row['bytes']) for name,row in files.items()}
    host = _wrapper(parsed['host/state.json'], 'r16.app-workspace.v1')
    registered = host.get('projects')
    need(isinstance(registered,list) and len(registered) == len(pins) and sorted(x.get('project',{}).get('id','') for x in registered) == sorted(pins), 'REGISTERED_PROJECT_GRAPH_DRIFT')
    projects = {x['project']['id']:x for x in registered}
    expected_dirs = {'host'} | {'host/project-'+p for p in pins}
    for name, value in parsed.items():
        parent, base = name.rsplit('/',1)
        need(parent in expected_dirs and (base in ('state.json','.lock') or re.fullmatch('archive-[A-Za-z0-9_-]+[.]json',base)), 'STORE_FILE_SCOPE_REFUSED')
        meta=files[name]
        need(meta['regular'] is True and meta['symlink'] is False and meta['uid'] == 1000 and meta['nlink'] == 1 and meta['mode'] == 0o600, 'STORE_FILE_METADATA_REFUSED')
        if base == '.lock':
            need(set(value) == {'schema','pid','start','nonce'} and type(value['schema']) is int and value['schema'] == 1 and type(value['pid']) is int and value['pid']>1 and isinstance(value['start'],str) and re.fullmatch('[1-9][0-9]*',value['start']) and isinstance(value['nonce'],str) and len(value['nonce']) >= 16, 'FOREIGN_STORE_WRITER')
            if (value['pid'],value['start']) != (target['pid'],target['startTicks']):
                proof=checkpoint.get('staleLockProofs',{}).get(name)
                need(type(proof) is dict and set(proof) == {'lockSha256','pid','startTicks','observedStartTicks','bootId'} and proof['lockSha256'] == bytehash(meta['bytes']) and proof['pid'] == value['pid'] and proof['startTicks'] == value['start'] and proof['bootId'] == target['bootId'] and (proof['observedStartTicks'] is None or isinstance(proof['observedStartTicks'],str) and re.fullmatch('[1-9][0-9]*',proof['observedStartTicks'])) and proof['observedStartTicks'] != value['start'],'FOREIGN_STORE_WRITER')
        else:
            _verify_embedded(value, pub)
            if base == 'state.json':
                data=value.get('data',{})
                need(isinstance(data,dict),'STORE_COLLECTION_INVALID')
                for field in ('operations','allocations','controls'):
                    items=data.get(field,[])
                    need(isinstance(items,list) and all(isinstance(item,dict) for item in items),'STORE_COLLECTION_INVALID')
                    if field == 'operations':need(all(item.get('status') in ('KNOWN','UNKNOWN','INFLIGHT') for item in items),'UNREVIEWED_OPERATION_STATUS')
                    elif field == 'allocations':need(all(item.get('status') in ('KNOWN','NOT_EXECUTED','CLOSED','UNKNOWN','INFLIGHT') for item in items),'UNREVIEWED_ALLOCATION_STATUS')
                    else:need(not items,'UNREVIEWED_APP_CONTROL_COLLECTION')
    need(set(n.rsplit('/',1)[0] for n in parsed) == expected_dirs and all(d+'/state.json' in parsed for d in expected_dirs), 'REGISTERED_STORE_MISSING')
    for directory in expected_dirs:
        name=directory+'/.lock'
        if name in parsed:continue
        proof=checkpoint.get('missingLockProofs',{}).get(name)
        need(type(proof) is dict and set(proof) == {'stateSha256','dirDev','dirIno','targetBootId','capturePhase'} and proof['stateSha256'] == bytehash(files[directory+'/state.json']['bytes']) and type(proof['dirDev']) is int and proof['dirDev']>=0 and type(proof['dirIno']) is int and proof['dirIno']>0 and proof['targetBootId'] == target['bootId'] and proof['capturePhase'] in ('FROZEN','EXITED','BASELINE_NOT_DRAIN_PROOF'),'REGISTERED_WRITER_LOCK_UNPROVEN')
    unknown = {};leases = {}
    allowed_unknown = set()
    host_ops = host.get('operations');need(isinstance(host_ops,list), 'STORE_COLLECTION_INVALID')
    for project, pin in pins.items():
        reg = projects[project];p = reg['project']
        need(set(p) == {'id','workspaceId','root'} and p['workspaceId'] == g['workspace']['id'] and isinstance(p['root'],str) and p['root'].startswith(g['workspace']['root']+'/') and reg.get('initialized') is True and reg.get('transition') is None, 'REGISTERED_PROJECT_BINDING_DRIFT')
        participant = _wrapper(parsed['host/project-'+project+'/state.json'], 'r16.participant.v1')
        need(participant.get('role') == 'app' and participant.get('grant') == pub['grant'] and type(participant.get('version')) is int and participant.get('version') == g['version'], 'PARTICIPANT_GRANT_DRIFT')
        active = participant.get('active');need(isinstance(active,dict) and set(active) == {'lease','activation'} and participant.get('pending') is None, 'ORIGINAL_LEASE_PHASE_DRIFT')
        lease = active['lease'];body = verified(lease, pub['issuerPublicKey'], 'r16.lease.v1')
        need(participant.get('closing') in (None,lease) and participant.get('lastGeneration') == pin['generation'], 'ORIGINAL_LEASE_PHASE_DRIFT')
        need(body.get('phase') == 'PREPARED' and body.get('grantId') == g['id'] and body.get('grantVersion') == 1 and body.get('grantHash') == digest(pub['grant']) and body.get('releaseHash') == digest(pub['release']) and body.get('versions') == pub['versions'] and body.get('project') == p and body.get('generation') == pin['generation'] and body.get('previousGeneration') == pin['generation']-1 and body.get('channel') == g['channel'] and isinstance(body.get('actions'),list) and set(body['actions']) <= set(g['actions']) and body.get('expiresAt') == body.get('issuedAt',-1)+3600000 and body.get('renewAt') == body.get('expiresAt',-1)-900000, 'ORIGINAL_LEASE_BINDING_DRIFT')
        activation = verified(active['activation'],pub['issuerPublicKey'],'r16.activation.v1')
        need(activation.get('grantId') == g['id'] and activation.get('grantVersion') == 1 and activation.get('projectId') == project and activation.get('generation') == pin['generation'] and activation.get('leaseHash') == digest(lease) and type(activation.get('activatedAt')) is int and body['issuedAt'] <= activation['activatedAt'] < body['expiresAt'], 'ORIGINAL_ACTIVATION_DRIFT')
        retirement = reg.get('retirement')
        need(retirement is None or retirement == {'lease':lease}, 'ORIGINAL_RETIREMENT_DRIFT')
        ops = [x for x in host_ops if x.get('id') == pin['operationId']]
        need(len(ops) == 1, 'ORIGINAL_OPERATION_MISSING')
        row=ops[0];operation=row.get('operation');o=verified(operation,g['peers']['app']['publicKey'],'r16.operation.v1')
        need(digest(operation) == pin['operationHash'] and row.get('projectId') == project and row.get('status') == 'UNKNOWN' and row.get('resultHash') is None and o.get('id') == pin['operationId'] and o.get('grantId') == g['id'] and o.get('projectId') == project and o.get('generation') == pin['generation'] and o.get('leaseHash') == digest(lease) and o.get('channel') == g['channel'] and o.get('action') in body['actions'], 'ORIGINAL_UNKNOWN_DRIFT')
        matches = [x for x in participant.get('operations',[]) if x.get('id') == pin['operationId']]
        need(len(matches) == 1, 'PARTICIPANT_ORIGINAL_MISSING');record=matches[0]
        need(record.get('hash') == pin['operationHash'] and record.get('projectId') == project and record.get('generation') == pin['generation'] and record.get('status') == 'UNKNOWN' and record.get('resultHash') is None, 'PARTICIPANT_ORIGINAL_DRIFT')
        unknown[project] = {**pin,'status':'UNKNOWN','resultHash':None}
        leases[project] = {'activeLeaseHash':digest(lease),'closingLeaseHash':digest(lease) if participant.get('closing') else None,'pendingLeaseHash':None}
        allowed_unknown.add(id(row));allowed_unknown.add(id(record))
    def unresolved(value):
        if isinstance(value,dict):
            need(value.get('status') != 'INFLIGHT', 'DURABLE_INFLIGHT_PRESENT')
            need(value.get('status') != 'UNKNOWN' or id(value) in allowed_unknown, 'ADDITIONAL_DURABLE_UNKNOWN')
            for item in value.values(): unresolved(item)
        elif isinstance(value,list):
            for item in value: unresolved(item)
    for value in parsed.values(): unresolved(value)
    binding = digest({'originalUnknown':unknown,'leaseBindings':leases})
    manifest = {n:{'sha256':bytehash(r['bytes']),'mode':r['mode'],'bytes':len(r['bytes'])} for n,r in files.items()}
    return {'expectedOriginalUnknown':unknown,'expectedLeaseBindings':leases,'expectedSemanticBindingsDigest':binding,'attestation':{'schema':'r16.r15-app-ledger-attestation.v1','sourcePublicConfigDigest':anchor,'grantHash':grant_anchor,'signatureVerification':True,'originalUnknownCount':2,'registeredProjectCount':2,'fileCount':len(files),'totalBytes':sum(len(x['bytes']) for x in files.values()),'checkpointManifestDigest':digest(manifest),'semanticBindingsDigest':binding,'otherDurableInflight':0,'foreignOpenWriters':0,'staleLockProofs':checkpoint.get('staleLockProofs',{}),'missingLockProofs':checkpoint.get('missingLockProofs',{}),'drainStatus':'UNPROVEN'}}

def validate_checkpoint(checkpoint, target, public_config, now_ms):
    """Production fixed policy. Returns only bindings and bounded attestation."""
    try: return _validate(checkpoint,target,public_config,now_ms,PUBLIC_DIGEST,GRANT_DIGEST,PINS)
    except Refused: raise
    except Exception: raise Refused('LEDGER_STRUCTURE_REFUSED') from None

def validate_cloud_authority(pub,control,cutover,accepted):
    """Mirror the existing R6 source publication bindings, without opening store."""
    data=_wrapper(accepted,'r16.cloud-publication.v1')
    delivery=data.get('accepted');body=verified(delivery,pub['issuerPublicKey'],'r16.configuration-delivery.v1')
    expected={'grantId':'r16-projects-daily','grantVersion':1,'status':'ACTIVE','connectRequested':True}
    need(digest(delivery) == DELIVERY_DIGEST and type(body.get('revision')) is int and body.get('revision') == 16 and body.get('publicConfig') == pub and canonical(body.get('control')) == canonical(control) == canonical(expected),'SOURCE_AUTHORITY_DELIVERY_DRIFT')
    need(cutover.get('schema') == 'r16.cloud-cutover.v1' and cutover.get('phase') == 'ACTIVE' and cutover.get('grantId') == 'r16-projects-daily' and cutover.get('releaseId') == 'r16-daily-20261012-r15','SOURCE_CUTOVER_DRIFT')
    return {'oldGrantActive':True,'sourceDeliveryRevision':16,'sourceDeliveryHash':digest(delivery),'connectRequested':True}

def _identity(st): return (st.st_dev,st.st_ino,st.st_mode,st.st_uid,st.st_gid,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns)

def _read_at(parent, name, *, uid, mode, max_bytes=MAX_FILE):
    fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
    try:
        before=os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_uid == uid and before.st_nlink == 1 and stat.S_IMODE(before.st_mode) == mode and 0 < before.st_size <= max_bytes,'READ_METADATA_REFUSED')
        chunks=[];count=0
        while True:
            raw=os.read(fd,min(65536,max_bytes+1-count))
            if not raw: break
            count+=len(raw);need(count<=max_bytes,'READ_CAPACITY_REFUSED');chunks.append(raw)
        need(count == before.st_size and _identity(os.fstat(fd)) == _identity(before) and _identity(os.stat(name,dir_fd=parent,follow_symlinks=False)) == _identity(before),'READ_CHANGED')
        return b''.join(chunks),before
    finally: os.close(fd)

def _open_directory(path, *, leaf_uid=None, leaf_mode=None):
    need(path.is_absolute(),'FIXED_PATH_REQUIRED');fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        for component in path.parts[1:]:
            nextfd=os.open(component,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
            os.close(fd);fd=nextfd;st=os.fstat(fd)
            need(st.st_uid in (0,1000) and not (st.st_mode & 0o7022),'DIRECTORY_METADATA_REFUSED')
        st=os.fstat(fd)
        if leaf_uid is not None: need(st.st_uid == leaf_uid and stat.S_IMODE(st.st_mode) == leaf_mode,'STORE_DIRECTORY_REFUSED')
        return fd
    except BaseException:
        os.close(fd);raise

def read_public(path):
    fd=_open_directory(path.parent)
    try: return parse(_read_at(fd,path.name,uid=0,mode=0o644)[0])
    finally: os.close(fd)

def read_accepted():
    fd=_open_directory(ACCEPTED.parent,leaf_uid=0,leaf_mode=0o700)
    try:return parse(_read_at(fd,ACCEPTED.name,uid=0,mode=0o600)[0])
    finally:os.close(fd)

def read_registration():
    """Existing root-sealed registration only; never initializes or rewrites it."""
    try:
        fd=_open_directory(REGISTRY_DIRECTORY,leaf_uid=0,leaf_mode=0o700)
        try:raw,_=_read_at(fd,REGISTRY_FILE.name,uid=0,mode=0o600,max_bytes=32767)
        finally:os.close(fd)
    except FileNotFoundError:raise Refused('SEALED_REGISTRATION_MISSING') from None
    return parse(raw),bytehash(raw)

def registration_bindings(record):
    """Root record names all three roles; only App store contents are read."""
    need(type(record) is dict and set(record)=={'schema','grantId','phase','specs','identities'} and record['schema']=='r16.cloud-ledger-registration.v1' and record['grantId']=='r16-projects-daily' and record['phase']=='SEALED','SEALED_REGISTRATION_SCOPE_DRIFT')
    need(canonical(record['specs'])==canonical(REGISTRY_SPECS),'SEALED_REGISTRATION_SPECS_DRIFT')
    identities=record['identities']
    need(isinstance(identities,list) and len(identities)==3,'SEALED_REGISTRATION_IDENTITIES_DRIFT')
    bindings={}
    for row in identities:
        need(type(row) is dict and set(row)=={'role','dev','ino'} and row['role'] in ('app','bridge','gateway') and row['role'] not in bindings and type(row['dev']) is int and 0<=row['dev']<=9007199254740991 and type(row['ino']) is int and 0<row['ino']<=9007199254740991,'SEALED_REGISTRATION_IDENTITIES_DRIFT')
        bindings[row['role']]=(row['dev'],row['ino'])
    need(set(bindings)=={'app','bridge','gateway'} and len(set(bindings.values()))==3,'SEALED_REGISTRATION_IDENTITIES_DRIFT')
    return bindings

def read_store_tree(root=STORE, *, expected_root_identity=None):
    """Complete descriptor-relative bounded enumeration; never follows links."""
    files={};identities={};dirs={};total=0
    def walk(fd,relative):
        nonlocal total
        before=os.fstat(fd);need(before.st_uid == 1000 and stat.S_IMODE(before.st_mode) == 0o700,'STORE_DIRECTORY_REFUSED')
        dirs[relative]=(before.st_dev,before.st_ino)
        names=sorted(os.listdir(fd));need(len(names)<=MAX_FILES,'STORE_CAPACITY_REFUSED')
        for name in names:
            need(not name.startswith(('.next','.reclaim')),'TEMPORARY_STORE_FILE_PRESENT')
            st=os.stat(name,dir_fd=fd,follow_symlinks=False);rel=relative+'/'+name
            if stat.S_ISDIR(st.st_mode):
                need(relative == 'host' and name in {'project-'+p for p in PINS},'UNREGISTERED_STORE_DIRECTORY')
                child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
                try: need(_identity(os.fstat(child)) == _identity(st),'STORE_DIRECTORY_CHANGED');walk(child,rel)
                finally: os.close(child)
            else:
                need(name in ('state.json','.lock') or re.fullmatch('archive-[A-Za-z0-9_-]+[.]json',name),'UNREVIEWED_STORE_FILE')
                raw,st=_read_at(fd,name,uid=1000,mode=0o600)
                total+=len(raw);need(total<=MAX_BYTES and len(files)<MAX_FILES,'STORE_CAPACITY_REFUSED')
                files[rel]={'bytes':raw,'regular':True,'symlink':False,'uid':st.st_uid,'nlink':st.st_nlink,'mode':stat.S_IMODE(st.st_mode)}
                identities[rel]=(st.st_dev,st.st_ino)
        need(names == sorted(os.listdir(fd)) and _identity(os.fstat(fd)) == _identity(before),'STORE_DIRECTORY_CHANGED')
    fd=_open_directory(root,leaf_uid=1000,leaf_mode=0o700)
    try:
        if expected_root_identity is not None:
            st=os.fstat(fd);need((st.st_dev,st.st_ino)==expected_root_identity,'SEALED_APP_DIRECTORY_IDENTITY_DRIFT')
        walk(fd,'host')
    finally: os.close(fd)
    return files,identities,dirs

def _start(pid):
    raw=Path('/proc/'+str(pid)+'/stat').read_text()
    return raw[raw.rfind(')')+2:].split()[19]

def _stale_lock_proofs(files,target):
    result={}
    for name,row in files.items():
        if not name.endswith('/.lock'):continue
        lock=parse(row['bytes'])
        need(type(lock.get('pid')) is int and lock['pid']>1 and isinstance(lock.get('start'),str),'FOREIGN_STORE_WRITER')
        if (lock['pid'],lock['start']) == (target['pid'],target['startTicks']):continue
        try:observed=_start(lock['pid'])
        except FileNotFoundError:observed=None
        need(observed != lock['start'],'FOREIGN_STORE_WRITER')
        result[name]={'lockSha256':bytehash(row['bytes']),'pid':lock['pid'],'startTicks':lock['start'],'observedStartTicks':observed,'bootId':target['bootId']}
    return result

def _missing_lock_proofs(files,dirs,target,phase):
    result={}
    for directory,(dev,ino) in dirs.items():
        if directory+'/.lock' in files:continue
        need(directory+'/state.json' in files,'REGISTERED_STORE_MISSING')
        result[directory+'/.lock']={'stateSha256':bytehash(files[directory+'/state.json']['bytes']),'dirDev':dev,'dirIno':ino,'targetBootId':target['bootId'],'capturePhase':phase}
    return result

def _scan_writers(identities,dirs,target_pid, *, proc=Path('/proc'), store_root=STORE):
    """Reject writable FDs/maps and foreign store directory capabilities.

    No environment, command lines, FD contents, keys or database are read.
    Vanished processes are harmless; inaccessible live processes fail closed.
    """
    inode_set=set(identities.values());dir_set=set(dirs.values());selfpid=os.getpid()
    for entry in proc.iterdir():
        if not entry.name.isdecimal(): continue
        pid=int(entry.name)
        if pid in (target_pid,selfpid): continue
        try:
            before=(entry/'stat').read_text();before=before[before.rfind(')')+2:].split()[19]
            for item in (entry/'fd').iterdir():
                try:
                    st=item.stat();identity=(st.st_dev,st.st_ino)
                    link=os.readlink(item)
                    in_tree=link == str(store_root) or link.startswith(str(store_root)+'/')
                    if identity in dir_set or (in_tree and stat.S_ISDIR(st.st_mode)): raise Refused('FOREIGN_STORE_DIRECTORY_FD')
                    if identity in inode_set or in_tree:
                        info=(entry/'fdinfo'/item.name).read_text()
                        flags=re.search(r'^flags:\s*([0-7]+)$',info,re.M)
                        need(flags is not None,'FD_ACCESS_UNPROVEN')
                        need((int(flags.group(1),8)&os.O_ACCMODE) == os.O_RDONLY,'FOREIGN_WRITABLE_FD')
                except FileNotFoundError: continue
            for line in (entry/'maps').read_text().splitlines():
                parts=line.split(None,5);need(len(parts)>=5,'MAP_ACCESS_UNPROVEN')
                if len(parts[1])>=4 and parts[1][1]=='w' and parts[1][3]=='s':
                    dev=parts[3].split(':');identity=(os.makedev(int(dev[0],16),int(dev[1],16)),int(parts[4]))
                    in_tree=len(parts)==6 and (parts[5] == str(store_root) or parts[5].startswith(str(store_root)+'/'))
                    need(identity not in inode_set and not in_tree,'FOREIGN_WRITABLE_SHARED_MAPPING')
            after=(entry/'stat').read_text();after=after[after.rfind(')')+2:].split()[19]
            need(before == after,'PROCESS_SCAN_CHANGED')
        except FileNotFoundError: continue
        except Refused: raise
        except (PermissionError,OSError,ValueError,IndexError): raise Refused('FOREIGN_WRITER_SCAN_UNPROVEN') from None

def _target_state(target,baseline):
    need(target.get('host') == HOST and target.get('unit') == UNIT and target.get('cgroup') == CGROUP and type(target.get('pid')) is int and target['pid']>1 and isinstance(target.get('startTicks'),str),'TARGET_BINDING_REFUSED')
    need(Path('/proc/sys/kernel/random/boot_id').read_text().strip() == target.get('bootId'),'BOOT_ID_DRIFT')
    cgroup=Path('/sys/fs/cgroup'+CGROUP)
    try: start=_start(target['pid'])
    except FileNotFoundError: start=None
    try:
        members=[int(x) for x in (cgroup/'cgroup.procs').read_text().split()]
        events=dict(line.split() for line in (cgroup/'cgroup.events').read_text().splitlines())
    except FileNotFoundError:
        need(not baseline and start is None and not cgroup.exists(),'CGROUP_OBSERVATION_UNPROVEN')
        return 'EXITED'
    if start is None:
        need(not baseline and members == [],'TARGET_EXIT_UNPROVEN');return 'EXITED'
    need(start == target['startTicks'] and members == [target['pid']],'TARGET_IDENTITY_DRIFT')
    need(Path('/proc/'+str(target['pid'])+'/cgroup').read_text().strip() == '0::'+CGROUP,'TARGET_CGROUP_DRIFT')
    if baseline: return 'BASELINE_NOT_DRAIN_PROOF'
    need(events.get('frozen') == '1','KERNEL_FREEZE_UNPROVEN');return 'FROZEN'

class LedgerCheckpoint:
    """No path or trust-policy arguments: only fixed production public/state paths."""
    def capture_baseline(self,target): return self._capture(target,True)
    def capture(self,target): return self._capture(target,False)
    def _capture(self,target,baseline):
        need(os.geteuid() == 0 and platform.node() == HOST,'FIXED_ROOT_CLOUD_REQUIRED')
        try:
            phase=_target_state(target,baseline)
            pub=read_public(PUBLIC);selector=read_public(SELECTOR);manifest=read_public(SOURCE/'app-manifest.json')
            need(selector.get('schema') == 'r16.app-host.v1' and selector.get('publicConfiguration') == str(PUBLIC) and selector.get('codeManifest') == str(SOURCE/'app-manifest.json'),'SOURCE_APP_SELECTOR_DRIFT')
            need(manifest.get('role') == 'app' and digest(manifest) == APP_VERSION and pub['versions']['app'] == APP_VERSION,'SOURCE_APP_MANIFEST_DRIFT')
            control=read_public(CONTROL);cutover=read_public(CUTOVER);accepted=read_accepted()
            authority=validate_cloud_authority(pub,control,cutover,accepted)
            registration,registration_hash=read_registration();registered=registration_bindings(registration)
            one,ids,dirs=read_store_tree(expected_root_identity=registered['app'])
            need(dirs.get('host')==registered['app'],'SEALED_APP_DIRECTORY_IDENTITY_DRIFT')
            _scan_writers(ids,dirs,target['pid'])
            two,ids2,dirs2=read_store_tree(expected_root_identity=registered['app'])
            need(one == two and ids == ids2 and dirs == dirs2,'CHECKPOINT_CHANGED')
            need(dirs2.get('host')==registered['app'],'SEALED_APP_DIRECTORY_IDENTITY_DRIFT')
            _scan_writers(ids2,dirs2,target['pid']);need(_target_state(target,baseline) == phase,'TARGET_STATE_CHANGED')
            need(read_public(PUBLIC) == pub and read_public(SELECTOR) == selector and read_public(SOURCE/'app-manifest.json') == manifest,'PUBLIC_CONFIGURATION_CHANGED')
            need(read_public(CONTROL) == control and read_public(CUTOVER) == cutover and read_accepted() == accepted,'AUTHORITY_CONFIGURATION_CHANGED')
            after_registration,after_registration_hash=read_registration()
            need(after_registration_hash==registration_hash and canonical(after_registration)==canonical(registration) and registration_bindings(after_registration)==registered,'SEALED_REGISTRATION_CHANGED')
            checkpoint={'schema':'r16.source-app-durable-checkpoint.v1','completeRegisteredFileSet':True,'otherWriterPids':[],'files':two,'staleLockProofs':_stale_lock_proofs(two,target),'missingLockProofs':_missing_lock_proofs(two,dirs2,target,phase)}
            result=validate_checkpoint(checkpoint,target,pub,int(time.time()*1000))
            checkpoint.update(result);checkpoint['attestation']['capturePhase']=phase
            checkpoint['attestation'].update(authority)
            checkpoint['attestation'].update(sealedRegistrationVerified=True,registrationHash=registration_hash)
            return checkpoint
        except Refused: raise
        except Exception: raise Refused('PROTECTED_READ_UNPROVEN') from None

if __name__ == '__main__':
    print(json.dumps({'status':'LIBRARY_ONLY_NATIVE_ADMISSION_REQUIRED','rawStateExported':False}))
    raise SystemExit(78)
