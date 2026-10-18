"""Standalone public-code admission. No services, signing, selectors or business IO.

Production entry is a byte-pinned stdlib loader plus the frozen native guard.
Fixture construction is restricted to a private, ordinary-user temporary root.
Interrupted effects are evidence for readback, never a license to resume.
"""
import ctypes
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import stat
import time

LOCAL = 'jenn-System-Product-Name'
CLOUD = 'VM-0-12-ubuntu'
HEAD = '8ffec0d6b4888f7608737ea400182334e0f23aa6'
CATALOG = '2e14bdbe36b523e333030dc0c8717a0281b07ffd51da93120089fee2ccc9b2a3'
CAPSULE = '62040899608e59108f40475b071d57f13d1275dd933cc9ee49ab692736ce9a8e'
GUARD = '43f055a7d00d13b95750dbc795a47c276065e3e4cd69768b7e8aa9c3af42cafc'
ROOT = '/usr/lib/r16-maintenance/source19-native-transition-r1'
PIN = '/etc/r16-maintenance/source19-native-transition-r1-entry-capsule.json'
HELPER = '/usr/libexec/r16-source19-native-transition-r1-rpc'
SUDOERS = '/etc/sudoers.d/r16-source19-native-transition-r1'
STATE = '/var/lib/r16-maintenance/source19-native-code-admission-r1/' + CATALOG
PUB = '56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec'
DELIVERY = 'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9'
GRANT = '00ac437d66143e627132975555d06396d69ff69616f630d19e3622627e15c5e6'
LIMIT = 2 * 1024 * 1024
SOURCE_STATE_LIMIT = 32 * 1024 * 1024
SOURCE_STATE_PATHS = frozenset({
    '/var/lib/r16-owner/configuration/state.json',
    '/var/lib/r16-cloud/authority/state.json',
})


def need(ok, code):
    if not ok:
        raise ValueError(code)


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def digest(value):
    return sha(raw(value))


def parse(value):
    def pairs(items):
        out = {}
        for k, v in items:
            need(k not in out, 'DUPLICATE_JSON_KEY')
            out[k] = v
        return out
    return json.loads(value, object_pairs_hook=pairs,
                      parse_constant=lambda _: need(False, 'NONFINITE_JSON'))


def identity(s):
    return {'dev': s.st_dev, 'ino': s.st_ino, 'uid': s.st_uid, 'gid': s.st_gid,
            'mode': stat.S_IMODE(s.st_mode), 'nlink': s.st_nlink, 'bytes': s.st_size,
            'mtimeNs': str(s.st_mtime_ns), 'ctimeNs': str(s.st_ctime_ns)}


def parents(path):
    return [str(p) for p in reversed(Path(path).parents) if str(p) != '/']


def target_bytes(packet, host):
    need(host in (LOCAL, CLOUD), 'FIXED_HOST_REQUIRED')
    c = packet['bundle/CODE_ADMISSION_CANDIDATE.json']
    need(sha(c) == CATALOG, 'ORIGINAL_REVIEW_OBJECT_CHANGED')
    obj = parse(c)
    need(obj['sourceHead'] == HEAD and obj['capsuleHash'] == CAPSULE,
         'ORIGINAL_REVIEW_BINDING_CHANGED')
    need(sha(packet['bundle/root/ENTRY_FREEZE.json']) == CAPSULE,
         'ORIGINAL_CAPSULE_CHANGED')
    need(sha(packet['native_guard.py']) == GUARD, 'FROZEN_NATIVE_GUARD_CHANGED')
    specs = dict(obj['targets'])
    if host == CLOUD:
        specs.update(obj['cloudOnlyTargets'])
    need(len(specs) == (30 if host == LOCAL else 32), 'FIXED_TARGET_COUNT')
    result = {}
    for path, spec in sorted(specs.items()):
        if path.startswith(ROOT + '/'):
            name = 'bundle/root/' + path[len(ROOT) + 1:]
        elif path == PIN:
            name = 'bundle/installed-entry-pin.json'
        elif path == HELPER:
            name = 'bundle/cloud-policy/r16-source19-native-transition-r1-rpc'
        elif path == SUDOERS:
            name = 'bundle/cloud-policy/r16-source19-native-transition-r1.sudoers'
        else:
            raise ValueError('TARGET_OUTSIDE_REVIEW')
        b = packet[name]
        need(len(b) == spec['bytes'] and sha(b) == spec['sha256']
             and spec['uid'] == spec['gid'] == 0
             and spec['mode'] in (0o600, 0o644, 0o755, 0o440), 'TARGET_BYTES_CHANGED')
        result[path] = (spec, b)
    return result


