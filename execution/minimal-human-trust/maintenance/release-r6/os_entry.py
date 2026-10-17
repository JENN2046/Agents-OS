#!/usr/bin/python3
"""Fixed dual-host maintenance entry. Source candidate; never installed by tests.

Only a human's exact native-admin bootstrap installs the frozen capsule. The
cloud bootstrap is a separate real cloud administrator action, never an assumed
extension of the existing configuration receiver's sudo authority.
"""
import base64
import dataclasses
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import socket
import stat
import subprocess
import sys
import time

ROOT = Path('/usr/lib/r16-maintenance/recovery-r6')
STATE = Path('/var/lib/r16-maintenance/recovery-r6')
SOURCE = Path('/home/jenn/AGENTS_OS_Workspace/ops/g1d-native-recovery-reconnect-20261014-r1/r15-backport/maintenance-app-recovery-r6')
CLOUD_SOURCE = Path('/home/ubuntu/r16-maintenance-app-recovery-r6-candidate')
CLOUD_NODE = '/opt/r16/runtime/node-v24.15.0/bin/node'
FREEZE = Path('/etc/r16-maintenance/recovery-r6-source-freeze.json')
LOCAL = 'jenn-System-Product-Name'
CLOUD = 'VM-0-12-ubuntu'
UNIT = 'r16-native-recovery-maintenance-r6.service'
UNIT_FILE = Path('/etc/systemd/system')/UNIT
HELPER = Path('/usr/libexec/r16-maintenance-os-r6')
SUDOERS = Path('/etc/sudoers.d/r16-maintenance-os-r6')
Q_SHA = '279193bdc2457444d455bf35d48e9bf3f98d0483efddac6138fd40dccf417f74'
SCOPE = 'STOP_FIXED_ROLES_PRESERVE_ALL_LEDGERS'
MAX_JSON = 1048576
CAPSULE_LIMIT = 16*MAX_JSON
ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'SYSTEMD_PAGER': 'cat', 'SYSTEMD_COLORS': '0'}


class Refused(Exception):
    def __init__(self, code): self.code = code;super().__init__(code)


def need(value, code):
    if not value: raise Refused(code)


def canonical(value):
    # Node's canonical key ordering is UTF-16, including non-BMP keys.
    def ordered(x):
        if isinstance(x, dict): return {k: ordered(x[k]) for k in sorted(x, key=lambda s: s.encode('utf-16-be', 'surrogatepass'))}
        if isinstance(x, (list,tuple)): return [ordered(v) for v in x]
        need(x is None or type(x) in (str, int, bool), 'CANONICAL_TYPE_REFUSED')
        if type(x) is int: need(abs(x) <= 9007199254740991, 'CANONICAL_INTEGER_REFUSED')
        return x
    return json.dumps(ordered(value), ensure_ascii=False, separators=(',', ':')).encode()


def digest(value): return hashlib.sha256(canonical(value)).hexdigest()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def ishash(value): return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None
def now_ms(): return int(time.time() * 1000)


def root(host=None):
    need(os.getuid() == 0 and os.geteuid() == 0, 'ROOT_REQUIRED')
    need(socket.gethostname() in ((host,) if host else (LOCAL, CLOUD)), 'HOST_REFUSED')


def candidate_source():
    return CLOUD_SOURCE if socket.gethostname()==CLOUD else SOURCE


def secure_read(path, max_bytes=MAX_JSON, source=False):
    path = Path(path);cursor = Path('/')
    for part in path.parts[1:-1]:
        cursor /= part;s = cursor.lstat()
        need(stat.S_ISDIR(s.st_mode) and s.st_uid in ((0, 1000) if source else (0,)) and not s.st_mode & 0o022, 'PATH_REFUSED')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_uid in ((0, 1000) if source else (0,)) and before.st_nlink == 1 and not before.st_mode & 0o022 and before.st_size <= max_bytes, 'FILE_REFUSED')
        raw = os.read(fd, max_bytes + 1);after = os.fstat(fd)
        fields = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        need(len(raw) == before.st_size and fields(before) == fields(after), 'FILE_DRIFT')
        return raw
    finally: os.close(fd)


def mkdir(path):
    cursor = Path('/')
    for part in Path(path).parts[1:]:
        cursor /= part
        try: cursor.mkdir(mode=0o700)
        except FileExistsError: pass
        s = cursor.lstat()
        need(stat.S_ISDIR(s.st_mode) and s.st_uid == 0 and not s.st_mode & 0o022, 'ROOT_DIRECTORY_REFUSED')


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)


def atomic(path, raw, mode=0o600, exclusive=False):
    path = Path(path);mkdir(path.parent)
    temp = path.parent / ('.' + path.name + '.pending')
    try:
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    except FileExistsError:
        need(secure_read(temp,max_bytes=max(MAX_JSON,len(raw)))==raw,'PENDING_BYTES_CONFLICT');fd=None
    if fd is not None:
        try:
            os.fchmod(fd,mode)
            offset = 0
            while offset < len(raw): offset += os.write(fd, raw[offset:])
            os.fsync(fd)
        finally: os.close(fd)
    if exclusive:
        os.link(temp, path, follow_symlinks=False);os.unlink(temp)
    else: os.replace(temp, path)
    sync_dir(path.parent)


def read_json(path, max_bytes=MAX_JSON): return json.loads(secure_read(path, max_bytes=max_bytes))


def ensure_file(path, raw, mode=0o600):
    """Complete only this capsule's exact immutable file, never replace foreign."""
    path=Path(path);temp=path.parent/('.'+path.name+'.pending')
    if path.exists():
        # link-before-unlink interruption in atomic(exclusive=True).
        if temp.exists():
            a=path.lstat();b=temp.lstat()
            if a.st_ino==b.st_ino and a.st_dev==b.st_dev:
                need(stat.S_ISREG(a.st_mode) and a.st_uid==os.geteuid() and a.st_nlink==2 and (a.st_mode&0o7777)==mode,'OWNED_PENDING_LINK_REFUSED')
                fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
                try: need(os.read(fd,len(raw)+1)==raw,'FOREIGN_INSTALLED_BYTES')
                finally: os.close(fd)
                os.unlink(temp);sync_dir(path.parent)
        need(secure_read(path,max_bytes=max(MAX_JSON,len(raw)))==raw and path.lstat().st_mode&0o7777==mode,'FOREIGN_INSTALLED_BYTES')
        if temp.exists(): need(secure_read(temp,max_bytes=max(MAX_JSON,len(raw)))==raw,'PENDING_BYTES_CONFLICT')
        return
    if temp.exists():
        mkdir(path.parent)
        fd=os.open(temp,os.O_RDWR|os.O_NOFOLLOW)
        try:
            st=os.fstat(fd)
            need(stat.S_ISREG(st.st_mode) and st.st_uid==os.geteuid() and st.st_nlink==1 and st.st_mode&0o7777==mode and st.st_size<=len(raw),'OWNED_PENDING_FILE_REFUSED')
            prefix=os.read(fd,len(raw)+1)
            need(raw.startswith(prefix),'PENDING_BYTES_CONFLICT')
            current=temp.lstat();need((current.st_dev,current.st_ino)==(st.st_dev,st.st_ino),'OWNED_PENDING_FILE_REFUSED')
            offset=len(prefix)
            while offset<len(raw): offset+=os.write(fd,raw[offset:])
            os.fsync(fd)
        finally: os.close(fd)
    atomic(path,raw,mode,exclusive=True)


def recover_json(path,max_bytes=MAX_JSON):
    path=Path(path);temp=path.parent/('.'+path.name+'.pending')
    if temp.exists():
        if path.exists() and path.lstat().st_ino==temp.lstat().st_ino and path.lstat().st_dev==temp.lstat().st_dev:
            # Complete an exclusive write without ever adopting a second inode.
            st=path.lstat();need(st.st_nlink==2 and st.st_uid==os.geteuid() and stat.S_ISREG(st.st_mode),'OWNED_PENDING_LINK_REFUSED')
            os.unlink(temp);sync_dir(path.parent)
        else:
            value=read_json(temp,max_bytes);need(isinstance(value,dict),'PENDING_JSON_UNCONFIRMED')
            os.replace(temp,path);sync_dir(path.parent)
    return read_json(path,max_bytes)


