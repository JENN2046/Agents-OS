#!/usr/bin/python3
"""Exclusive protected code placement. No signer, credential reader or service action.
Root effects require a foreground authenticated Host Admin and exact challenge.
This code-only admission does not establish Human identity or caller localness.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import stat
import subprocess
import sys
import time

PUB19 = '56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec'
DELIVERY19 = 'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9'
OPT = '/opt/r16/releases/r16-daily-20261012-r17/'
LIB = '/usr/lib/minimal-human-trust/'
STATE = '/var/lib/minimal-human-trust/code-admission'
FIXED = {
 '/etc/minimal-human-trust/first-trust-code.json',
 '/etc/minimal-human-trust/identity-admission-code.json',
 '/usr/libexec/minimal-human-trust-identity-admission',
 '/etc/minimal-human-trust/stage-installer-reviewed.mjs',
 '/etc/systemd/system/minimal-human-trust-proposal.service',
 '/etc/systemd/system/minimal-human-trust-publisher.service',
 '/etc/systemd/system/minimal-human-trust-approval.socket',
 '/etc/systemd/system/minimal-human-trust-approval@.service',
 '/etc/systemd/system/minimal-human-trust-identity-admission.service',
 '/usr/share/applications/minimal-human-trust-approval.desktop',
 '/usr/share/applications/minimal-human-trust-first-cutover.desktop',
 '/usr/share/polkit-1/actions/org.jenn.r16.minimal-human-trust.policy',
 '/usr/share/polkit-1/actions/org.jenn.r16.minimal-human-trust.identity-admission.policy',
}
USES = ('/run/minimal-human-trust/approval.sock',
        '/run/minimal-human-trust/approval',
        '/var/lib/minimal-human-trust/native-activation-intent.json',
        '/etc/minimal-human-trust/trust-roots.json',
        '/etc/minimal-human-trust/issuer.json',
        '/etc/minimal-human-trust/human-proposal-request.json',
        '/etc/minimal-human-trust/human-pending.json',
        '/etc/credstore.encrypted/minimal-human-trust',
        '/var/lib/minimal-human-trust/identity-admission',
        '/var/lib/minimal-human-trust/human-approval',
        '/var/lib/minimal-human-trust/human-proposals',
        '/var/lib/minimal-human-trust/first-trust-publication')


def need(ok, code):
    if not ok:
        raise ValueError(code)


def canonical(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def digest(v):
    return sha(canonical(v))


def read(path, protected=False):
    path = Path(path)
    for parent in (*reversed(path.parents), path):
        s = parent.lstat()
        need(not stat.S_ISLNK(s.st_mode), 'PATH_LINK_REFUSED')
        if protected:
            need(s.st_uid == 0 and not s.st_mode & 0o022, 'PROTECTED_SOURCE_REFUSED')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
             and before.st_size <= 64 * 1024 * 1024, 'SOURCE_FILE_REFUSED')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(64 * 1024 * 1024 + 1)
        key = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_mode, s.st_uid, s.st_gid, s.st_nlink)
        need(len(raw) == before.st_size and key(before) == key(os.fstat(fd)) == key(path.lstat()), 'SOURCE_CHANGED')
        return raw
    finally:
        os.close(fd)


def target(path):
    need(isinstance(path, str) and Path(path).is_absolute()
         and str(Path(path)) == path and '..' not in Path(path).parts, 'TARGET_PATH_REFUSED')
    need(path in FIXED or path.startswith(OPT) or path.startswith(LIB), 'TARGET_SCOPE_REFUSED')
    need(not any(p in ('secrets', 'credentials', 'tokens', 'cookies', 'state-private', '.git')
                 or p.startswith('.env') for p in Path(path).parts)
         and not path.endswith(('.key', '.pem', '.cred', '.p12', '.pfx', '.log')), 'SENSITIVE_TARGET_REFUSED')
    return path


def prepare(catalog, packet):
    need(catalog.get('schema') == 'r17.source19.protected-code-preparation-review.v1'
         and catalog.get('authority') is False and catalog.get('signable') is False
         and catalog.get('executable') is False, 'CODE_REVIEW_SCHEMA_REQUIRED')
    need(catalog.get('sourceRevision') == 19 and catalog.get('sourcePublicConfigHash') == PUB19
         and catalog.get('sourceDeliveryHash') == DELIVERY19
         and catalog.get('host') == 'jenn-System-Product-Name', 'SOURCE19_REVIEW_REQUIRED')
    rows = catalog.get('targets')
    need(isinstance(rows, list) and 0 < len(rows) <= 20000
         and digest(rows) == catalog.get('contentRoot'), 'COMPLETE_CONTENT_ROOT_REQUIRED')
    seen = set()
    payload = []
    total = 0
    for row in rows:
        need(set(row) == {'source', 'sha256', 'bytes', 'target', 'uid', 'gid', 'mode', 'operation'}, 'TARGET_ROW_SHAPE')
        p = target(row['target'])
        need(p not in seen and row['uid'] == row['gid'] == 0
             and row['mode'] in ('0600', '0644', '0755')
             and row['operation'] == 'EXCLUSIVE_CREATE_IF_ABSENT', 'TARGET_ROW_REFUSED')
        seen.add(p)
        rel = row['source']
        need(isinstance(rel, str) and rel.startswith(('payload/', 'metadata/'))
             and '\\' not in rel and all(p not in ('', '.', '..', 'secrets', 'credentials', 'tokens', 'cookies', 'state-private', '.git') and not p.startswith('.env') for p in rel.split('/'))
             and not any(ord(c) < 32 or ord(c) == 127 for c in rel)
             and not rel.endswith(('.key', '.pem', '.cred', '.p12', '.pfx', '.log')), 'PACKET_SOURCE_SCOPE')
        raw = read(packet / rel)
        need(sha(raw) == row['sha256'] and len(raw) == row['bytes'], 'PACKET_BYTES_DRIFT')
        total += len(raw)
        need(total <= 512 * 1024 * 1024, 'PACKET_SIZE_REFUSED')
        payload.append((row, raw))
    return payload


class FileBackend:
    """Production has no path override. Tests use a private /tmp root as uid!=0."""
    def __init__(self, fixture=None):
        self.fixture = fixture
        if fixture is not None:
            p = Path(fixture)
            need(os.geteuid() != 0 and str(p).startswith('/tmp/') and p.is_dir()
                 and not p.is_symlink() and stat.S_IMODE(p.stat().st_mode) == 0o700, 'FIXTURE_SCOPE_REFUSED')

    def unused_services(self):
        if self.fixture is not None: return
        # list-units queries only already loaded objects; unlike `show`, it
        # cannot implicitly LoadUnit an installed but unadmitted service.
        units = sorted(Path(p).name for p in FIXED if p.startswith('/etc/systemd/system/'))
        r = subprocess.run(['/usr/bin/systemctl', 'list-units', '--all', '--plain', '--no-legend',
                            '--no-pager', *units, 'minimal-human-trust-approval@*.service'],
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=8,
                           env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'SYSTEMD_PAGER': 'cat'})
        need(r.returncode == 0 and not r.stdout.strip(), 'CODE_SERVICES_LOADED_PRESERVE_REQUIRED')

    def path(self, name):
        return Path(name) if self.fixture is None else Path(self.fixture) / name.lstrip('/')

    def exists(self, name):
        p = self.path(name)
        return p.exists() or p.is_symlink()

    def mkdir(self, name, mode, before_effect=lambda: None):
        p = self.path(name)
        missing = []
        while not p.exists():
            missing.append(p)
            p = p.parent
        for parent in [p, *p.parents]:
            s = parent.lstat()
            need(stat.S_ISDIR(s.st_mode) and not stat.S_ISLNK(s.st_mode), 'DESTINATION_PARENT_REFUSED')
            if self.fixture is None:
                need(s.st_uid == 0 and not s.st_mode & 0o022, 'DESTINATION_PARENT_UNPROTECTED')
        for q in reversed(missing):
            before_effect()
            q.mkdir(mode=mode)
            q.chmod(mode)
        return missing

    def write_new(self, name, raw, mode, before_effect=lambda: None):
        p = self.path(name)
        self.mkdir(str(Path(name).parent), 0o755, before_effect)
        before_effect()
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
        try:
            with os.fdopen(fd, 'wb', closefd=False) as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(fd)
            os.fchmod(fd, mode)
        finally:
            os.close(fd)
        fd = os.open(p.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        return self.identity(name)

    def identity(self, name):
        p = self.path(name)
        raw = read(p, protected=self.fixture is None)
        s = p.lstat()
        need(stat.S_IMODE(s.st_mode) in (0o600, 0o644, 0o755), 'DESTINATION_MODE_REFUSED')
        return {'sha256': sha(raw), 'dev': s.st_dev, 'ino': s.st_ino,
                'mode': stat.S_IMODE(s.st_mode), 'uid': s.st_uid, 'gid': s.st_gid, 'nlink': s.st_nlink}

    def journal(self, name, value):
        p = self.path(name)
        self.mkdir(str(Path(name).parent), 0o700)
        need(not p.exists() and not p.is_symlink(), 'JOURNAL_IMMUTABLE')
        self.write_new(name, canonical(value), 0o600)

    def append(self, name, value):
        p = self.path(name)
        fd = os.open(p, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            st = os.fstat(fd)
            need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and stat.S_IMODE(st.st_mode) == 0o600
                 and st.st_uid == os.geteuid(), 'PROGRESS_FILE_REFUSED')
            raw = canonical(value) + b'\n'
            at = 0
            while at < len(raw): at += os.write(fd, raw[at:])
            os.fsync(fd)
        finally: os.close(fd)
        fd = os.open(p.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)

    def load(self, name):
        return json.loads(read(self.path(name), protected=self.fixture is None))


def progress_records(catalog, backend):
    root = STATE + '/' + digest(catalog)
    name = root + '/progress.jsonl'
    if not backend.exists(name): return [], None
    raw = read(backend.path(name), protected=backend.fixture is None)
    need(not raw or raw.endswith(b'\n'), 'CODE_WRITE_OUTCOME_UNKNOWN_READBACK_REQUIRED')
    created = []; pending = None
    for line in raw.splitlines():
        record = json.loads(line)
        index = record.get('index')
        need(type(index) is int and index == len(created) and index < len(catalog['targets']), 'PROGRESS_ORDER_REFUSED')
        if record.get('kind') == 'intent':
            need(pending is None and set(record) == {'kind', 'index'}, 'PROGRESS_INTENT_REFUSED')
            pending = index
        else:
            row = catalog['targets'][index]
            need(record.get('kind') == 'result' and pending == index and set(record) == {'kind', 'index', 'target', 'identity'}
                 and record['target'] == row['target'] and record['identity']['sha256'] == row['sha256']
                 and record['identity']['mode'] == int(row['mode'], 8), 'PROGRESS_RESULT_REFUSED')
            created.append(record); pending = None
    return created, pending


def readback(catalog, backend):
    root = STATE + '/' + digest(catalog)
    if not backend.exists(root + '/intent.json'):
        return {'status': 'CODE_ADMISSION_NOT_STARTED', 'productionSigning': 0, 'serviceActions': 0}
    intent = backend.load(root + '/intent.json')
    need(intent['catalogHash'] == digest(catalog) and intent['targets'] == catalog['targets'], 'CODE_INTENT_CONFLICT')
    if backend.exists(root + '/removal-result.json'):
        result = backend.load(root + '/removal-result.json')
        removal = backend.load(root + '/removal-intent.json')
        created, pending = progress_records(catalog, backend)
        need(pending is None and result['catalogHash'] == removal['catalogHash'] == digest(catalog)
             and result['removedFiles'] == len(created) and removal['created'] == created, 'REMOVAL_RESULT_CONFLICT')
        for row in catalog['targets']: need(not backend.exists(row['target']), 'REMOVED_CODE_REAPPEARED')
        return {'status': 'CODE_REMOVED_UNUSED_HISTORY_ONLY', 'historicalReadOnly': True,
                'productionSigning': 0, 'serviceActions': 0}
    need(not backend.exists(root + '/removal-intent.json'), 'CODE_REMOVAL_OUTCOME_UNKNOWN_READBACK_REQUIRED')
    created, pending = progress_records(catalog, backend)
    need(pending is None, 'CODE_WRITE_OUTCOME_UNKNOWN_READBACK_REQUIRED')
    for row in created:
        need(backend.identity(row['target']) == row['identity'], 'INSTALLED_CODE_DRIFT')
    complete = backend.exists(root + '/result.json')
    if complete:
        result = backend.load(root + '/result.json')
        need(result['catalogHash'] == digest(catalog) and len(created) == len(catalog['targets']), 'CODE_RESULT_CONFLICT')
    return {'status': 'CODE_INSTALLED_NOT_LOADED_OR_STARTED' if complete else 'CODE_ADMISSION_INCOMPLETE_READBACK_REQUIRED',
            'catalogHash': digest(catalog), 'createdFiles': len(created),
            'productionSigning': 0, 'serviceActions': 0, 'historicalReadOnly': True}


def remove_unused(catalog, backend, approve, fresh, now=lambda: int(time.time()*1000)):
    root = STATE + '/' + digest(catalog)
    need(backend.exists(root + '/intent.json'), 'NO_CODE_ADMISSION_TO_REMOVE')
    if backend.exists(root + '/removal-result.json'): return readback(catalog, backend)
    need(not backend.exists(root + '/removal-intent.json'), 'CODE_REMOVAL_OUTCOME_UNKNOWN_READBACK_REQUIRED')
    created, pending = progress_records(catalog, backend)
    need(pending is None and bool(created), 'CODE_WRITE_OUTCOME_UNKNOWN_READBACK_REQUIRED')
    backend.unused_services()
    for name in USES: need(not backend.exists(name), 'CODE_ALREADY_USED_PRESERVE_REQUIRED')
    for row in created: need(backend.identity(row['target']) == row['identity'], 'INSTALLED_CODE_DRIFT')
    for row in catalog['targets'][len(created):]: need(not backend.exists(row['target']), 'UNTRACKED_CODE_WRITE_REFUSED')
    fresh()
    challenge = {'schema': 'mht.code-removal-native-challenge.v1', 'catalogHash': digest(catalog),
                 'createdFiles': len(created), 'nonce': secrets.token_hex(16),
                 'effects': 'REMOVE_ONLY_EXACT_UNUSED_CREATED_FILES_KEEP_ALL_RECEIPTS', 'maximumMs': 300000}
    need(approve(challenge) is True, 'CODE_REMOVAL_CANCELLED')
    accepted = now(); deadline = accepted + 300000
    started = time.monotonic()
    def effect_guard():
        fresh()
        need(accepted <= now() < deadline and time.monotonic() - started < 300, 'CODE_REMOVAL_EXPIRED')
    lock = os.open(backend.path(root + '/.lock'), os.O_RDWR | os.O_NOFOLLOW)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        backend.unused_services()
        for name in USES: need(not backend.exists(name), 'CODE_ALREADY_USED_PRESERVE_REQUIRED')
        for row in created: need(backend.identity(row['target']) == row['identity'], 'INSTALLED_CODE_DRIFT')
        backend.journal(root + '/removal-intent.json', {'schema': 'mht.code-removal-intent.v1',
            'catalogHash': digest(catalog), 'challengeHash': digest(challenge), 'acceptedAt': accepted,
            'expiresAt': deadline, 'created': created})
        for row in reversed(created):
            need(backend.identity(row['target']) == row['identity'], 'INSTALLED_CODE_DRIFT')
            for name in USES: need(not backend.exists(name), 'CODE_ALREADY_USED_PRESERVE_REQUIRED')
            path = backend.path(row['target'])
            effect_guard()
            path.unlink()
            fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try: os.fsync(fd)
            finally: os.close(fd)
        result = {'schema': 'mht.code-removal-completion.v1', 'status': 'CODE_REMOVED_UNUSED_HISTORY_ONLY',
                  'catalogHash': digest(catalog), 'removedFiles': len(created), 'completedAt': now(),
                  'oldApprovalRenewed': False, 'serviceActions': 0, 'businessAcceptance': False}
        backend.journal(root + '/removal-result.json', result)
        return result
    finally: os.close(lock)


def install(catalog, packet, backend, approve, fresh, now=lambda: int(time.time()*1000), fault=lambda _: None):
    payload = prepare(catalog, packet)  # Hold exact reviewed public bytes before asking for consent.
    root = STATE + '/' + digest(catalog)
    if backend.exists(root + '/intent.json'):
        return readback(catalog, backend)  # Never auto-resume an interrupted install.
    backend.unused_services()
    for name in USES:
        need(not backend.exists(name), 'PREVIOUS_TRUST_USAGE_REFUSED')
    for name in (LIB.rstrip('/'), OPT.rstrip('/'), '/etc/minimal-human-trust'):
        need(not backend.exists(name), 'FOREIGN_PROTECTED_ROOT_REFUSED')
    for row, _ in payload:
        need(not backend.exists(row['target']), 'DESTINATION_EXISTS')
    fresh()
    challenge = {'schema': 'mht.code-admission-native-challenge.v1', 'catalogHash': digest(catalog),
                 'contentRoot': catalog['contentRoot'], 'sourceRevision': 19, 'nonce': secrets.token_hex(16),
                 'host': 'jenn-System-Product-Name', 'targets': len(payload),
                 'authorityType': 'TRUSTED_HOST_ADMIN_CODE_ONLY', 'humanIdentityConfirmed': False,
                 'effects': 'EXCLUSIVE_CODE_FILES_ONLY_NO_SIGN_KEYS_SERVICES_SELECTORS', 'maximumMs': 300000}
    need(approve(challenge) is True, 'CODE_ADMISSION_CANCELLED')
    accepted = now(); deadline = accepted + 300000
    started = time.monotonic()
    def effect_guard():
        need(accepted <= now() < deadline and time.monotonic() - started < 300, 'CODE_ADMISSION_EXPIRED')
    fresh()
    effect_guard()
    # Journal creation is an audit effect after actual native acceptance.
    backend.mkdir(root, 0o700)
    lock_path = backend.path(root + '/.lock')
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        st = os.fstat(fd)
        need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and st.st_uid == os.geteuid()
             and stat.S_IMODE(st.st_mode) == 0o600, 'LOCK_FILE_REFUSED')
        need(not backend.exists(root + '/intent.json'), 'CONCURRENT_CODE_ADMISSION')
        for name in USES: need(not backend.exists(name), 'PREVIOUS_TRUST_USAGE_REFUSED')
        for name in (LIB.rstrip('/'), OPT.rstrip('/'), '/etc/minimal-human-trust'):
            need(not backend.exists(name), 'FOREIGN_PROTECTED_ROOT_REFUSED')
        backend.journal(root + '/intent.json', {'schema': 'mht.code-admission-intent.v1',
            'catalogHash': digest(catalog), 'challengeHash': digest(challenge),
            'authorityType': 'TRUSTED_HOST_ADMIN_CODE_ONLY', 'humanIdentityConfirmed': False,
            'nativeHostAdmin': challenge.get('nativeHostAdmin'),
            'acceptedAt': accepted, 'expiresAt': deadline, 'targets': catalog['targets']})
        created = []
        for index, (row, raw) in enumerate(payload):
            need(accepted <= now() < deadline, 'CODE_ADMISSION_EXPIRED')
            if index % 128 == 0: fresh()
            backend.append(root + '/progress.jsonl', {'kind': 'intent', 'index': index})
            fault('before_write')
            identity = backend.write_new(row['target'], raw, int(row['mode'], 8), effect_guard)
            need(identity['sha256'] == row['sha256'] and identity['mode'] == int(row['mode'], 8), 'CODE_WRITE_READBACK_FAILED')
            record = {'kind': 'result', 'index': index, 'target': row['target'], 'identity': identity}
            created.append(record)
            backend.append(root + '/progress.jsonl', record)
            fault('after_known_write')
        for row in created:
            need(backend.identity(row['target']) == row['identity'], 'FINAL_CODE_READBACK_FAILED')
        need(accepted <= now() < deadline, 'CODE_ADMISSION_EXPIRED')
        fresh()
        effect_guard()
        result = {'schema': 'mht.code-admission-completion.v1', 'status': 'CODE_INSTALLED_NOT_LOADED_OR_STARTED',
                  'catalogHash': digest(catalog), 'contentRoot': catalog['contentRoot'],
                  'installedFiles': len(created), 'completedAt': now(),
                  'authorityType': 'TRUSTED_HOST_ADMIN_CODE_ONLY', 'humanIdentityConfirmed': False,
                  'nativeHostAdmin': challenge.get('nativeHostAdmin'),
                  'signaturesIssued': 0, 'keysChanged': False, 'serviceActions': 0,
                  'selectorsChanged': False, 'ownerChanged': False, 'businessAcceptance': False}
        backend.journal(root + '/result.json', result)
        return result
    finally:
        os.close(fd)


def fresh_source19():
    pub = json.loads(read('/run/r16-owner/public-config.json', protected=True))
    w = json.loads(read('/var/lib/r16-owner/configuration/state.json', protected=True))
    need(digest(pub) == PUB19 and w.get('schema') == 1, 'SOURCE19_CURRENT_STATE_DRIFT')
    config = w['data']; d = config['delivery']; envelope = d['envelope']
    need(d['revision'] == 19 and digest(envelope) == DELIVERY19
         and envelope['body']['revision'] == 19 and envelope['body']['publicConfig'] == pub,
         'SOURCE19_SIGNED_DELIVERY_DRIFT')
    need(d['hash'] == digest({'publicConfig': pub, 'control': envelope['body']['control'],
                             'connectionNonce': config.get('connectionNonce') or 0}), 'SOURCE19_CACHE_DRIFT')


def _native_proc(pid):
    """Only identity metadata; never read argv, environ or terminal input."""
    raw = Path('/proc/' + str(pid) + '/stat').read_text()
    need(raw.startswith(str(pid) + ' (') and ')' in raw, 'NATIVE_PROC_REFUSED')
    fields = raw[raw.rfind(')') + 2:].split()
    status = Path('/proc/' + str(pid) + '/status').read_text()
    uid_rows = [x.split()[1:] for x in status.splitlines() if x.startswith('Uid:')]
    need(len(fields) >= 20 and len(uid_rows) == 1 and len(uid_rows[0]) == 4
         and all(x.isdecimal() for x in uid_rows[0]), 'NATIVE_PROC_REFUSED')
    return {'pid': pid, 'ppid': int(fields[1]), 'pgrp': int(fields[2]), 'sid': int(fields[3]),
            'ttyNr': int(fields[4]) & 0xffffffff, 'foregroundPgrp': int(fields[5]),
            'startTicks': fields[19], 'uids': tuple(int(x) for x in uid_rows[0])}


def _native_executable(path):
    # Python3 may be the distribution's versioned symlink. Resolve the fixed
    # trusted name, then verify every real ancestor and final inode.
    p = Path(path).resolve(strict=True)
    for q in (*reversed(p.parents), p):
        s = q.lstat()
        need(s.st_uid == 0 and not s.st_mode & 0o022 and not stat.S_ISLNK(s.st_mode), 'NATIVE_EXECUTABLE_REFUSED')
    s = p.stat()
    need(stat.S_ISREG(s.st_mode), 'NATIVE_EXECUTABLE_REFUSED')
    return (s.st_dev, s.st_ino)


def _native_exe_is(pid, expected):
    # /proc/pid/exe is the kernel-held executable inode, not a process name or
    # caller-provided SUDO_* environment claim.
    s = os.stat('/proc/' + str(pid) + '/exe')
    need(stat.S_ISREG(s.st_mode) and s.st_uid == 0 and not s.st_mode & 0o022
         and (s.st_dev, s.st_ino) == expected, 'NATIVE_EXECUTABLE_REFUSED')


def _native_pts(pid=None):
    rows = [os.fstat(fd) if pid is None else os.stat('/proc/' + str(pid) + '/fd/' + str(fd)) for fd in (0, 1, 2)]
    names = [os.ttyname(fd) if pid is None else os.readlink('/proc/' + str(pid) + '/fd/' + str(fd)) for fd in (0, 1, 2)]
    key = lambda s: (s.st_dev, s.st_ino, s.st_rdev, s.st_uid, s.st_gid, stat.S_IMODE(s.st_mode))
    need(all(re.fullmatch(r'/dev/pts/[0-9]+', n) and n == names[0] for n in names)
         and all(stat.S_ISCHR(s.st_mode) and stat.S_IMODE(s.st_mode) in (0o600, 0o620)
                 and key(s) == key(rows[0]) for s in rows), 'SAME_FOREGROUND_JENN_TTY_REQUIRED')
    # No-follow traversal binds the actual named devpts inode. The /dev/tty
    # alias is intentionally not compared with this real pts metadata.
    root = os.open('/dev', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        pts = os.open('pts', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root)
        try:
            fd = os.open(names[0].rsplit('/', 1)[1], os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=pts)
            try:
                need(key(os.fstat(fd)) == key(rows[0]), 'NATIVE_PTS_NODE_DRIFT')
                if pid is None:
                    need(os.tcgetpgrp(fd) == os.getpgrp(), 'FOREGROUND_NATIVE_TTY_REQUIRED')
            finally: os.close(fd)
        finally: os.close(pts)
    finally: os.close(root)
    return {'path': names[0], 'identity': key(rows[0])}


def native_root_context():
    need(os.getuid() == os.geteuid() == 0 and socket.gethostname() == 'jenn-System-Product-Name', 'LOCAL_HOST_ADMIN_REQUIRED')
    need(sys.stdin.isatty() and all(os.isatty(fd) and os.tcgetpgrp(fd) == os.getpgrp() for fd in (0, 1, 2)), 'FOREGROUND_NATIVE_TTY_REQUIRED')
    alias = os.open('/dev/tty', os.O_RDWR | os.O_NOFOLLOW)
    try: need(os.tcgetpgrp(alias) == os.getpgrp(), 'FOREGROUND_NATIVE_TTY_REQUIRED')
    finally: os.close(alias)
    inner = _native_pts()
    need(inner['identity'][3] in (0, 1000), 'JENN_OR_PROVEN_SUDO_PTY_REQUIRED')
    sudo = _native_executable('/usr/bin/sudo')
    python = _native_executable('/usr/bin/python3')
    original = _native_proc(os.getpid())
    need(original['uids'] == (0, 0, 0, 0) and original['pgrp'] == os.getpgrp()
         and original['ttyNr'] == inner['identity'][2] and original['foregroundPgrp'] == os.getpgrp(), 'NATIVE_ROOT_PROCESS_DRIFT')
    _native_exe_is(original['pid'], python)
    chain = []
    pid = original['ppid']
    for _ in range(2):
        row = _native_proc(pid)
        if row['uids'][1:] != (0, 0, 0):
            break
        # sudo may preserve the invoking real UID while retaining root
        # effective/saved/filesystem UIDs. No other real UID is admitted.
        need(row['uids'][0] in (0, 1000), 'NATIVE_SUDO_UID_REFUSED')
        if not chain:
            need(row['sid'] == original['sid'], 'NATIVE_SUDO_SESSION_DRIFT')
        _native_exe_is(pid, sudo)
        chain.append(row)
        pid = row['ppid']
    need(len(chain) in (1, 2), 'TRUSTED_SUDO_ANCESTRY_REQUIRED')
    launcher = _native_proc(pid)
    need(launcher['uids'] == (1000, 1000, 1000, 1000), 'JENN_LAUNCHER_REQUIRED')
    _native_exe_is(pid, python)
    outer = _native_pts(pid)
    need(outer['identity'][3] == 1000, 'JENN_OUTER_PTY_REQUIRED')
    for row in chain:
        need(_native_pts(row['pid']) == outer, 'SUDO_OUTER_PTY_DRIFT')
    need((inner == outer) if inner['identity'][3] == 1000 else inner['path'] != outer['path'], 'SUDO_INNER_PTY_UNPROVEN')
    allowed_outer_groups = {chain[-1]['pgrp'], launcher['pgrp']}
    if inner == outer:
        allowed_outer_groups.add(original['pgrp'])
    # A different controlling TTY cannot be queried with TIOCGPGRP from the
    # inner session (Linux correctly returns ENOTTY). Its real owner process's
    # kernel stat carries tty_nr/tpgid; bind both to the verified outer pts.
    need(launcher['ttyNr'] == outer['identity'][2] and launcher['foregroundPgrp'] in allowed_outer_groups,
         'OUTER_NATIVE_TTY_BACKGROUND')
    if len(chain) == 2:
        need(chain[-1]['ttyNr'] == outer['identity'][2]
             and chain[-1]['foregroundPgrp'] == launcher['foregroundPgrp'], 'SUDO_OUTER_FOREGROUND_DRIFT')
    # This G1 action admits public code under TRUSTED_HOST_ADMIN. Neither a
    # global graphical Display nor a sudo TTY establishes Human identity or
    # physical caller localness. The separate G2/G3 pkexec/auth_self ceremony
    # retains those requirements; this entry never substitutes for it.
    for row in (original, *chain, launcher):
        need(_native_proc(row['pid']) == row, 'NATIVE_PROCESS_ANCESTRY_CHANGED')
        if row in chain: _native_exe_is(row['pid'], sudo)
    _native_exe_is(original['pid'], python)
    _native_exe_is(launcher['pid'], python)
    need(_native_pts() == inner and _native_pts(launcher['pid']) == outer
         and all(_native_pts(row['pid']) == outer for row in chain)
         and all(os.tcgetpgrp(fd) == os.getpgrp() for fd in (0, 1, 2)), 'NATIVE_PTY_CHANGED')
    return {'process': original, 'sudoAncestors': chain, 'launcher': launcher, 'inner': inner, 'outer': outer,
            'outerForegroundPgrp': launcher['foregroundPgrp'],
            'authorityType': 'TRUSTED_HOST_ADMIN_CODE_ONLY', 'humanIdentityConfirmed': False,
            'callerLocalness': 'NOT_ASSERTED_BY_CODE_ADMISSION'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('describe', 'apply', 'readback', 'remove-unused'))
    parser.add_argument('--catalog', required=True, type=Path)
    parser.add_argument('--catalog-sha256', required=True)
    parser.add_argument('--packet', type=Path)
    args = parser.parse_args()
    try:
        raw = read(args.catalog)
        need(sha(raw) == args.catalog_sha256, 'REVIEWED_CATALOG_HASH_REQUIRED')
        catalog = json.loads(raw)
        if args.mode == 'describe':
            need(args.packet is not None, 'PACKET_REQUIRED'); prepare(catalog, args.packet)
            print(json.dumps({'status': 'EXACT_CODE_PACKET_VERIFIED_NO_EFFECTS', 'catalogHash': digest(catalog),
                              'contentRoot': catalog['contentRoot'], 'files': len(catalog['targets']), 'authority': False}));return 0
        native_root_context(); fresh_source19(); backend = FileBackend()
        if args.mode == 'readback':
            print(json.dumps(readback(catalog, backend)));return 0
        def approve(challenge):
            native_before = native_root_context()
            challenge['nativeHostAdmin'] = native_before
            print('TRUSTED_HOST_ADMIN_CODE_ONLY：只准入准确代码；不证明Human身份或物理本机来源。')
            print('不签名、不生成密钥、不加载/启动服务、不切换发行或Owner。')
            print(json.dumps(challenge, sort_keys=True))
            verb = 'REMOVE_UNUSED_CODE' if challenge['schema'] == 'mht.code-removal-native-challenge.v1' else 'INSTALL_CODE'
            exact = verb + ' ' + digest(challenge)
            accepted = input('本人核对完整审阅目录后准确输入 '+exact+'\n> ') == exact
            need(native_root_context() == native_before, 'NATIVE_CONFIRMATION_CONTEXT_CHANGED')
            return accepted
        if args.mode == 'remove-unused':
            print(json.dumps(remove_unused(catalog, backend, approve, fresh_source19), sort_keys=True));return 0
        need(args.packet is not None, 'PACKET_REQUIRED')
        print(json.dumps(install(catalog, args.packet, backend, approve, fresh_source19), sort_keys=True));return 0
    except (OSError, ValueError, KeyError, EOFError, subprocess.SubprocessError):
        print('{"status":"CODE_ADMISSION_REFUSED_OR_READBACK_REQUIRED","automaticRetry":false,"businessAcceptance":false}')
        return 78


if __name__ == '__main__':
    raise SystemExit(main())