def audit_scope(targets):
    files = {STATE + '/' + n: 0o600 for n in
             ('.lock', 'intent.json', 'progress.jsonl', 'result.json',
              'withdraw-intent.json', 'withdraw-progress.jsonl', 'withdraw-result.json')}
    archives = {STATE + '/archive' + path: spec['mode'] for path, (spec, _) in targets.items()}
    dirs = set(parents(STATE + '/intent.json'))
    for p in archives:
        dirs.update(parents(p))
    # Existing protected ancestors are never chmodded. New audit namespace dirs
    # are private; the original reviewed code hierarchy uses its own 0755 mode.
    return {'files': files, 'archiveTargets': archives, 'uid': 0, 'gid': 0,
            'newDirectoryModes': {p: 0o700 for p in sorted(dirs)},
            'authority': False, 'historyRetained': True}


class FS:
    """All leaf operations are relative to held, validated no-follow dir FDs."""
    def __init__(self, fixture=None):
        self.fixture = fixture
        self.uid = self.gid = 0
        if fixture is not None:
            p = Path(fixture)
            need(os.geteuid() != 0 and p.is_absolute() and str(p).startswith('/tmp/'),
                 'FIXTURE_ORDINARY_PRIVATE_TMP_ONLY')
            s = p.lstat()
            need(stat.S_ISDIR(s.st_mode) and s.st_uid == os.getuid()
                 and stat.S_IMODE(s.st_mode) == 0o700, 'FIXTURE_PRIVATE_ROOT_REQUIRED')
            self.uid, self.gid = os.getuid(), os.getgid()

    def checkdir(self, fd):
        s = os.fstat(fd)
        need(stat.S_ISDIR(s.st_mode) and s.st_uid == self.uid and s.st_gid == self.gid
             and not s.st_mode & 0o022, 'UNPROTECTED_DIRECTORY')

    def device(self, path):
        fd = os.open(self.fixture or '/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            self.checkdir(fd)
            for name in path.split('/')[1:-1]:
                try:
                    c = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                except FileNotFoundError:
                    break
                self.checkdir(c)
                os.close(fd)
                fd = c
            return os.fstat(fd).st_dev
        finally:
            os.close(fd)

    def parent(self, path, create=False, guard=None, directory_mode=0o755):
        need(path.startswith('/') and '..' not in path.split('/')
             and '//' not in path and not path.endswith('/'), 'ABSOLUTE_FIXED_PATH_REQUIRED')
        fd = os.open(self.fixture or '/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            self.checkdir(fd)
            for name in path.split('/')[1:-1]:
                try:
                    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                except FileNotFoundError:
                    if not create:
                        raise
                    guard()
                    globals()['EFFECTS_STARTED'] = True
                    os.mkdir(name, directory_mode, dir_fd=fd)
                    guard()
                    os.fsync(fd)
                    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    guard()
                    os.fchmod(child, directory_mode)
                    guard()
                    os.fsync(child)
                self.checkdir(child)
                os.close(fd)
                fd = child
            return fd, path.rsplit('/', 1)[1]
        except BaseException:
            os.close(fd)
            raise

    def inspect(self, path, modes=None):
        # The frozen public-state reader already permits 32MiB configuration
        # wrappers. This exception is only for those two literal source paths;
        # code, pins, audit and all other objects retain the 2MiB ceiling.
        maximum = SOURCE_STATE_LIMIT if path in SOURCE_STATE_PATHS else LIMIT
        try:
            d, n = self.parent(path)
        except FileNotFoundError:
            return None
        try:
            try:
                fd = os.open(n, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=d)
            except FileNotFoundError:
                return None
            try:
                s = os.fstat(fd)
                need(stat.S_ISREG(s.st_mode) and s.st_nlink == 1
                     and s.st_uid == self.uid and s.st_gid == self.gid
                     and not s.st_mode & 0o022 and s.st_size <= maximum,
                     'UNPROTECTED_FILE')
                if modes is not None:
                    need(stat.S_IMODE(s.st_mode) in modes, 'FILE_MODE_DRIFT')
                b = bytearray()
                while len(b) <= maximum:
                    chunk = os.read(fd, min(65536, maximum + 1 - len(b)))
                    if not chunk:
                        break
                    b.extend(chunk)
                need(len(b) <= maximum and identity(s) == identity(os.fstat(fd)), 'FILE_CHANGED_DURING_READ')
                leaf = os.stat(n, dir_fd=d, follow_symlinks=False)
                need(identity(leaf) == identity(s), 'NAMED_FILE_DRIFT')
                return {'identity': identity(s), 'sha256': sha(b), 'raw': bytes(b)}
            finally:
                os.close(fd)
        finally:
            os.close(d)

    def exclusive(self, path, b, mode, guard, directory_mode=0o755):
        d, n = self.parent(path, True, guard, directory_mode)
        try:
            guard()
            globals()['EFFECTS_STARTED'] = True
            fd = os.open(n, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         mode, dir_fd=d)
            try:
                guard()
                os.fchmod(fd, mode)
                offset = 0
                while offset < len(b):
                    guard()
                    count = os.write(fd, b[offset:])
                    need(count > 0, 'SHORT_WRITE')
                    offset += count
                guard()
                os.fsync(fd)
            finally:
                os.close(fd)
            guard()
            os.fsync(d)
        finally:
            os.close(d)
        out = self.inspect(path, [mode])
        need(out is not None and out['sha256'] == sha(b), 'CREATED_FILE_READBACK_FAILED')
        return out

    def append(self, path, value, guard):
        before = self.inspect(path, [0o600])
        need(before is not None and before['raw'].endswith(b'\n') or
             before is not None and before['raw'] == b'', 'TORN_JOURNAL_REFUSED')
        d, n = self.parent(path)
        try:
            fd = os.open(n, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW, dir_fd=d)
            try:
                need(identity(os.fstat(fd)) == before['identity'], 'JOURNAL_CHANGED')
                b = raw(value) + b'\n'
                guard()
                globals()['EFFECTS_STARTED'] = True
                need(os.write(fd, b) == len(b), 'SHORT_JOURNAL_WRITE')
                guard()
                os.fsync(fd)
            finally:
                os.close(fd)
        finally:
            os.close(d)

    def archive(self, source, dest, expected, guard):
        need(self.inspect(source) == expected, 'CREATED_OBJECT_DRIFT')
        a, sn = self.parent(source)
        try:
            b, dn = self.parent(dest, True, guard, 0o700)
            try:
                need(os.fstat(a).st_dev == os.fstat(b).st_dev == expected['identity']['dev'],
                     'CROSS_DEVICE_ARCHIVE_REFUSED')
                need(self.inspect(dest) is None, 'ARCHIVE_ALREADY_PRESENT_READBACK_ONLY')
                need(self.inspect(source) == expected, 'CREATED_OBJECT_DRIFT')
                libc = ctypes.CDLL(None, use_errno=True)
                rename = getattr(libc, 'renameat2', None)
                need(rename is not None, 'ATOMIC_NOREPLACE_UNAVAILABLE')
                rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
                rename.restype = ctypes.c_int
                guard()
                globals()['EFFECTS_STARTED'] = True
                if rename(a, os.fsencode(sn), b, os.fsencode(dn), 1) != 0:
                    raise OSError(ctypes.get_errno(), 'ATOMIC_NOREPLACE_REFUSED')
                guard()
                os.fsync(a)
                guard()
                os.fsync(b)
            finally:
                os.close(b)
        finally:
            os.close(a)
        after = self.inspect(dest)
        need(after is not None and self.inspect(source) is None
             and after['sha256'] == expected['sha256']
             and all(after['identity'][k] == expected['identity'][k]
                     for k in ('dev', 'ino', 'uid', 'gid', 'mode', 'bytes', 'nlink', 'mtimeNs')),
             'ARCHIVE_RESULT_READBACK_REQUIRED')
        return after

    def namespace(self, root, allowed):
        # Refuse a foreign object anywhere in the dedicated code namespace.
        wanted_dirs = {p for f in allowed for p in parents(f)}
        try:
            d, name = self.parent(root)
        except FileNotFoundError:
            return
        try:
            try:
                fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=d)
            except FileNotFoundError:
                return
            try:
                def walk(current, path):
                    self.checkdir(current)
                    for n in os.listdir(current):
                        p = path + '/' + n
                        s = os.stat(n, dir_fd=current, follow_symlinks=False)
                        if stat.S_ISDIR(s.st_mode):
                            need(p in wanted_dirs, 'FOREIGN_CODE_DIRECTORY')
                            c = os.open(n, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
                            try:
                                walk(c, p)
                            finally:
                                os.close(c)
                        else:
                            need(p in allowed, 'FOREIGN_CODE_OBJECT')
                            self.inspect(p)
                walk(fd, root)
            finally:
                os.close(fd)
        finally:
            os.close(d)


class Admission:
    def __init__(self, packet, host, fs, native, source, boot, wall=time.time, mono=time.monotonic):
        self.packet, self.host, self.fs = packet, host, fs
        self.native, self.source, self.boot = native, source, boot
        self.wall, self.mono = wall, mono
        self.targets = target_bytes(packet, host)
        self.supplement = parse(packet['SUPPLEMENTAL_NATIVE_ENTRY_REVIEW_R1.json'])
        self.supplement_hash = sha(packet['SUPPLEMENTAL_NATIVE_ENTRY_REVIEW_R1.json'])
        need(self.supplement['originalObjectSha256'] == CATALOG
             and self.supplement['sourceHead'] == HEAD
             and self.supplement['capsuleHash'] == CAPSULE
             and self.supplement['auditScopes'][host] == audit_scope(self.targets),
             'SUPPLEMENT_SCOPE_MISMATCH')
        self.grant = None

    def inventory(self):
        self.fs.namespace(ROOT, self.targets)
        result = {}
        for path, (spec, _) in self.targets.items():
            r = self.fs.inspect(path, [spec['mode']])
            if r is not None:
                need(r['sha256'] == spec['sha256'] and r['identity']['bytes'] == spec['bytes'],
                     'EXISTING_TARGET_NOT_EXACT')
            result[path] = None if r is None else {k: v for k, v in r.items() if k != 'raw'}
        return result

    def review(self, action):
        need(action in ('install', 'withdraw'), 'ACTION_REFUSED')
        native = self.native()
        source = self.source()
        inventory = self.inventory()
        audit_device = self.fs.device(STATE + '/intent.json')
        devices = {p: self.fs.device(p) for p in self.targets}
        need(all(d == audit_device for p, d in devices.items() if inventory[p] is None),
             'CROSS_DEVICE_ROLLBACK_UNAVAILABLE')
        if action == 'install':
            # Even an empty object-specific audit directory proves an earlier
            # attempt may have produced effects. It cannot be resumed here.
            try:
                fd, _ = self.fs.parent(STATE + '/intent.json')
            except FileNotFoundError:
                pass
            else:
                os.close(fd)
                raise ValueError('AUDIT_NAMESPACE_PRESENT_READBACK_ONLY')
        else:
            self.withdraw_inventory()
        return {'schema': 'r16.source19-native-code-admission.challenge.v1',
                'host': self.host, 'action': action, 'sourceHead': HEAD, 'capsuleHash': CAPSULE,
                'originalObjectSha256': CATALOG, 'supplementSha256': self.supplement_hash,
                'entryPacketSha256': globals().get('ENTRY_PACKET_SHA'),
                'heldPacketFileSha256': globals().get('HELD_PACKET_FILE_SHA'),
                'targets': {p: s for p, (s, _) in self.targets.items()},
                'before': inventory, 'auditScope': audit_scope(self.targets),
                'archiveDevice': audit_device, 'targetDevices': devices,
                'nativeContext': native, 'source19': source, 'bootId': self.boot(),
                'nonce': secrets.token_hex(16), 'validForMsFromAcceptance': 300000,
                'permissions': ['EXCLUSIVE_PUBLIC_CODE_CREATE', 'ADDITIVE_ADMINISTRATIVE_AUDIT']
                 if action == 'install' else ['ARCHIVE_ONLY_IDENTICAL_OWN_CREATED_CODE', 'ADDITIVE_ADMINISTRATIVE_AUDIT'],
                'withdrawalLimits': {'neverUsedClaimed': False,
                     'usageCheck': 'VISIBLE_MAPS_AND_FD_REFERENCES_AND_MAINTENANCE_STATE_ONLY',
                     'readonlyPreflightMayFailOrContinueFromAlreadyHeldBytes': True,
                     'noProcessSignalOrServiceAction': True},
                'humanIdentityConfirmed': False, 'businessAcceptance': False}

    def accept(self, challenge, typed):
        expected = ('INSTALL_READONLY_CODE' if challenge['action'] == 'install' else
                    'ARCHIVE_EXACT_NEW_CODE') + ' ' + ('CLOUD' if self.host == CLOUD else 'LOCAL') + ' ' + digest(challenge)
        need(typed == expected, 'EXACT_NATIVE_INTENT_CANCELLED')
        # Start the window when the complete human intent is received, not
        # after potentially slow verification. No callback can extend it.
        now, monotonic = self.wall(), self.mono()
        need(challenge['nativeContext'] == self.native() and challenge['source19'] == self.source()
             and challenge['before'] == self.inventory() and challenge['bootId'] == self.boot(),
             'NATIVE_OR_SOURCE_OR_TARGET_CHANGED')
        need(challenge['archiveDevice'] == self.fs.device(STATE + '/intent.json')
             and challenge['targetDevices'] == {p: self.fs.device(p) for p in self.targets},
             'FILESYSTEM_CHANGED_BEFORE_ACCEPTANCE')
        # No disk writes, lock, mkdir or audit append happen before this point.
        self.grant = {'challenge': challenge, 'acceptedAt': now, 'expiresAt': now + 300,
                      'monotonicAccepted': monotonic, 'nativeIntentHash': digest(challenge)}
        self.time_guard()

    def time_guard(self):
        g = self.grant
        need(g is not None and self.boot() == g['challenge']['bootId'],
             'NATIVE_AUTHORITY_EXPIRED_NO_EXTENSION')
        # Boot observation precedes the final clock observations; a slow boot
        # read cannot consume the window after the last clock check.
        now, monotonic = self.wall(), self.mono()
        need(g['acceptedAt'] <= now < g['expiresAt']
             and 0 <= monotonic - g['monotonicAccepted'] < 300,
             'NATIVE_AUTHORITY_EXPIRED_NO_EXTENSION')

    def guard(self):
        self.time_guard()
        g = self.grant
        need(self.native() == g['challenge']['nativeContext'], 'NATIVE_CONTEXT_CHANGED')
        need(self.source() == g['challenge']['source19'], 'SOURCE19_CHANGED')
        need(g['challenge']['archiveDevice'] == self.fs.device(STATE + '/intent.json')
             and g['challenge']['targetDevices'] == {p: self.fs.device(p) for p in self.targets},
             'FILESYSTEM_CHANGED')
        # native/source/device checks can block. Recheck at the effect boundary.
        self.time_guard()

    def write(self, name, value):
        return self.fs.exclusive(STATE + '/' + name, raw(value) + b'\n', 0o600,
                                 self.guard, 0o700)

    def lock(self, create):
        p = STATE + '/.lock'
        if create:
            self.fs.exclusive(p, b'', 0o600, self.guard, 0o700)
        before = self.fs.inspect(p, [0o600])
        need(before is not None, 'AUDIT_LOCK_MISSING')
        d, n = self.fs.parent(p)
        try:
            fd = os.open(n, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=d)
        finally:
            os.close(d)
        try:
            need(identity(os.fstat(fd)) == before['identity'], 'LOCK_CHANGED')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except BaseException:
            os.close(fd)
            raise

    def install(self):
        self.guard()
        ch = self.grant['challenge']
        need(ch['action'] == 'install' and self.inventory() == ch['before'], 'INSTALL_TARGET_CHANGED')
        # Exclusive audit intent is first; after any partial effect, another
        # install attempt is refused by review(). Missing journals stay missing.
        self.write('intent.json', {'challenge': ch, 'acceptedAt': self.grant['acceptedAt'],
                                   'expiresAt': self.grant['expiresAt'], 'nativeIntentHash': digest(ch)})
        fd = self.lock(True)
        try:
            self.fs.exclusive(STATE + '/progress.jsonl', b'', 0o600, self.guard, 0o700)
            for path, (spec, b) in self.targets.items():
                before = ch['before'][path]
                current = self.fs.inspect(path, [spec['mode']])
                clean = None if current is None else {k: v for k, v in current.items() if k != 'raw'}
                need(clean == before, 'INSTALL_TARGET_CHANGED')
                if before is not None:
                    self.fs.append(STATE + '/progress.jsonl', {'event': 'PREEXISTING', 'path': path,
                                    'object': before}, self.guard)
                    continue
                self.fs.append(STATE + '/progress.jsonl', {'event': 'INTENT', 'path': path}, self.guard)
                made = self.fs.exclusive(path, b, spec['mode'], self.guard)
                self.fs.append(STATE + '/progress.jsonl', {'event': 'CREATED', 'path': path,
                    'object': {k: v for k, v in made.items() if k != 'raw'}}, self.guard)
            final = self.inventory()
            need(all(x is not None for x in final.values()), 'INCOMPLETE_CODE_INSTALLATION')
            result = {'schema': 'r16.source19-native-code-admission.result.v1',
                      'status': 'READONLY_CODE_INSTALLED_EXACT', 'host': self.host,
                      'nativeIntentHash': digest(ch), 'originalObjectSha256': CATALOG,
                      'supplementSha256': self.supplement_hash, 'after': final,
                      'completedAt': self.wall(), 'source19': self.source(),
                      'productionBusinessChanged': False, 'signaturesIssued': 0,
                      'serviceActionIssued': False, 'ownerIdentityChanged': False,
                      'humanIdentityConfirmed': False, 'readonlyCapabilityExecuted': False,
                      'businessAcceptance': False}
            self.write('result.json', result)
            return result
        finally:
            os.close(fd)

    def journal(self):
        intent = self.fs.inspect(STATE + '/intent.json', [0o600])
        need(intent is not None, 'MISSING_ORIGINAL_INSTALL_INTENT')
        original = parse(intent['raw'])
        ch = original['challenge']
        need(ch['host'] == self.host and ch['originalObjectSha256'] == CATALOG
             and ch['supplementSha256'] == self.supplement_hash and ch['action'] == 'install'
             and original['nativeIntentHash'] == digest(ch)
             and ch['targets'] == {p: s for p, (s, _) in self.targets.items()},
             'INSTALL_INTENT_BINDING_DRIFT')
        r = self.fs.inspect(STATE + '/progress.jsonl', [0o600])
        need(r is not None and (r['raw'] == b'' or r['raw'].endswith(b'\n')), 'TORN_OR_MISSING_JOURNAL')
        records, pending, done = [], None, set()
        for line in r['raw'].splitlines():
            row = parse(line)
            p, event = row['path'], row['event']
            need(p in self.targets, 'JOURNAL_SCOPE_DRIFT')
            if event == 'INTENT':
                need(pending is None and p not in done, 'JOURNAL_ORDER_DRIFT')
                pending = p
            elif event in ('CREATED', 'PREEXISTING'):
                need(p not in done and (pending == p if event == 'CREATED' else pending is None),
                     'JOURNAL_ORDER_DRIFT')
                done.add(p)
                pending = None
                obj, expected = row['object'], self.targets[p][0]
                need(obj['sha256'] == expected['sha256']
                     and obj['identity']['bytes'] == expected['bytes']
                     and obj['identity']['mode'] == expected['mode']
                     and obj['identity']['uid'] == self.fs.uid
                     and obj['identity']['gid'] == self.fs.gid
                     and obj['identity']['nlink'] == 1
                     and (ch['before'][p] is None if event == 'CREATED' else ch['before'][p] == obj),
                     'JOURNAL_OBJECT_BINDING_DRIFT')
            else:
                raise ValueError('JOURNAL_EVENT_REFUSED')
            records.append(row)
        need(pending is None, 'UNRESOLVED_EFFECT_INTENT_READBACK_ONLY')
        return records

    def readback(self):
        # Never creates state, grants, locks or missing receipts.
        current = self.inventory()
        i = self.fs.inspect(STATE + '/intent.json', [0o600])
        if i is None:
            try:
                d, _ = self.fs.parent(STATE + '/intent.json')
            except FileNotFoundError:
                partial = False
            else:
                os.close(d)
                partial = True
            return {'status': 'PARTIAL_AUDIT_NO_INTENT_READBACK_REQUIRED' if partial else 'NO_INTENT_READBACK_ONLY', 'targets': current,
                    'authority': False, 'businessAcceptance': False}
        records = self.journal()
        r = self.fs.inspect(STATE + '/result.json', [0o600])
        status = 'PARTIAL_READBACK_REQUIRED'
        if r:
            receipt = parse(r['raw'])
            need(receipt['host'] == self.host and receipt['originalObjectSha256'] == CATALOG
                 and receipt['supplementSha256'] == self.supplement_hash
                 and receipt['nativeIntentHash'] == parse(i['raw'])['nativeIntentHash'], 'RESULT_BINDING_DRIFT')
            if receipt['after'] == current and len([x for x in records if x['event'] != 'INTENT']) == len(self.targets):
                status = 'READONLY_CODE_INSTALLED_EXACT_READBACK'
        w = self.fs.inspect(STATE + '/withdraw-intent.json', [0o600])
        if w:
            status = 'WITHDRAWAL_ATTEMPT_READBACK_REQUIRED'
            wr = self.fs.inspect(STATE + '/withdraw-result.json', [0o600])
            if wr:
                value = parse(wr['raw'])
                need(value['host'] == self.host and value['originalObjectSha256'] == CATALOG,
                     'WITHDRAW_RESULT_BINDING_DRIFT')
                for row in records:
                    if row['event'] == 'CREATED':
                        a = self.fs.inspect(STATE + '/archive' + row['path'])
                        expected = value['archived'].get(row['path'])
                        need(current[row['path']] is None and a is not None
                             and {k: v for k, v in a.items() if k != 'raw'} == expected,
                             'ARCHIVE_RESULT_DRIFT')
                status = 'OWN_CREATED_CODE_ARCHIVED_READBACK'
        return {'status': status, 'targets': current, 'journalRecords': len(records),
                'authority': False, 'businessAcceptance': False}

    def withdraw_inventory(self):
        need(self.fs.inspect(STATE + '/withdraw-intent.json') is None,
             'WITHDRAW_ALREADY_ATTEMPTED_READBACK_ONLY')
        records = self.journal()
        # Do not withdraw after any uncertain target effect, even when another
        # object happens to match its expected bytes.
        created = [r for r in records if r['event'] == 'CREATED']
        for row in created:
            current = self.fs.inspect(row['path'])
            need(current is not None and {k: v for k, v in current.items() if k != 'raw'} == row['object'],
                 'CREATED_OBJECT_DRIFT')
            need(self.fs.inspect(STATE + '/archive' + row['path']) is None, 'ARCHIVE_ALREADY_PRESENT_READBACK_ONLY')
        return created

    def withdraw(self, unused):
        self.guard()
        ch = self.grant['challenge']
        need(ch['action'] == 'withdraw', 'WITHDRAW_SCOPE_REQUIRED')
        need(self.inventory() == ch['before'], 'WITHDRAW_TARGET_CHANGED')
        created = self.withdraw_inventory()
        unused()
        fd = self.lock(False)
        try:
            self.write('withdraw-intent.json', {'challenge': ch, 'acceptedAt': self.grant['acceptedAt'],
                       'expiresAt': self.grant['expiresAt'], 'created': created})
            self.fs.exclusive(STATE + '/withdraw-progress.jsonl', b'', 0o600, self.guard, 0o700)
            archived = {}
            for row in created:
                unused()
                p = row['path']
                current = self.fs.inspect(p)
                need(current is not None and {k: v for k, v in current.items() if k != 'raw'} == row['object'],
                     'CREATED_OBJECT_DRIFT')
                self.fs.append(STATE + '/withdraw-progress.jsonl', {'event': 'ARCHIVE_INTENT', 'path': p}, self.guard)
                a = self.fs.archive(p, STATE + '/archive' + p, current, self.guard)
                archived[p] = {k: v for k, v in a.items() if k != 'raw'}
                self.fs.append(STATE + '/withdraw-progress.jsonl', {'event': 'ARCHIVED', 'path': p,
                               'object': archived[p]}, self.guard)
            result = {'schema': 'r16.source19-native-code-admission.withdraw-result.v1',
                      'status': 'OWN_CREATED_CODE_ARCHIVED_HISTORY_RETAINED',
                      'host': self.host, 'originalObjectSha256': CATALOG,
                      'supplementSha256': self.supplement_hash, 'nativeIntentHash': digest(ch),
                      'archived': archived, 'completedAt': self.wall(),
                      'neverUsedClaimed': False,
                      'serviceActionIssued': False, 'businessAcceptance': False}
            self.write('withdraw-result.json', result)
            return result
        finally:
            os.close(fd)


def source19(fs, host):
    """Narrow public, accepted-envelope projection; no secret or ledger reads."""
    p = '/run/r16-owner/public-config.json' if host == LOCAL else '/etc/r16-cloud/public-config.json'
    a = '/var/lib/r16-owner/configuration/state.json' if host == LOCAL else '/var/lib/r16-cloud/authority/state.json'
    pub_record, accepted = fs.inspect(p, [0o600, 0o644]), fs.inspect(a, [0o600])
    need(pub_record is not None and accepted is not None, 'SOURCE19_PROTECTED_PROJECTION_REQUIRED')
    pub, wrapper = parse(pub_record['raw']), parse(accepted['raw'])
    need(digest(pub) == PUB and digest(pub['grant']) == GRANT and wrapper['schema'] == 1,
         'SOURCE19_PUBLIC_BASELINE_DRIFT')
    body = wrapper['data']
    if host == LOCAL:
        need(body['kind'] == 'r16.owner.configuration.v1' and body['connected'] is True
             and body['activeGrantId'] == pub['grant']['body']['id']
             and body.get('replacement') is None, 'SOURCE19_OWNER_DRIFT')
        delivery = body['delivery']['envelope']
        need(body['delivery']['revision'] == 19 and body['delivery']['hash'] ==
             digest({'publicConfig': pub, 'control': delivery['body']['control'],
                     'connectionNonce': body.get('connectionNonce', 0)}), 'SOURCE19_CACHE_DRIFT')
    else:
        need(body['kind'] == 'r16.cloud-publication.v1', 'SOURCE19_CLOUD_DRIFT')
        delivery = body['accepted']
    need(digest(delivery) == DELIVERY and delivery['body']['revision'] == 19
         and delivery['body']['publicConfig'] == pub, 'SOURCE19_ACCEPTED_DELIVERY_DRIFT')
    return {'configurationRevision': 19, 'publicConfigSha256': PUB,
            'acceptedDeliverySha256': DELIVERY, 'grantSha256': GRANT}


def no_current_users():
    """Refuse withdrawal if any other process visibly references this code.

    No argv, environment, maps, FD contents or process identities are disclosed.
    This is code-only withdrawal; it is never permission to stop a process.
    """
    own = os.getpid()
    try:
        Path('/var/lib/r16-maintenance/source19-native-transition-r1').lstat()
    except FileNotFoundError:
        pass
    else:
        raise ValueError('CODE_USE_STATE_PRESENT_NO_WITHDRAWAL')
    for directory in Path('/proc').iterdir():
        if not directory.name.isdecimal() or int(directory.name) == own:
            continue
        try:
            maps = (directory / 'maps').read_bytes()
            need(not any(p.encode() in maps for p in (ROOT, HELPER)),
                 'CODE_CURRENTLY_REFERENCED_NO_WITHDRAWAL')
            for fd in (directory / 'fd').iterdir():
                try:
                    link = os.readlink(fd)
                except FileNotFoundError:
                    continue
                need(not any(link == p or link.startswith(p + '/') for p in (ROOT, HELPER)),
                     'CODE_CURRENTLY_REFERENCED_NO_WITHDRAWAL')
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            raise ValueError('PROCESS_USAGE_UNPROVEN_NO_WITHDRAWAL')


def main():
    # The loader has held and verified every byte before executing this module.
    import native_guard
    packet = globals()['SEALED_PACKET']
    mode, host = globals()['MODE'], globals()['HOST']
    need(os.getuid() == os.geteuid() == 0 and socket.gethostname() == host, 'FIXED_ROOT_HOST_REQUIRED')
    need(mode in ('describe', 'review', 'install', 'readback', 'withdraw'), 'MODE_REFUSED')
    fs = FS()
    boot = lambda: Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    engine = Admission(packet, host, fs, lambda: native_guard.native_root_context(host),
                       lambda: source19(fs, host), boot)
    if mode == 'describe':
        print(raw({'targets': {p: s for p, (s, _) in engine.targets.items()},
                   'auditScope': audit_scope(engine.targets), 'authority': False}).decode())
        return 0
    if mode == 'readback':
        print(raw(engine.readback()).decode())
        return 0
    action = 'withdraw' if mode == 'withdraw' else 'install'
    ch = engine.review(action)
    print(raw(ch).decode(), flush=True)
    if mode == 'review':
        print('REVIEW_ONLY_NO_AUTHORITY_CREATED', flush=True)
        return 0
    verb = 'ARCHIVE_EXACT_NEW_CODE' if action == 'withdraw' else 'INSTALL_READONLY_CODE'
    print('只准入上述准确只读代码及独立审计对象；不启停、不签发、不改业务。', flush=True)
    if action == 'withdraw':
        print('归档可能使只读预检失败；已持有的只读代码可能继续运行。未声称代码从未使用，不向进程发信号。', flush=True)
    print('本人准确输入：' + verb + ' ' + ('CLOUD' if host == CLOUD else 'LOCAL') + ' ' + digest(ch), flush=True)
    print('> ', end='', flush=True)
    line = __import__('sys').stdin.readline(256)
    need(0 < len(line) <= 160 and line.endswith('\n'), 'COMPLETE_NATIVE_INTENT_LINE_REQUIRED')
    typed = line[:-1]
    engine.accept(ch, typed)
    result = engine.withdraw(no_current_users) if action == 'withdraw' else engine.install()
    print(raw(result).decode(), flush=True)
    return 0