def command(argv, data=b'', timeout=30):
    root()
    result = subprocess.run(tuple(map(str, argv)), input=data, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=ENV, timeout=timeout, check=False)
    need(len(result.stdout) <= MAX_JSON, 'FIXED_COMMAND_OUTPUT_TOO_LARGE')
    if result.returncode != 0:
        try: code = json.loads(result.stdout).get('code')
        except (ValueError, AttributeError): code = None
        need(False, code if isinstance(code,str) and re.fullmatch('[A-Z0-9_]{1,80}',code) else 'FIXED_COMMAND_FAILED')
    return result.stdout


def load_q():
    path = ROOT/'quiescence.py'
    raw = secure_read(path)
    need(sha(raw) == Q_SHA, 'QUIESCENCE_SOURCE_DRIFT')
    spec = importlib.util.spec_from_loader('r3_fixed_quiescence', loader=None)
    module = importlib.util.module_from_spec(spec);sys.modules[spec.name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def snapshot(q, data):
    data = dict(data);data['members'] = tuple(data['members']);data['code_hashes'] = tuple(tuple(x) for x in data['code_hashes'])
    return q.Snapshot(**data)


def plan_hash(plan): return digest(plan)


def validate_plan(plan, template, capsule, allow_recovery=False, current=None, historical=False):
    current = now_ms() if current is None else current
    dynamic = {'approvedAt', 'expiresAt', 'rollbackDeadline', 'capsuleHash', 'sourceFreezeHash', 'nonce'}
    need(isinstance(plan, dict) and set(plan) == set(template) | dynamic, 'PLAN_FIELDS_REFUSED')
    need({k: v for k, v in plan.items() if k not in dynamic} == template, 'PLAN_TEMPLATE_DRIFT')
    need(plan.get('schema') == 'r16.native-recovery-maintenance.plan.v3' and plan.get('osScope') == SCOPE, 'PLAN_SCOPE_REFUSED')
    need(plan['capsuleHash'] == capsule and plan['sourceFreezeHash'] == capsule and ishash(capsule), 'PLAN_CAPSULE_DRIFT')
    need(isinstance(plan['nonce'], str) and re.fullmatch('[0-9a-f]{32}', plan['nonce']), 'PLAN_NONCE_REFUSED')
    a, e, r = (plan[k] for k in ('approvedAt', 'expiresAt', 'rollbackDeadline'))
    need(all(type(x) is int for x in (a, e, r)) and 0 < e-a <= 300000 and e <= r <= a+1800000, 'PLAN_WINDOW_REFUSED')
    if not historical: need(a <= current < (r if allow_recovery else e), 'PLAN_EXPIRED')
    return plan_hash(plan)


def installed_context(allow_recovery=False,historical=False):
    root()
    manifest = read_json(STATE / 'capsule.json',CAPSULE_LIMIT);capsule = read_json(STATE / 'capsule-digest.json')['capsuleHash']
    need(sha(secure_read(STATE / 'capsule.json',CAPSULE_LIMIT)) == capsule and sha(secure_read(ROOT/'SOURCE_FREEZE.json',CAPSULE_LIMIT)) == capsule, 'CAPSULE_DRIFT')
    for rel, pin in manifest['files'].items(): need(sha(secure_read(ROOT / safe_rel(rel))) == pin, 'INSTALLED_SOURCE_DRIFT')
    plan = read_json(STATE / 'plan.json')
    h = validate_plan(plan, manifest['planTemplate'], capsule, allow_recovery,historical=historical)
    return manifest, plan, h


def safe_rel(value):
    need(isinstance(value, str) and value and not value.startswith('/') and all(x not in ('', '.', '..') for x in value.split('/')) and '\\' not in value, 'RELATIVE_PATH_REFUSED')
    return value


def snapshot_json(value): return dataclasses.asdict(value)


class Journal:
    def __init__(self, path): self.path = Path(path);self.value = None
    def read(self):
        temp = self.path.parent / ('.'+self.path.name+'.pending')
        if temp.exists() and self.path.exists():
            before=self.path.lstat();pending=temp.lstat()
            if (before.st_dev,before.st_ino)==(pending.st_dev,pending.st_ino):
                # A new journal's exclusive link may have reached disk before
                # its pending name was removed. Recover only that exact pair.
                need(stat.S_ISREG(before.st_mode) and before.st_uid==0 and before.st_nlink==2 and
                     before.st_mode&0o7777==0o600, 'JOURNAL_PENDING_PAIR_REFUSED')
                fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW)
                try:
                    fields=lambda x:(x.st_dev,x.st_ino,x.st_mode,x.st_uid,x.st_gid,x.st_nlink,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
                    opened=os.fstat(fd);raw=os.read(fd,MAX_JSON+1);after=os.fstat(fd)
                    need(len(raw)==before.st_size<=MAX_JSON and fields(before)==fields(opened)==fields(after)==fields(temp.lstat())==fields(self.path.lstat()), 'JOURNAL_PENDING_PAIR_REFUSED')
                    candidate=json.loads(raw)
                    need(candidate.get('schema')=='r16.os-maintenance-journal.v3' and candidate.get('planHash')==plan_hash(read_json(STATE/'plan.json')) and
                         candidate.get('phase')=='NEW' and candidate.get('cycle')==0 and candidate.get('pending') is None and
                         all(candidate.get(k)==[] for k in ('events','touched','stop_attempts','stopped')) and
                         candidate.get('baseline')==candidate.get('originalBaseline') and
                         set(candidate.get('baseline',{})) in (set(('r16-app.service','r16-bridge.service')),set(load_q().ROLE_HOST)),
                         'JOURNAL_PENDING_PAIR_REFUSED')
                finally:os.close(fd)
                os.unlink(temp);sync_dir(self.path.parent)
        if temp.exists():
            candidate = read_json(temp)
            need(candidate.get('schema') == 'r16.os-maintenance-journal.v3' and ishash(candidate.get('planHash')), 'JOURNAL_PENDING_REFUSED')
            if self.path.exists(): need(read_json(self.path)['planHash'] == candidate['planHash'], 'JOURNAL_PENDING_DRIFT')
            os.replace(temp, self.path);sync_dir(self.path.parent)
        self.value = read_json(self.path);return self.value
    def save(self): atomic(self.path, canonical(self.value))
    def new(self, h, baseline):
        need(not self.path.exists(), 'JOURNAL_ALREADY_EXISTS')
        self.value = {'schema': 'r16.os-maintenance-journal.v3', 'planHash': h, 'phase': 'NEW', 'baseline': baseline,
                      'originalBaseline': baseline, 'cycle': 0, 'touched': [], 'stop_attempts': [], 'stopped': [], 'events': [], 'pending': None}
        atomic(self.path, canonical(self.value), exclusive=True)
    def permit(self, q, plan):
        v = self.value
        p = q._Permit(q._BRAND, v['planHash'], time.monotonic() + max(0, plan['expiresAt']-now_ms())/1000,
                      {u: snapshot(q, row) for u, row in v['baseline'].items()})
        for key in ('touched', 'stop_attempts', 'stopped'): setattr(p, key, list(v[key]))
        p.state = v['phase'];return p
    def capture(self, p):
        self.value.update(phase=p.state, touched=list(p.touched), stop_attempts=list(p.stop_attempts), stopped=list(p.stopped))
    def before(self, operation, unit, p=None):
        need(self.value.get('pending') is None, 'UNRESOLVED_OS_EFFECT')
        if p: self.capture(p)
        event = {'operation': operation, 'unit': unit, 'sequence': len(self.value['events']), 'cycle': self.value['cycle']}
        self.value['pending'] = event;self.value['events'].append({**event, 'state': 'INTENT'})
        need(len(self.value['events']) <= 128, 'JOURNAL_CAPACITY_REFUSED');self.save()
    def after(self):
        event = self.value['pending'];need(event, 'EFFECT_INTENT_MISSING')
        self.value['events'].append({**event, 'state': 'RETURNED'});self.value['pending'] = None;self.save()


def durable_backend(q, journal):
    class Backend(q.RealBackend):
        def effect(self, op, unit, h):
            need(self._admitted is not None and time.monotonic()<self._admitted.expires_at, 'OS_EFFECT_WINDOW_EXPIRED')
            journal.before(op, unit, self._admitted)
            row = self.inspect(unit, h) if op == 'fence' else None
            if row and row.fence_effective: result = None
            else: result = getattr(super(), op)(unit, h)
            journal.after();return result
        def fence(self, u, h): return self.effect('fence', u, h)
        def unfence(self, u, h): return self.effect('unfence', u, h)
        def stop(self, u, h): return self.effect('stop', u, h)
        def start(self, u, h): return self.effect('start', u, h)
    return Backend()


def resolve_pending(q, backend, journal, h):
    event = journal.value.get('pending')
    if not event: return
    unit = event['unit'];q.validate_unit(unit)
    need(event['operation'] in ('fence', 'stop', 'unfence', 'start'), 'JOURNAL_EFFECT_REFUSED')
    row = backend.inspect(unit, h)
    # Never repeat a possibly accepted stop/start. This readback records only
    # observable OS state, not whether the remote command executed or business closed.
    journal.value['events'].append({**event, 'state': 'READBACK_ONLY', 'stopped': row.stopped(), 'active': row.active == 'active', 'fenced': row.fence_effective})
    journal.value['pending'] = None;journal.value['phase'] = 'ABORT_REQUIRED';journal.save()


def os_action(action):
    root(LOCAL);_, plan, h = installed_context(allow_recovery=action in ('resume', 'activate', 'requiesce', 'observe', 'status'))
    q = load_q();journal = Journal(STATE / 'os-journal.json')
    if action=='status':
        backend=q.RealBackend();actors=[]
        for unit in q.ROLE_HOST:
            row=backend.inspect(unit,h)
            original=None
            if unit=='r16-app.service' and journal.path.exists(): journal.read();original=snapshot(q,journal.value['originalBaseline'][unit])
            expected_stopped=bool(original and original.stopped() and row.code_phase=='SOURCE')
            if expected_stopped: need(row.stopped() and not row.fence_hash and not row.daemon_reload_needed and not row.pending_job and row.graceful_only(),'ORIGINAL_APP_STOPPED_BASELINE_NOT_RESTORED')
            else: need(row.active=='active' and row.sub=='running' and row.main_pid>0 and row.main_start>0 and row.main_pid in row.members and not row.fence_hash and not row.daemon_reload_needed and not row.pending_job and row.graceful_only(), 'FIXED_ROLE_NOT_RUNNING')
            actors.append({'unit':unit,'host':row.host,'mainPid':row.main_pid,'mainStartTicks':row.main_start,'codePinsValid':True,'cgroupMembershipValid':True,'ownedFenceAbsent':True,'expectedStopped':expected_stopped})
        return {'status':'ACTUAL_FIXED_ROLES_EXPECTED_STATE' if any(x['expectedStopped'] for x in actors) else 'ACTUAL_FIXED_ROLES_RUNNING','planHash':h,'actors':actors,'businessReadinessClaim':False}
    if action == 'baseline':
        # Persist both cloud roles before any effective-fence fast path can
        # skip an RPC. Cloud samples its own roles under its existing lock.
        cloud = cloud_rpc(q, 'baseline', h)
        need(cloud.get('status')=='CLOUD_BASELINE_SAVED' and cloud.get('planHash')==h and
             set(cloud.get('baseline',{}))=={'r16-app.service','r16-bridge.service'}, 'CLOUD_BASELINE_REFUSED')
        backend = q.RealBackend();rows = q.Controller(backend).baseline(h)
        need(all((unit=='r16-app.service' and row.stopped()) or (row.active=='active' and row.sub=='running' and row.main_pid>0 and row.main_start>0 and row.main_pid in row.members) for unit,row in rows.items()),'SOURCE_ROLES_NOT_RUNNING')
        need(all(row.code_phase in ('SOURCE','STATIC') for row in rows.values()),'BASELINE_REQUIRES_SOURCE_CODE')
        values = {u:snapshot_json(row) for u,row in rows.items()}
        need(all(snapshot(q,cloud['baseline'][u])==rows[u] for u in cloud['baseline']), 'CLOUD_BASELINE_SAMPLE_DRIFT')
        if journal.path.exists():
            journal.read();need(journal.value['planHash']==h,'JOURNAL_PLAN_DRIFT')
            need(canonical(journal.value['originalBaseline'])==canonical(values) and canonical(journal.value['baseline'])==canonical(values), 'BASELINE_READBACK_DRIFT')
        else: journal.new(h, values)
        return {'status':'BASELINE_SAVED','planHash':h,'roles':len(rows)}
    journal.read();need(journal.value['planHash'] == h, 'JOURNAL_PLAN_DRIFT')
    backend = durable_backend(q, journal);controller = q.Controller(backend);p = journal.permit(q, plan)
    if action in ('quiesce','requiesce') and journal.value['phase']=='QUIESCENT':
        actors=controller.observe(p)
        return {'status':'OS_QUIESCENT_FIXED_ROLES_ONLY','planHash':h,'actors':actors,'businessRecordsClosed':False,
                'adapterLedgerMutationPerformed':False,'globalSameEpochBusinessStopClaim':False,'forceTerminationUsed':False,
                'authority':False,'mayInstall':False,'permissionWindowStillCurrent':now_ms()<plan['expiresAt']}
    if action == 'requiesce':
        need(journal.value['cycle'] == 0, 'RECOVERY_CYCLE_ALREADY_USED')
        resolve_pending(q, backend, journal, h)
        need(journal.value['phase'] != 'NEW', 'RECOVERY_CYCLE_NOT_NEEDED')
        cloud_rpc(q, 'begin-cycle', h, {'cycle': 1})
        rows = {u: backend.inspect(u, h) for u in q.ROLE_HOST}
        need(all(row.graceful_only() and row.active in ('active','inactive','failed') and not row.daemon_reload_needed for row in rows.values()), 'RECOVERY_BASELINE_UNSTABLE')
        journal.value.update(cycle=1, baseline={u:snapshot_json(row) for u,row in rows.items()}, phase='NEW', touched=[], stop_attempts=[], stopped=[])
        journal.save();p = journal.permit(q, plan)
        # Same approved rollback window; no extension of the forward signing window.
        p.expires_at = time.monotonic()+max(0,plan['rollbackDeadline']-now_ms())/1000
        action = 'quiesce'
    if action == 'quiesce':
        need(journal.value['phase'] == 'NEW' and journal.value['pending'] is None, 'QUIESCE_ONCE_REQUIRED')
        try:
            result = controller.quiesce(p)
        finally:
            journal.capture(p);journal.save()
        return result
    if action == 'observe':
        need(journal.value['phase'] == 'QUIESCENT' and journal.value['pending'] is None, 'NOT_QUIESCENT')
        return {'status': 'OS_QUIESCENT_FIXED_ROLES_ONLY', 'planHash': h, 'actors': controller.observe(p), 'businessReadinessClaim': False}
    need(action in ('resume', 'activate'), 'OS_ACTION_REFUSED')
    if action == 'activate': need(journal.value['phase'] in ('QUIESCENT', 'ACTIVATING', 'RESTORE_PARTIAL', 'OS_ACTIVE'), 'ACTIVATE_REQUIRES_QUIESCENCE')
    return restore_roles(q, backend, journal, plan, h)


RESTORE_FAILURE_CODES = frozenset((
    'RECOVERY_WINDOW_EXPIRED', 'OWNER_NOT_RUNNING_FOR_NATIVE', 'OWNER_PUBLICATION_NOT_CURRENT',
    'OWNER_PUBLICATION_BINDING_REFUSED', 'TARGET_APP_ACTIVATION_SCOPE_REQUIRED',
    'ORIGINAL_APP_STOPPED_BASELINE_NOT_RESTORED', 'UNKNOWN_START_NOT_REPLAYED',
    'RESTORE_PROCESS_UNCERTAIN', 'RESTORE_READY_TIMEOUT', 'RESTORE_IDENTITY_DRIFT',
    'RESTORE_CODE_DRIFT', 'RESTORE_FOREIGN_FENCE', 'RESTORE_FENCE_REMAINS',
    'UNSAFE_MANAGER_STOP_POLICY', 'FOREIGN_FENCE_REFUSED', 'FENCE_REMOVAL_UNCONFIRMED',
    'CODE_PIN_DRIFT', 'REMOTE_CODE_PHASE_DRIFT', 'ROLE_SELECTOR_DRIFT',
    'ROLE_MANIFEST_VERSION_DRIFT', 'ROLE_MANIFEST_CODE_PIN_DRIFT',
    'UNIT_IDENTITY_REFUSED', 'REMOTE_IDENTITY_REFUSED', 'UNIT_CGROUP_DRIFT',
    'PID_IDENTITY_UNAVAILABLE', 'PID_CGROUP_DRIFT', 'MAIN_PID_OUTSIDE_CGROUP',
    'CONTROL_PID_OUTSIDE_CGROUP', 'PID_REUSED_DURING_INSPECTION',
    'CGROUP_MEMBERSHIP_DRIFT', 'CGROUP_METADATA_UNAVAILABLE',
    'MANAGER_POLICY_DRIFT', 'MANAGER_LIFECYCLE_UNSTABLE', 'PENDING_MANAGER_JOB',
    'OS_EFFECT_WINDOW_EXPIRED', 'START_WHILE_FENCED_OR_JOB_REFUSED',
))


def restore_failure_code(error):
    code = getattr(error, 'code', None)
    return code if type(code) is str and code in RESTORE_FAILURE_CODES else 'RESTORE_BACKEND_REFUSED'


def restore_row_guard(q, row, unit, h, allow_owned_fence=False):
    # inspect() must authenticate each complete snapshot. A refusal is never a
    # readiness sample and must not be hidden by a polling catch/retry loop.
    need(row.unit == unit and row.host == q.ROLE_HOST[unit], 'RESTORE_IDENTITY_DRIFT')
    need(row.graceful_only(), 'UNSAFE_MANAGER_STOP_POLICY')
    need(dict(row.code_hashes) == q.expected_code_pins(unit, row.code_phase), 'RESTORE_CODE_DRIFT')
    if row.fence_hash:
        need(row.fence_hash == q.sha(q.fence_bytes(h)), 'RESTORE_FOREIGN_FENCE')
        need(allow_owned_fence, 'RESTORE_FENCE_REMAINS')


def await_restore_ready(q, backend, unit, h, plan, end, running=False):
    # Pending jobs, activating and NeedDaemonReload are read-only observations:
    # wait for an authenticated stable row; never reload or start to settle it.
    while True:
        need(now_ms() < plan['rollbackDeadline'], 'RECOVERY_WINDOW_EXPIRED')
        row = backend.inspect(unit, h)
        restore_row_guard(q, row, unit, h)
        need(now_ms() < plan['rollbackDeadline'], 'RECOVERY_WINDOW_EXPIRED')
        need(time.monotonic() < end, 'RESTORE_READY_TIMEOUT')
        settled = not row.pending_job and not row.daemon_reload_needed and row.active != 'activating'
        is_running = row.active == 'active' and row.sub == 'running' and row.main_pid > 0 and row.main_start > 0 and row.main_pid in row.members
        if settled:
            if not running:
                need(row.stopped() or is_running, 'RESTORE_PROCESS_UNCERTAIN');return row
            if is_running: return row
        need(row.active in ('active', 'activating', 'inactive', 'failed') or row.pending_job,
             'RESTORE_PROCESS_UNCERTAIN')
        remaining = min(end-time.monotonic(), (plan['rollbackDeadline']-now_ms())/1000)
        need(remaining > 0, 'RESTORE_READY_TIMEOUT')
        time.sleep(min(.05, remaining))


def restore_roles(q, backend, journal, plan, h):
    resolve_pending(q, backend, journal, h)
    journal.value['phase'] = 'ACTIVATING';journal.save()
    p = journal.permit(q, plan);p.state = 'ABORT_RESTORING'
    p.expires_at=time.monotonic()+max(0,plan['rollbackDeadline']-now_ms())/1000
    backend._bind_admitted(p)
    errors, active, failure_codes = [], [], {}
    for unit in q.START_ORDER:
        original = snapshot(q, journal.value['originalBaseline'][unit])
        try:
            need(now_ms()<plan['rollbackDeadline'], 'RECOVERY_WINDOW_EXPIRED')
            if unit=='r16-native.service':
                owner=backend.inspect('r16-owner.service',h)
                need(owner.active=='active' and owner.sub=='running' and owner.main_pid>0,'OWNER_NOT_RUNNING_FOR_NATIVE')
                await_owner_publication(plan)
            row = backend.inspect(unit, h)
            restore_row_guard(q, row, unit, h, allow_owned_fence=True)
            if row.fence_hash: backend.unfence(unit,h)
            # An automatic manager job may become visible when the owned fence
            # is removed. Observe a valid snapshot settling before deciding
            # whether a start is needed; share one bounded budget with its readback.
            ready_end = time.monotonic()+15
            row = await_restore_ready(q, backend, unit, h, plan, ready_end)
            target_app_start=bool(unit=='r16-app.service' and original.stopped() and original.code_phase=='SOURCE' and row.code_phase=='TARGET')
            if target_app_start: need(plan.get('activationScope')=='START_REVIEWED_TARGET_APP_IF_SOURCE_ALREADY_STOPPED','TARGET_APP_ACTIVATION_SCOPE_REQUIRED')
            if original.active != 'active' and not target_app_start:
                need(unit=='r16-app.service' and original.stopped() and original.code_phase=='SOURCE' and row.code_phase=='SOURCE' and
                     row.stopped() and not row.fence_hash and not row.daemon_reload_needed and not row.pending_job and row.graceful_only(),
                     'ORIGINAL_APP_STOPPED_BASELINE_NOT_RESTORED')
                continue
            if row.active != 'active' or row.sub != 'running':
                need(row.stopped(), 'RESTORE_PROCESS_UNCERTAIN')
                prior = [e for e in journal.value['events'] if e['cycle'] == journal.value['cycle'] and e['unit'] == unit and e['operation']=='start' and e['state']=='INTENT']
                need(not prior, 'UNKNOWN_START_NOT_REPLAYED')
                need(now_ms()<plan['rollbackDeadline'], 'RECOVERY_WINDOW_EXPIRED')
                need(time.monotonic()<ready_end, 'RESTORE_READY_TIMEOUT')
                backend.start(unit, h)
                row = await_restore_ready(q, backend, unit, h, plan, ready_end, running=True)
            active.append(unit)
        except Exception as error:
            # Aggregate a partial restoration once, including transport/OS
            # failures. This is not the readiness polling loop: no failed
            # inspection or effect is retried, and exception text is not kept.
            remaining = q.START_ORDER[q.START_ORDER.index(unit):]
            errors.extend(remaining);failure_codes[unit] = restore_failure_code(error)
            for blocked in remaining[1:]: failure_codes[blocked] = 'RESTORE_PREDECESSOR_UNCONFIRMED'
            break
    if now_ms()>=plan['rollbackDeadline']:
        errors.extend(q.START_ORDER)
        for unit in q.START_ORDER: failure_codes.setdefault(unit, 'RECOVERY_WINDOW_EXPIRED')
    journal.value.update(phase='OS_ACTIVE' if not errors else 'RESTORE_PARTIAL', failureCodes=failure_codes);journal.save()
    return {'status': journal.value['phase'], 'activeUnits':active, 'unconfirmedUnits':sorted(set(errors)), 'failureCodes':failure_codes, 'businessReadinessClaim':False, 'planHash':h}


def await_owner_publication(plan):
    deadline=time.monotonic()+15
    while True:
        try:
            wrapper=read_json(Path('/var/lib/r16-owner/configuration/state.json'),32*MAX_JSON)
            proposal=read_json(Path('/etc/r16-owner/release-proposal.json'),32*MAX_JSON)
            published=read_json(Path('/run/r16-owner/public-config.json'),32*MAX_JSON)
            config=wrapper['data'];delivery=config['delivery'];body=delivery['envelope']['body'];public=body['publicConfig']
            need(wrapper.get('schema')==1 and config.get('kind')=='r16.owner.configuration.v1' and body.get('schema')=='r16.configuration-delivery.v1','OWNER_PUBLICATION_BINDING_REFUSED')
            need(delivery['revision']==body['revision'] and digest(public['grant'])==plan['grantHash'],'OWNER_PUBLICATION_BINDING_REFUSED')
            need(public['release']==proposal['release'] and public['versions']==proposal['versions'],'OWNER_PUBLICATION_BINDING_REFUSED')
            if published==public: return
        except (FileNotFoundError,KeyError,TypeError,json.JSONDecodeError): pass
        need(time.monotonic()<deadline and now_ms()<plan['rollbackDeadline'],'OWNER_PUBLICATION_NOT_CURRENT')
        time.sleep(.05)


def cloud_rpc(q, operation, h='', data=None):
    cmd = shlex.join(('/usr/bin/sudo', '-n', str(HELPER), operation, h))
    return json.loads(command((*q.SSH, cmd), canonical(data) if data is not None else b'', timeout=45))


def verify_capsule(expected):
    need(ishash(expected), 'CAPSULE_HASH_REQUIRED')
    source=candidate_source()
    raw = secure_read(source / 'SOURCE_FREEZE.json',CAPSULE_LIMIT,source=True);manifest_raw = raw;manifest = json.loads(raw)
    need(sha(raw) == expected and manifest.get('schema') == 'r16.native-recovery-source-freeze.v3', 'SOURCE_FREEZE_DRIFT')
    need(set(manifest) == {'schema', 'files', 'payloadFiles', 'planTemplate'}, 'SOURCE_FREEZE_FIELDS_REFUSED')
    need(isinstance(manifest['files'], dict) and 4 <= len(manifest['files']) <= 64 and {'os_entry.py', 'quiescence.py', 'run.mjs', 'context.mjs', 'cloud.mjs'} <= set(manifest['files']), 'SOURCE_SET_REFUSED')
    need(isinstance(manifest['payloadFiles'], dict) and 1 <= len(manifest['payloadFiles']) <= 20000, 'PACKAGE_SET_REFUSED')
    need(manifest['files']['quiescence.py'] == Q_SHA, 'QUIESCENCE_SOURCE_DRIFT')
    # Sealed bytes, not a later reread, are copied after hash verification.
    sources = {}
    for rel, pin in manifest['files'].items():
        safe_rel(rel);need(ishash(pin), 'SOURCE_PIN_REFUSED')
        raw = secure_read(source / rel, max_bytes=4*MAX_JSON, source=True);need(sha(raw) == pin, 'SOURCE_BYTE_DRIFT');sources[rel] = raw
    expected_files = set(manifest['payloadFiles'])
    actual = set()
    for directory, subdirs, names in os.walk(source / 'package', followlinks=False):
        need(all(not (Path(directory)/x).is_symlink() for x in subdirs), 'PACKAGE_SYMLINK_REFUSED')
        for name in names: actual.add(str((Path(directory)/name).relative_to(source / 'package')))
    need(actual == expected_files, 'PACKAGE_INVENTORY_DRIFT')
    for rel, pin in manifest['payloadFiles'].items():
        safe_rel(rel);need(rel.startswith(('metadata/', 'payload/')) and ishash(pin), 'PACKAGE_PIN_REFUSED')
    return manifest, sources, manifest_raw


def install_capsule(manifest, sources, capsule, manifest_raw):
    marker=STATE/'bootstrap.json';pending=STATE/'.bootstrap.json.pending'
    if not marker.exists() and not pending.exists():
        need(not STATE.exists() or not any(STATE.iterdir()),'FOREIGN_BOOTSTRAP_STATE')
        need(not ROOT.exists() or not any(ROOT.iterdir()),'FOREIGN_BOOTSTRAP_ROOT')
        mkdir(STATE);mkdir(ROOT)
        ensure_file(marker,canonical({'state':'INTENT','capsuleHash':capsule,'createdAt':now_ms()}))
    record=recover_json(marker)
    need(record.get('capsuleHash')==capsule and type(record.get('createdAt')) is int,'BOOTSTRAP_CAPSULE_DRIFT')
    need(record['createdAt']<=now_ms()<record['createdAt']+1800000,'BOOTSTRAP_WINDOW_EXPIRED')
    mkdir(STATE);mkdir(ROOT)
    for rel, raw in sources.items(): ensure_file(ROOT / rel, raw, 0o644)
    ensure_file(ROOT/'SOURCE_FREEZE.json', manifest_raw, 0o644)
    source=candidate_source()
    inventory_raw = secure_read(source/'package/metadata/PAYLOAD_INVENTORY.json', max_bytes=16*MAX_JSON, source=True)
    need(sha(inventory_raw) == manifest['payloadFiles'].get('metadata/PAYLOAD_INVENTORY.json'), 'INVENTORY_PIN_REQUIRED')
    inventory = json.loads(inventory_raw)
    inventory_rows = inventory if isinstance(inventory, list) else [{'path':k,**v} for k,v in inventory.items()] if isinstance(inventory,dict) else None
    need(isinstance(inventory_rows,list), 'INVENTORY_SHAPE_REFUSED')
    modes = {}
    for row in inventory_rows:
        rel = row.get('path',row.get('artifactPath'));mode = row.get('mode')
        need(isinstance(rel,str) and type(mode) is int and mode & ~0o755 == 0 and not mode & 0o022, 'PAYLOAD_MODE_REFUSED')
        modes['payload/'+safe_rel(rel)] = mode
    for rel, pin in manifest['payloadFiles'].items():
        raw = secure_read(source / 'package' / rel, max_bytes=64*MAX_JSON, source=True)
        need(sha(raw) == pin, 'PACKAGE_BYTE_DRIFT')
        mode = modes.get(rel) if rel.startswith('payload/') else 0o644
        need(mode is not None, 'PAYLOAD_MODE_MISSING');ensure_file(STATE / 'package' / rel, raw, mode)
    ensure_file(STATE / 'capsule.json', manifest_raw)
    ensure_file(STATE / 'capsule-digest.json', canonical({'capsuleHash': capsule}))
    if record['state']=='INTENT': record['state']='COPIED';atomic(marker,canonical(record))
    return record


def checkpoint_bootstrap(record,state,**fields):
    record.update(state=state,**fields);atomic(STATE/'bootstrap.json',canonical(record))


def reconcile_service(h):
    raw=command(('/usr/bin/systemctl','show',UNIT,'--property=Id,ActiveState,SubState,MainPID,ControlPID,InvocationID')).decode()
    props=dict(line.split('=',1) for line in raw.splitlines() if '=' in line)
    need(props.get('Id')==UNIT,'MAINTENANCE_UNIT_IDENTITY_REFUSED')
    return {'status':'MAINTENANCE_START_RECONCILED_READ_ONLY','planHash':h,'active':props.get('ActiveState')=='active','activating':props.get('ActiveState')=='activating','terminalReceiptPresent':(STATE/'transaction-receipt.json').exists(),'startRepeated':False}


TERMINAL_STATUSES=('MAINTENANCE_COMMITTED','ROLLED_BACK_TO_R15_WITH_NEWER_REVISION','ABORTED_BEFORE_CONFIGURATION_CHANGE','ABORTED_BEFORE_SERVICE_CHANGES')


def receipt_projection(h):
    try: receipt=read_json(STATE/'transaction-receipt.json')
    except FileNotFoundError:
        return {'status':'PENDING_NO_TERMINAL_RECEIPT','planHash':h,'terminal':False,'businessAcceptance':False}
    need(isinstance(receipt,dict) and receipt.get('schema')=='r16.maintenance-completion.v3' and receipt.get('status') in TERMINAL_STATUSES,'TERMINAL_RECEIPT_REFUSED')
    projection={'schema':receipt['schema'],'status':receipt['status'],'businessAcceptance':False}
    for name in ('configurationRevision','completedAt'):
        if name in receipt:
            need(type(receipt[name]) is int and 0<=receipt[name]<=9007199254740991,'TERMINAL_RECEIPT_REFUSED');projection[name]=receipt[name]
    for name in ('failureCode','recoveryCode'):
        if name in receipt:
            need(isinstance(receipt[name],str) and re.fullmatch('[A-Z0-9_]{1,80}',receipt[name]),'TERMINAL_RECEIPT_REFUSED');projection[name]=receipt[name]
    return {'status':receipt['status'],'planHash':h,'terminal':True,'receipt':projection,'businessAcceptance':False}


def receipt_status(h):
    result=receipt_projection(h)
    if result['terminal']: return result
    raw=command(('/usr/bin/systemctl','show',UNIT,'--property=Id,ActiveState,SubState,MainPID,ControlPID,ExecMainStatus,Result')).decode()
    props=dict(line.split('=',1) for line in raw.splitlines() if '=' in line)
    need(props.get('Id')==UNIT,'MAINTENANCE_UNIT_IDENTITY_REFUSED')
    active=props.get('ActiveState')
    need(active in ('active','activating','inactive','deactivating','failed'),'MAINTENANCE_UNIT_STATE_REFUSED')
    result['serviceState']=active
    if active=='failed': result['status']='RECOVERY_REQUIRED_NO_TERMINAL_RECEIPT'
    return result


def await_receipt(plan,h,maximum=180):
    need(type(maximum) is int and 0<=maximum<=180,'RECEIPT_WAIT_BOUND_REFUSED')
    deadline=time.monotonic()+min(maximum,max(0,plan['rollbackDeadline']-now_ms())/1000)
    while True:
        result=receipt_status(h)
        if result['terminal'] or result['status']=='RECOVERY_REQUIRED_NO_TERMINAL_RECEIPT': return result
        remaining=deadline-time.monotonic()
        if remaining<=0:
            result['waitBoundReached']=True;return result
        time.sleep(min(.25,remaining))


def historical_receipt():
    root(LOCAL);_,plan,h=installed_context(historical=True)
    result=receipt_status(h);result['readOnly']=True;result['operationAuthorityExtended']=False
    return result


HELPER_BYTES = ('#!/bin/sh\nexec /usr/bin/python3 -I -B ' + str(ROOT / 'os_entry.py') + ' cloud-helper "$@"\n').encode()
SUDOERS_BYTES = ('# Fixed parsed helper; no generic Python, shell or path authority.\nubuntu ALL=(root) NOPASSWD: ' + str(HELPER) + ' *\n').encode()
UNIT_BYTES = ('[Unit]\nDescription=Same-Grant Native recovery maintenance transaction\n[Service]\nType=oneshot\nUser=root\nGroup=root\nExecStartPre=/usr/bin/python3 -I -B ' + str(ROOT / 'os_entry.py') + ' service-admit\nExecStart=/usr/bin/node ' + str(ROOT / 'run.mjs') + '\nLoadCredentialEncrypted=release-signing-key:/etc/credstore.encrypted/r16-release/release-signing-key.cred\nLoadCredentialEncrypted=issuer-signing-key:/etc/credstore.encrypted/r16-issuer/issuer-signing-key.cred\nUMask=0077\nRestart=no\nSendSIGKILL=no\nKillSignal=SIGTERM\nTimeoutStartSec=600\nLimitCORE=0\nNoNewPrivileges=yes\nPrivateTmp=yes\n').encode()


def bootstrap(kind, capsule):
    root(LOCAL if kind == 'bootstrap-local' else CLOUD)
    mkdir(STATE.parent)
    fd=os.open(STATE.parent/'recovery-r6-bootstrap.lock',os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        s=os.fstat(fd);need(stat.S_ISREG(s.st_mode) and s.st_uid==os.geteuid() and s.st_nlink==1 and s.st_mode&0o7777==0o600,'BOOTSTRAP_LOCK_REFUSED')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return bootstrap_locked(kind,capsule)
    finally: os.close(fd)


def bootstrap_locked(kind, capsule):
    root(LOCAL if kind == 'bootstrap-local' else CLOUD)
    manifest, sources, manifest_raw = verify_capsule(capsule);record=install_capsule(manifest, sources, capsule, manifest_raw)
    if kind == 'bootstrap-cloud':
        if (STATE/'admission.json').exists() or (STATE/'.admission.json.pending').exists():
            admission=recover_json(STATE/'admission.json')
            need(admission.get('capsuleHash')==capsule and admission.get('expiresAt')==record['createdAt']+1800000,'CLOUD_BOOTSTRAP_ADMISSION_DRIFT')
        else:
            admission = {'capsuleHash': capsule, 'expiresAt': record['createdAt']+1800000, 'unused': True}
            ensure_file(STATE / 'admission.json', canonical(admission))
        ensure_file(HELPER, HELPER_BYTES, 0o755)
        ensure_file(SUDOERS, SUDOERS_BYTES, 0o440)
        command(('/usr/sbin/visudo', '-cf', str(SUDOERS)))
        ensure_file(FREEZE, canonical({'files': {str(ROOT/rel): pin for rel, pin in manifest['files'].items()}, 'capsuleHash': capsule}))
        checkpoint_bootstrap(record,'CLOUD_READY_FOR_ONCE_ADMIT')
        return {'status': 'CLOUD_BOOTSTRAPPED', 'capsuleHash': capsule, 'expiresAt': admission['expiresAt'], 'productionBusinessChanged': False}
    q = load_q();cloud = cloud_rpc(q, 'admission', capsule)
    need(cloud.get('capsuleHash') == capsule, 'CLOUD_ADMISSION_REFUSED')
    if (STATE/'plan.json').exists() or (STATE/'.plan.json.pending').exists():
        plan=recover_json(STATE/'plan.json');h=validate_plan(plan,manifest['planTemplate'],capsule,allow_recovery=True)
        need(cloud.get('unused') is True or cloud.get('planHash')==h,'CLOUD_ADMISSION_REFUSED')
    else:
        need(cloud.get('unused') is True,'CLOUD_ADMISSION_REFUSED')
        approved = record['createdAt'];deadline = min(approved+1800000, cloud['expiresAt']);expires = min(approved+300000, deadline)
        need(expires-now_ms()>=60000, 'CLOUD_ADMISSION_TOO_SHORT')
        plan = {**manifest['planTemplate'], 'capsuleHash': capsule, 'sourceFreezeHash': capsule,
                'approvedAt': approved, 'expiresAt': expires, 'rollbackDeadline': deadline, 'nonce':secrets.token_hex(16)}
        h = validate_plan(plan, manifest['planTemplate'], capsule)
        ensure_file(STATE/'plan.json', canonical(plan))
    mkdir(FREEZE.parent)
    if not (STATE/'context.json').exists():
        if (STATE/'context.json.next').exists():
            context=read_json(STATE/'context.json.next',32*MAX_JSON)
            need(context.get('planHash')==h,'PENDING_CONTEXT_DRIFT');os.replace(STATE/'context.json.next',STATE/'context.json');sync_dir(STATE)
        else: command(('/usr/bin/node', str(ROOT/'context.mjs')), timeout=120)
    context = read_json(STATE/'context.json',32*MAX_JSON)
    need(context.get('schema')=='r16.native-recovery-context.v3' and context.get('planHash')==h and ishash(context.get('artifactsHash')), 'CONTEXT_ARTIFACTS_REQUIRED')
    expected_freeze={'schema':'r16.maintenance-source-freeze.v3','files':{str(ROOT/rel):pin for rel,pin in manifest['files'].items()},'artifactsHash':context['artifactsHash'],'rollbackDeadline':plan['rollbackDeadline'],'capsuleHash':capsule}
    if FREEZE.with_name(FREEZE.name+'.next').exists():
        need(read_json(FREEZE.with_name(FREEZE.name+'.next'))==expected_freeze,'ROOT_FREEZE_DRIFT')
        os.replace(FREEZE.with_name(FREEZE.name+'.next'),FREEZE);sync_dir(FREEZE.parent)
    ensure_file(FREEZE,canonical(expected_freeze)+b'\n') if not FREEZE.exists() else need(read_json(FREEZE)==expected_freeze,'ROOT_FREEZE_DRIFT')
    checkpoint_bootstrap(record,'CONTEXT_PREPARED',planHash=h)
    admitted = cloud_rpc(q, 'admit', h, plan)
    need(admitted.get('planHash') == h, 'CLOUD_PLAN_ADMISSION_REFUSED')
    ensure_file(UNIT_FILE, UNIT_BYTES, 0o644)
    if record.get('startIntent'):
        reconcile_service(h)
        return await_receipt(plan,h)
    command(('/usr/bin/systemctl', 'daemon-reload'))
    checkpoint_bootstrap(record,'SERVICE_START_INTENT',planHash=h,startIntent=True)
    command(('/usr/bin/systemctl', 'start', '--no-block', UNIT))
    checkpoint_bootstrap(record,'SERVICE_START_SUBMITTED',planHash=h,startSubmitted=True)
    return await_receipt(plan,h)


def cloud_admit(operation, h, data):
    root(CLOUD);admission = recover_json(STATE/'admission.json')
    manifest = read_json(STATE/'capsule.json',CAPSULE_LIMIT);capsule = sha(secure_read(STATE/'capsule.json',CAPSULE_LIMIT))
    need(admission['capsuleHash'] == capsule and now_ms() < admission['expiresAt'], 'CLOUD_ADMISSION_EXPIRED')
    if operation == 'admission':
        need(h == capsule, 'CAPSULE_DRIFT');return admission
    need(operation == 'admit', 'ADMISSION_OPERATION_REFUSED')
    expected = validate_plan(data, manifest['planTemplate'], capsule,allow_recovery=not admission['unused'])
    need(h == expected and data['rollbackDeadline'] <= admission['expiresAt'], 'CLOUD_PLAN_DRIFT')
    if not admission['unused']:
        need(admission.get('planHash')==h,'CLOUD_ONCE_ADMISSION_USED')
        if (STATE/'plan.json').exists() or (STATE/'.plan.json.pending').exists():
            need(recover_json(STATE/'plan.json')==data,'CLOUD_ONCE_ADMISSION_USED')
        else: ensure_file(STATE/'plan.json',canonical(data))
        return {'planHash': h, 'alreadyAdmitted': True}
    # Intent consumes the capability before any plan becomes executable. A
    # crash here may complete only the same digest's missing immutable plan.
    admission['unused'] = False;admission['planHash'] = h
    atomic(STATE/'admission.json', canonical(admission))
    ensure_file(STATE/'plan.json', canonical(data))
    return {'planHash': h, 'alreadyAdmitted': False}


def cloud_helper(args, data):
    root(CLOUD);need(2 <= len(args) <= 3, 'HELPER_ARGUMENTS_REFUSED')
    op = args[0]
    if op in ('admit', 'admission'):
        need(len(args) == 2 and ishash(args[1]), 'HELPER_ARGUMENTS_REFUSED')
        return cloud_admit(op, args[1], data)
    recovery = op in ('unfence', 'start', 'readback')
    _, plan, h = installed_context(allow_recovery=True)
    if op in ('stage', 'commit', 'readback'):
        need(len(args) == 2 and args[1] == h, 'HELPER_PLAN_REFUSED')
        need(op != 'readback' or data is not None, 'PUBLICATION_REQUEST_REQUIRED')
        raw = command((CLOUD_NODE, str(ROOT/'cloud.mjs'), op), canonical(data), timeout=120)
        return json.loads(raw)
    if op == 'baseline':
        need(len(args)==2 and args[1]==h and data is None, 'HELPER_PLAN_REFUSED')
        need(now_ms()<plan['expiresAt'], 'FORWARD_WINDOW_EXPIRED')
        q=load_q();backend=q.RealBackend();rows={}
        for unit in ('r16-app.service','r16-bridge.service'):
            row=backend.inspect(unit,h)
            need(row.graceful_only() and not row.fence_hash and not row.daemon_reload_needed and not row.pending_job and
                 row.code_phase==('SOURCE' if unit=='r16-app.service' else 'STATIC'), 'CLOUD_BASELINE_UNSTABLE')
            need((unit=='r16-app.service' and row.stopped()) or
                 (row.active=='active' and row.sub=='running' and row.main_pid>0 and row.main_start>0 and row.main_pid in row.members), 'SOURCE_ROLES_NOT_RUNNING')
            rows[unit]=snapshot_json(row)
        need(now_ms()<plan['expiresAt'], 'FORWARD_WINDOW_EXPIRED')
        journal=Journal(STATE/'cloud-os-journal.json')
        if journal.path.exists():
            journal.read();need(journal.value['planHash']==h,'JOURNAL_PLAN_DRIFT')
            need(canonical(journal.value['baseline'])==canonical(rows) and canonical(journal.value['originalBaseline'])==canonical(rows), 'CLOUD_BASELINE_READBACK_DRIFT')
        else: journal.new(h,rows)
        return {'status':'CLOUD_BASELINE_SAVED','planHash':h,'baseline':rows}
    if op == 'begin-cycle':
        need(len(args)==2 and args[1]==h and data=={'cycle':1}, 'RECOVERY_CYCLE_REFUSED')
        q = load_q();backend = q.RealBackend();journal = Journal(STATE/'cloud-os-journal.json');journal.read()
        need(journal.value['planHash']==h, 'JOURNAL_PLAN_DRIFT')
        if journal.value['cycle']==1: return {'cycle':1,'alreadyStarted':True,'planHash':h}
        need(journal.value['cycle']==0, 'RECOVERY_CYCLE_ALREADY_USED')
        resolve_pending(q,backend,journal,h)
        journal.value['cycle']=1;journal.value['phase']='RECOVERY_STOPPING';journal.save()
        return {'cycle':1,'alreadyStarted':False,'planHash':h}
    need(op in ('inspect', 'fence', 'unfence', 'stop', 'start') and len(args) == 3 and args[2] == h, 'HELPER_OPERATION_REFUSED')
    unit = args[1];need(unit in ('r16-app.service', 'r16-bridge.service'), 'CLOUD_ROLE_REFUSED')
    q = load_q();backend = q.RealBackend()
    if op == 'inspect': return snapshot_json(backend.inspect(unit, h))
    journal = Journal(STATE/'cloud-os-journal.json')
    need(journal.path.exists(), 'REMOTE_COMPLETE_BASELINE_REQUIRED')
    journal.read()
    need(set(journal.value['originalBaseline'])=={'r16-app.service','r16-bridge.service'} and
         set(journal.value['baseline'])=={'r16-app.service','r16-bridge.service'}, 'REMOTE_COMPLETE_BASELINE_REQUIRED')
    need(journal.value['planHash'] == h, 'JOURNAL_PLAN_DRIFT')
    need(recovery or journal.value['cycle']==1 or now_ms()<plan['expiresAt'], 'FORWARD_WINDOW_EXPIRED')
    if journal.value['pending']:
        # Never retry effects with an unknown reply. Caller must use inspect
        # and a subsequent recovery-only unfence/start, not replay stop/fence.
        need(op in ('unfence', 'start'), 'UNRESOLVED_OS_EFFECT')
        resolve_pending(q, backend, journal, h)
    prior = [x for x in journal.value['events'] if x.get('cycle')==journal.value['cycle'] and x['operation'] == op and x['unit'] == unit and x['state'] == 'INTENT']
    need(not prior, 'REMOTE_EFFECT_ALREADY_ATTEMPTED')
    row = backend.inspect(unit, h)
    if op == 'fence':
        need(not row.fence_hash or row.fence_effective, 'PREEXISTING_FENCE')
        if journal.value['cycle']==0:
            need(snapshot(q,journal.value['baseline'][unit])==row, 'REMOTE_BASELINE_READBACK_DRIFT')
        else: journal.value['baseline'][unit] = snapshot_json(row)
    else:
        need(unit in journal.value['baseline'], 'REMOTE_BASELINE_REQUIRED')
    if op == 'start':
        original = snapshot(q, journal.value['originalBaseline'][unit])
        target_app_start=bool(unit=='r16-app.service' and original.stopped() and original.code_phase=='SOURCE' and row.code_phase=='TARGET' and plan.get('activationScope')=='START_REVIEWED_TARGET_APP_IF_SOURCE_ALREADY_STOPPED')
        need((original.active=='active' or target_app_start) and row.stopped(), 'REMOTE_RESTORE_SCOPE_REFUSED')
        need(target_app_start or any(x['operation'] == 'stop' and x['unit'] == unit and x['state'] == 'INTENT' for x in journal.value['events']), 'REMOTE_STOP_INTENT_REQUIRED')
    deadline = plan['rollbackDeadline'] if recovery or journal.value['cycle']==1 else plan['expiresAt']
    p = q._Permit(q._BRAND, h, time.monotonic()+max(0,deadline-now_ms())/1000, {})
    p.state = 'ABORT_RESTORING' if recovery else ('STOPPING' if op == 'stop' else 'FENCING');backend._bind_admitted(p)
    journal.before(op, unit)
    if not(op=='fence' and row.fence_effective): getattr(backend, op)(unit, h)
    journal.after();return {'status': 'OS_EFFECT_RETURNED', 'operation': op, 'unit': unit, 'planHash': h}


def assert_cloud_quiescent():
    root(CLOUD);_,plan,h=installed_context(allow_recovery=True);q=load_q();backend=q.RealBackend();actors=[]
    for unit in ('r16-app.service','r16-bridge.service'):
        row=backend.inspect(unit,h)
        need(row.stopped() and row.fence_effective and row.graceful_only() and not row.daemon_reload_needed, 'CLOUD_NOT_QUIESCENT')
        actors.append({'unit':unit,'mainPid':0,'controlPid':0,'cgroupEmpty':True,'fenceHash':row.fence_hash})
    return {'status':'CLOUD_OS_QUIESCENT','planHash':h,'actors':actors,'businessReadinessClaim':False}


def service_admit():
    root(LOCAL);_, plan, h = installed_context(allow_recovery=True)
    group = Path('/proc/self/cgroup').read_text()
    need(any(line.split(':', 2)[-1] == '/system.slice/'+UNIT for line in group.splitlines()), 'SERVICE_CGROUP_REQUIRED')
    need(not (STATE/'transaction-receipt.json').exists(), 'TRANSACTION_ALREADY_TERMINAL')
    marker=STATE/'service-attempted.json'
    if marker.exists():
        need(read_json(marker)['planHash']==h, 'SERVICE_TRANSACTION_DRIFT')
        return {'status':'SAME_TRANSACTION_RESUME_ADMITTED','planHash':h,'authorityExtended':False}
    atomic(marker, canonical({'planHash': h, 'at': now_ms()}), exclusive=True)
    return {'status': 'ONCE_TRANSACTION_ADMITTED', 'planHash': h}


def continue_transaction():
    root(LOCAL);_,plan,h=installed_context(allow_recovery=True)
    if (STATE/'transaction-receipt.json').exists():
        result=receipt_projection(h);result['readOnly']=True;return result
    need(secure_read(UNIT_FILE)==UNIT_BYTES,'MAINTENANCE_UNIT_DRIFT')
    if (STATE/'service-attempted.json').exists(): need(read_json(STATE/'service-attempted.json')['planHash']==h,'SERVICE_TRANSACTION_DRIFT')
    need(read_json(STATE/'context.json',32*MAX_JSON)['planHash']==h,'SERVICE_CONTEXT_DRIFT')
    command(('/usr/bin/systemctl','start','--no-block',UNIT))
    return await_receipt(plan,h)


def continue_entry():
    # The unit's ExecStartPre independently acquires entry.lock. Keep that
    # mutator lock free while submitting/waiting; serialize human resume
    # submissions with their own lock instead.
    root(LOCAL);mkdir(STATE)
    fd=os.open(STATE/'continue-submit.lock',os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        st=os.fstat(fd)
        need(stat.S_ISREG(st.st_mode) and st.st_uid==os.geteuid() and st.st_nlink==1 and st.st_mode&0o7777==0o600,'CONTINUE_LOCK_REFUSED')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return continue_transaction()
    finally: os.close(fd)


def execute(args, data=None):
    need(args, 'ARGUMENTS_REQUIRED');root()
    if args[0] in ('bootstrap-local', 'bootstrap-cloud'):
        need(len(args) == 2, 'ARGUMENTS_REFUSED');return bootstrap(args[0], args[1])
    # A cloud commit holds the mutator lock while its Node subprocess asks for
    # an independent live stop proof. Read-only proof must not reacquire that
    # same lock; it performs all actual root/plan/capsule/OS checks itself.
    if args==['assert-cloud-quiescent']: return assert_cloud_quiescent()
    if args==['status']: return os_action('status')
    if args==['receipt']: return historical_receipt()
    if args==['cloud-app-state']:
        root(CLOUD);_,plan,h=installed_context(allow_recovery=True);q=load_q();row=q.RealBackend().inspect('r16-app.service',h)
        return {'status':'ACTUAL_APP_OS_OBSERVATION','codePhase':row.code_phase,'stopped':row.stopped(),'activeState':row.active,'mainPid':row.main_pid,'controlPid':row.control_pid,'cgroupEmpty':not row.members}
    if args==['continue']: return continue_entry()
    mkdir(STATE)
    fd = os.open(STATE/'entry.lock', os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args[0] == 'cloud-helper': return cloud_helper(args[1:], data)
        need(len(args) == 1, 'ARGUMENTS_REFUSED')
        if args[0] == 'service-admit': return service_admit()
        need(args[0] in ('baseline', 'quiesce', 'observe', 'resume', 'activate', 'requiesce', 'status'), 'OPERATION_REFUSED')
        return os_action(args[0])
    finally: os.close(fd)


def main():
    os.umask(0o077)
    try:
        root()
        raw = sys.stdin.buffer.read(MAX_JSON+1) if len(sys.argv)>1 and sys.argv[1]=='cloud-helper' else b''
        need(len(raw) <= MAX_JSON, 'INPUT_CAPACITY_REFUSED')
        result = execute(sys.argv[1:], json.loads(raw) if raw else None)
        output = canonical(result);need(len(output) <= MAX_JSON, 'OUTPUT_CAPACITY_REFUSED')
        print(output.decode())
        if sys.argv[1:2] in (['bootstrap-local'],['continue']) and result.get('terminal') is False: return 75
        return 0
    except Exception as error:
        code = getattr(error, 'code', None)
        if not isinstance(code, str) or re.fullmatch('[A-Z0-9_]{1,80}', code) is None: code = 'FIXED_ENTRY_REFUSED'
        print(json.dumps({'refused': True, 'code': code}));return 78


if __name__ == '__main__': raise SystemExit(main())
