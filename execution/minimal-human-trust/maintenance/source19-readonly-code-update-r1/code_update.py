"""Exact three-object public-code update; no business or service operations.

The prior admission implementation is reused byte-for-byte as filesystem/source
projection support, never as its old install/withdraw entry. Partial updates
cannot resume. Restoration is a separately confirmed, current-state operation.
"""
import fcntl
import os
import secrets
import socket
import time
from pathlib import Path
import support_admission as s

HEAD = '381a09d4094fabbb5c33452fa55bb0e87659d56f'
CAPSULE = 'dd3df0a9fe82f6d4aa5cafac28488081da9033ce49e308b7e1f29d6df1bc7657'
CATALOG = 'ea2e3fa09be82bf63405287ac129e838d7a21a296af98de5e2c01008a48256db'
SUPPORT = '6333b19b9e2a446cfe21860a7383db74109a45189034df55afd43ec14c89bace'
STATE = '/var/lib/r16-maintenance/source19-readonly-schema-fix-r1/' + CAPSULE
ORDER = (s.ROOT + '/runtime/maintenance/source19-native-transition-r1/checkpoint_public.mjs',
         s.ROOT + '/ENTRY_FREEZE.json', s.PIN)
need, raw, sha, parse, digest = s.need, s.raw, s.sha, s.parse, s.digest


def public(record):
    return None if record is None else {k: v for k, v in record.items() if k != 'raw'}


def same_object(a, b):
    # rename changes ctime; ownership/mode/inode/content/mtime must all survive.
    return a is not None and b is not None and a['sha256'] == b['sha256'] and all(
        a['identity'][k] == b['identity'][k] for k in a['identity'] if k != 'ctimeNs')


def slot(kind, i):
    need(kind in ('stage', 'archive', 'reverted') and type(i) is int and 0 <= i < 3,
         'FIXED_SLOT_REQUIRED')
    return STATE + '/' + kind + '/' + str(i)


def audit_scope():
    return {'root': STATE, 'directoryMode': 0o700, 'uid': 0, 'gid': 0,
            'files': {STATE + '/' + n: 0o600 for n in
                      ('intent.json', '.lock', 'progress.jsonl', 'result.json')},
            'slots': {slot(k, i): (0o644 if i == 0 else 0o600)
                      for k in ('stage', 'archive', 'reverted') for i in range(3)},
            'restoreAttemptFiles': {'pathPattern': STATE + '/restore/<current-challenge-sha256>/'
                                   + '{intent.json,progress.jsonl,result.json}',
                                   'mode': 0o600, 'directoryMode': 0o700},
            'oldLockReferenceOnly': s.STATE + '/.lock',
            'historyPreserved': True, 'authority': False}


def targets(packet, host):
    need(sha(packet['support_admission.py']) == SUPPORT and
         sha(packet['native_guard.py']) == s.GUARD, 'SUPPORT_SOURCE_DRIFT')
    previous = {'bundle/' + n[len('previous/'):]: b for n, b in packet.items()
                if n.startswith('previous/')}
    previous['native_guard.py'] = packet['native_guard.py']
    previous['SUPPLEMENTAL_NATIVE_ENTRY_REVIEW_R1.json'] = packet['legacy_supplement.json']
    old = s.target_bytes(previous, host)
    c = packet['bundle/CODE_ADMISSION_CANDIDATE.json']
    need(sha(c) == CATALOG, 'NEW_CATALOG_DRIFT')
    obj = parse(c)
    need(obj['sourceHead'] == HEAD and obj['capsuleHash'] == CAPSULE and
         sha(packet['bundle/root/ENTRY_FREEZE.json']) == CAPSULE,
         'NEW_CAPSULE_DRIFT')
    specs = obj['targets'] | (obj['cloudOnlyTargets'] if host == s.CLOUD else {})
    need(specs.keys() == old.keys(), 'TARGET_SET_DRIFT')
    new = {}
    for p, spec in specs.items():
        if p.startswith(s.ROOT + '/'):
            name = 'bundle/root/' + p[len(s.ROOT) + 1:]
        elif p == s.PIN:
            name = 'bundle/installed-entry-pin.json'
        else:
            name = 'bundle/cloud-policy/' + ('r16-source19-native-transition-r1-rpc'
                    if p == s.HELPER else 'r16-source19-native-transition-r1.sudoers')
        b = packet[name]
        need(spec['uid'] == spec['gid'] == 0 and len(b) == spec['bytes'] and
             sha(b) == spec['sha256'] and spec['mode'] == old[p][0]['mode'], 'NEW_TARGET_DRIFT')
        new[p] = (spec, b)
    need({p for p in old if old[p] != new[p]} == set(ORDER), 'THREE_OBJECT_SCOPE_REQUIRED')
    return previous, old, new


class Update:
    def __init__(self, packet, host, fs, native, source, boot,
                 wall=time.time, mono=time.monotonic, fault=lambda _: None):
        self.packet, self.host, self.fs = packet, host, fs
        self.native, self.source, self.boot = native, source, boot
        self.wall, self.mono, self.fault = wall, mono, fault
        previous, self.old, self.new = targets(packet, host)
        self.legacy = s.Admission(previous, host, fs, native, source, boot, wall, mono)
        self.grant = None
        self.held_new_lock = None
        self.bound = None
        review = parse(packet['review.json']);self.review_object = review
        need(review['sourceHead'] == HEAD and review['oldCapsuleHash'] == s.CAPSULE and
             review['newCapsuleHash'] == CAPSULE and review['auditScope'] == audit_scope() and
             review['changes'] == [{'path': p, 'before': self.old[p][0],
                                    'after': self.new[p][0]} for p in ORDER] and
             review['supportSources'] == {n: sha(packet[n]) for n in
                 ('code_update.py', 'support_admission.py', 'native_guard.py', 'launch_code_update.py')},
             'UPDATE_REVIEW_SCOPE_DRIFT')

    def inspect(self, path):
        return self.fs.inspect(path)

    def inventory(self):
        self.fs.namespace(s.ROOT, self.old)
        return {p: public(self.inspect(p)) for p in sorted(self.old)}

    def state_absent(self):
        try:
            fd, _ = self.fs.parent(STATE + '/intent.json')
        except FileNotFoundError:
            return
        os.close(fd)
        raise ValueError('UPDATE_ALREADY_ATTEMPTED_READBACK_ONLY')

    def devices(self):
        paths = list(ORDER) + [slot(k, i) for k in ('stage', 'archive', 'reverted')
                              for i in range(3)] + [STATE + '/intent.json']
        out = {p: self.fs.device(p) for p in paths}
        need(len(set(out.values())) == 1, 'SAME_FILESYSTEM_REQUIRED')
        return out

    def old_lock(self):
        r = self.fs.inspect(s.STATE + '/.lock', [0o600])
        need(r is not None and r['raw'] == b'', 'ORIGINAL_LOCK_REQUIRED')
        return public(r)

    def original(self):
        r = self.fs.inspect(STATE + '/intent.json', [0o600])
        need(r is not None, 'COMPLETE_UPDATE_INTENT_REQUIRED')
        v = parse(r['raw']);ch = v['challenge']
        need(ch['action'] == 'update' and ch['host'] == self.host and
             ch['oldCapsuleHash'] == s.CAPSULE and ch['newCapsuleHash'] == CAPSULE and
             ch['reviewSha256'] == sha(self.packet['review.json']) and
             v['nativeIntentHash'] == digest(ch) and ch['auditScope'] == audit_scope() and
             ch['targets'] == {p: self.new[p][0] for p in sorted(self.new)} and
             ch['source19'] == self.source(), 'ORIGINAL_INTENT_BINDING_DRIFT')
        need(ch['before'].keys() == self.old.keys() and all(ch['before'][p] is not None and
             ch['before'][p]['sha256'] == self.old[p][0]['sha256'] and
             ch['before'][p]['identity']['bytes'] == self.old[p][0]['bytes'] and
             ch['before'][p]['identity']['mode'] == self.old[p][0]['mode'] and
             ch['before'][p]['identity']['uid'] == self.fs.uid and
             ch['before'][p]['identity']['gid'] == self.fs.gid and
             ch['before'][p]['identity']['nlink'] == 1 for p in self.old),
             'ORIGINAL_PREIMAGE_SCOPE_DRIFT')
        return v

    def observation(self):
        intent = self.original();before = intent['challenge']['before']
        current = self.inventory()
        need(all(current[p] == before[p] for p in self.old if p not in ORDER),
             'UNCHANGED_OBJECT_DRIFT')
        journal = self.fs.inspect(STATE + '/progress.jsonl', [0o600])
        rows = [] if journal is None else self.lines(journal['raw'])
        made = {}
        for row in rows:
            if row['event'] == 'DONE' and row['operation'].startswith('stage-'):
                i = int(row['operation'][6:]);need(0 <= i < 3 and i not in made,
                                                'STAGE_JOURNAL_DRIFT')
                a = row['object'];spec = self.new[ORDER[i]][0]
                need(a['sha256'] == spec['sha256'] and a['identity']['bytes'] == spec['bytes']
                     and a['identity']['mode'] == spec['mode'] and
                     a['identity']['uid'] == self.fs.uid and a['identity']['gid'] == self.fs.gid
                     and a['identity']['nlink'] == 1, 'STAGE_IDENTITY_DRIFT')
                made[i] = a
        slots = {slot(k, i): public(self.inspect(slot(k, i)))
                 for k in ('stage', 'archive', 'reverted') for i in range(3)}
        for i, p in enumerate(ORDER):
            old_places = [current[p], slots[slot('archive', i)]]
            need(sum(same_object(a, before[p]) for a in old_places) == 1,
                 'ORIGINAL_OBJECT_LOCATION_UNPROVEN')
            if slots[slot('archive', i)] is not None:
                need(same_object(slots[slot('archive', i)], before[p]), 'FOREIGN_ARCHIVE_OBJECT')
            if current[p] is not None and not same_object(current[p], before[p]):
                need(i in made and same_object(current[p], made[i]), 'FOREIGN_TARGET_OBJECT')
            if i in made:
                places = [current[p], slots[slot('stage', i)], slots[slot('reverted', i)]]
                need(sum(same_object(a, made[i]) for a in places) == 1,
                     'NEW_OBJECT_LOCATION_UNPROVEN')
                for k in ('stage', 'reverted'):
                    a = slots[slot(k, i)]
                    need(a is None or same_object(a, made[i]), 'FOREIGN_NEW_OBJECT')
            else:
                # A torn first stage cannot authorize adoption or mutation of
                # an unrecorded inode. Old targets must still be untouched.
                need(current[p] == before[p] and slots[slot('archive', i)] is None
                     and slots[slot('reverted', i)] is None, 'UNRECORDED_STAGE_EFFECT')
        return {'intentSha256': sha(self.inspect(STATE + '/intent.json')['raw']),
                'targets': current, 'slots': slots, 'stageObjects': {str(i): a for i, a in made.items()},
                'journalSha256': None if journal is None else journal['sha256']}

    @staticmethod
    def lines(b):
        need(b == b'' or b.endswith(b'\n'), 'TORN_JOURNAL_READBACK_REQUIRED')
        return [parse(line) for line in b.splitlines()]

    def review(self, action):
        need(action in ('update', 'restore'), 'FIXED_ACTION_REQUIRED')
        native, source = self.native(), self.source()
        if action == 'update':
            self.state_absent()
            rb = self.legacy.readback()
            need(rb['status'] == 'READONLY_CODE_INSTALLED_EXACT_READBACK',
                 'ORIGINAL_INSTALLATION_READBACK_REQUIRED')
            before = self.inventory()
            receipt = self.inspect(s.STATE + '/result.json')
            need(receipt is not None, 'ORIGINAL_INSTALL_RECEIPT_REQUIRED')
            observation = None
        else:
            observation = self.observation();before = observation['targets']
            receipt = self.inspect(s.STATE + '/result.json')
            need(receipt is not None, 'ORIGINAL_INSTALL_RECEIPT_REQUIRED')
        return {'schema': 'r16.source19-readonly-code-update.challenge.v1',
                'action': action, 'host': self.host, 'sourceHead': HEAD,
                'entrySourceHead': self.review_object['entrySourceHead'],
                'entrySources': self.review_object['supportSources'],
                'changedObjects': self.review_object['changes'],
                'oldCapsuleHash': s.CAPSULE, 'newCapsuleHash': CAPSULE,
                'reviewSha256': sha(self.packet['review.json']),
                'entryPacketSha256': globals().get('ENTRY_PACKET_SHA'),
                'heldPacketFileSha256': globals().get('HELD_PACKET_FILE_SHA'),
                'targets': {p: self.new[p][0] for p in sorted(self.new)},
                'before': before, 'observation': observation,
                'oldInstallReceiptSha256': receipt['sha256'], 'oldLock': self.old_lock(),
                'devices': self.devices(), 'auditScope': audit_scope(),
                'nativeContext': native, 'source19': source, 'bootId': self.boot(),
                'nonce': secrets.token_hex(16), 'validForMsFromAcceptance': 300000,
                'oldApprovalOrDeadlineReused': False, 'humanIdentityConfirmed': False,
                'businessAcceptance': False}

    def accept(self, ch, typed):
        verb = 'UPDATE_READONLY_CODE' if ch['action'] == 'update' else 'RESTORE_READONLY_CODE'
        need(typed == verb + ' ' + ('CLOUD' if self.host == s.CLOUD else 'LOCAL') +
             ' ' + digest(ch), 'EXACT_NATIVE_INTENT_CANCELLED')
        now, mono = self.wall(), self.mono()
        need(self.native() == ch['nativeContext'] and self.source() == ch['source19'] and
             self.boot() == ch['bootId'] and self.inventory() == ch['before'] and
             self.old_lock() == ch['oldLock'] and self.devices() == ch['devices'],
             'NATIVE_SOURCE_OR_OBJECT_CHANGED')
        need(ch['action'] != 'restore' or self.observation() == ch['observation'],
             'RESTORE_OBSERVATION_CHANGED')
        self.grant = {'challenge': ch, 'acceptedAt': now, 'expiresAt': now + 300,
                      'mono': mono, 'nativeIntentHash': digest(ch)}
        self.time_guard()

    def time_guard(self):
        g = self.grant
        need(g is not None and self.boot() == g['challenge']['bootId'], 'NATIVE_AUTHORITY_EXPIRED')
        now, mono = self.wall(), self.mono()
        need(g['acceptedAt'] <= now < g['expiresAt'] and 0 <= mono - g['mono'] < 300,
             'NATIVE_AUTHORITY_EXPIRED_NO_EXTENSION')

    def guard(self):
        self.time_guard();ch = self.grant['challenge']
        need(self.native() == ch['nativeContext'] and self.source() == ch['source19'] and
             self.old_lock() == ch['oldLock'] and self.devices() == ch['devices'],
             'NATIVE_SOURCE_OR_DEVICE_CHANGED')
        need(self.inspect(s.STATE + '/result.json')['sha256'] == ch['oldInstallReceiptSha256'],
             'ORIGINAL_INSTALL_RECEIPT_CHANGED')
        if self.held_new_lock is not None:
            need(public(self.inspect(STATE + '/.lock')) == self.held_new_lock, 'UPDATE_LOCK_CHANGED')
        need(all(public(self.inspect(p)) == ch['before'][p]
                 for p in self.old if p not in ORDER), 'UNCHANGED_OBJECT_DRIFT')
        self.time_guard()

    def write(self, path, b, mode=0o600):
        def write_guard():
            self.guard();self.verify_bound((path,));self.time_guard()
        write_guard();globals()['EFFECTS_STARTED'] = True
        return self.fs.exclusive(path, b, mode, write_guard, 0o700)

    def lock(self, path, expected):
        need(public(self.inspect(path)) == expected, 'LOCK_IDENTITY_DRIFT')
        d, n = self.fs.parent(path)
        try: fd = os.open(n, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=d)
        finally: os.close(d)
        try:
            need(s.identity(os.fstat(fd)) == expected['identity'], 'LOCK_IDENTITY_DRIFT')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            need(public(self.inspect(path)) == expected, 'LOCK_IDENTITY_DRIFT')
            return fd
        except BaseException:
            os.close(fd);raise

    def log(self, path, value):
        globals()['EFFECTS_STARTED'] = True
        def append_guard():
            self.guard();self.verify_bound();self.time_guard()
        self.fs.append(path, value, append_guard)

    def verify_bound(self, skip=()):
        if self.bound is not None:
            need(all(public(self.inspect(p)) == expected for p, expected in self.bound.items()
                     if p not in skip), 'CONFIRMED_OBJECT_IDENTITY_DRIFT')

    def create(self, log, operation, path, b, mode):
        self.verify_bound()
        self.log(log, {'event': 'INTENT', 'operation': operation, 'path': path})
        self.fault(operation + ':before')
        out = self.write(path, b, mode)
        if self.bound is not None:self.bound[path] = public(out)
        self.fault(operation + ':after')
        self.verify_bound()
        self.log(log, {'event': 'DONE', 'operation': operation, 'path': path, 'object': public(out)})
        return out

    def move(self, log, operation, src, dst, expected):
        self.guard();self.verify_bound()
        need(self.inspect(src) == expected and self.inspect(dst) is None, 'EXACT_RENAME_PREIMAGE_REQUIRED')
        self.log(log, {'event': 'INTENT', 'operation': operation, 'source': src,
                       'destination': dst, 'object': public(expected)})
        self.fault(operation + ':before')
        globals()['EFFECTS_STARTED'] = True
        def rename_guard():
            self.guard();self.verify_bound((src, dst))
            a, b = self.inspect(src), self.inspect(dst)
            if a is not None:
                need(a == expected and b is None, 'EXACT_RENAME_PREIMAGE_REQUIRED')
            else:
                need(same_object(public(b), public(expected)), 'EXACT_RENAME_RESULT_REQUIRED')
            self.time_guard()
        out = self.fs.archive(src, dst, expected, rename_guard)
        if self.bound is not None:
            self.bound[src] = None;self.bound[dst] = public(out)
        self.fault(operation + ':after')
        self.verify_bound()
        self.log(log, {'event': 'DONE', 'operation': operation, 'destination': dst,
                       'object': public(out)})
        return out

    def update(self):
        self.guard();ch = self.grant['challenge']
        need(ch['action'] == 'update', 'UPDATE_SCOPE_REQUIRED');self.state_absent()
        oldfd = self.lock(s.STATE + '/.lock', ch['oldLock']);newfd = None
        try:
            self.state_absent()
            need(self.inventory() == ch['before'] and self.review_original_receipt(ch),
                 'LOCKED_PREIMAGE_CHANGED')
            self.write(STATE + '/intent.json', raw(self.grant_record()) + b'\n')
            r = self.write(STATE + '/.lock', b'');newfd = self.lock(STATE + '/.lock', public(r));self.held_new_lock = public(r)
            log = STATE + '/progress.jsonl';self.write(log, b'')
            self.bound = dict(ch['before']) | {slot(k, i): None for k in ('stage','archive','reverted') for i in range(3)}
            self.verify_bound()
            stages = [self.create(log, 'stage-' + str(i), slot('stage', i),
                      self.new[p][1], self.new[p][0]['mode']) for i, p in enumerate(ORDER)]
            for i, p in enumerate(ORDER):
                before = self.inspect(p)
                need(public(before) == ch['before'][p], 'ORIGINAL_TARGET_CHANGED')
                self.move(log, 'archive-' + str(i), p, slot('archive', i), before)
                self.move(log, 'publish-' + str(i), slot('stage', i), p, stages[i])
            self.verify_bound()
            obs = self.observation()
            need(all(same_object(obs['targets'][p], public(stages[i]))
                     for i, p in enumerate(ORDER)), 'UPDATED_READBACK_FAILED')
            out = self.result('READONLY_CODE_UPDATED_EXACT', obs)
            self.write(STATE + '/result.json', raw(out) + b'\n');return out
        finally:
            if newfd is not None: os.close(newfd)
            os.close(oldfd)

    def review_original_receipt(self, ch):
        need(self.legacy.readback()['status'] == 'READONLY_CODE_INSTALLED_EXACT_READBACK',
             'ORIGINAL_INSTALLATION_READBACK_REQUIRED')
        return self.inspect(s.STATE + '/result.json')['sha256'] == ch['oldInstallReceiptSha256']

    def grant_record(self):
        return {k: v for k, v in self.grant.items() if k != 'mono'}

    def restore(self):
        self.guard();ch = self.grant['challenge']
        need(ch['action'] == 'restore', 'RESTORE_SCOPE_REQUIRED')
        oldfd = self.lock(s.STATE + '/.lock', ch['oldLock']);newfd = None
        try:
            r = self.fs.inspect(STATE + '/.lock', [0o600])
            need(r is not None and r['raw'] == b'', 'UPDATE_LOCK_REQUIRED')
            newfd = self.lock(STATE + '/.lock', public(r));self.held_new_lock = public(r)
            need(self.observation() == ch['observation'], 'LOCKED_RESTORE_OBSERVATION_CHANGED')
            self.bound = dict(ch['observation']['targets']) | dict(ch['observation']['slots'])
            self.verify_bound()
            attempt = STATE + '/restore/' + digest(ch)
            self.write(attempt + '/intent.json', raw(self.grant_record()) + b'\n')
            log = attempt + '/progress.jsonl';self.write(log, b'')
            before = self.original()['challenge']['before']
            for i, p in enumerate(ORDER):
                self.verify_bound()
                verified = self.observation()
                current = self.inspect(p)
                need(public(current) == verified['targets'][p], 'RESTORE_TARGET_CHANGED')
                if same_object(public(current), before[p]): continue
                if current is not None:
                    self.move(log, 'retire-' + str(i), p, slot('reverted', i), current)
                archived = self.inspect(slot('archive', i))
                need(same_object(public(archived), before[p]), 'ORIGINAL_ARCHIVE_CHANGED')
                self.move(log, 'restore-' + str(i), slot('archive', i), p, archived)
            self.verify_bound()
            obs = self.observation()
            need(all(same_object(obs['targets'][p], before[p]) for p in ORDER),
                 'RESTORED_READBACK_FAILED')
            out = self.result('ORIGINAL_READONLY_CODE_RESTORED_EXACT', obs)
            self.write(attempt + '/result.json', raw(out) + b'\n');return out
        finally:
            if newfd is not None: os.close(newfd)
            os.close(oldfd)

    def result(self, status, observation):
        return {'schema': 'r16.source19-readonly-code-update.result.v1', 'status': status,
                'host': self.host, 'nativeIntentHash': self.grant['nativeIntentHash'],
                'oldCapsuleHash': s.CAPSULE, 'newCapsuleHash': CAPSULE,
                'after': observation, 'source19': self.source(), 'completedAt': self.wall(),
                'oldApprovalOrDeadlineReused': False, 'serviceActionIssued': False,
                'signaturesIssued': 0, 'ownerIdentityChanged': False,
                'humanIdentityConfirmed': False, 'terminal': True, 'businessAcceptance': False}

    def readback(self):
        r = self.inspect(STATE + '/intent.json')
        if r is None:
            try:self.state_absent();status = 'NO_UPDATE_INTENT_READBACK_ONLY'
            except ValueError:status = 'PARTIAL_AUDIT_NO_INTENT_READBACK_REQUIRED'
            return {'status': status, 'targets': self.inventory(),
                    'authority': False, 'businessAcceptance': False}
        obs = self.observation();v = self.inspect(STATE + '/result.json')
        status = 'PARTIAL_UPDATE_READBACK_REQUIRED'
        if v is not None:
            receipt = parse(v['raw'])
            need(receipt['host'] == self.host and receipt['newCapsuleHash'] == CAPSULE and
                 receipt['nativeIntentHash'] == self.original()['nativeIntentHash'], 'RESULT_BINDING_DRIFT')
            if receipt['after'] == obs: status = 'READONLY_CODE_UPDATED_EXACT_READBACK'
        before = self.original()['challenge']['before']
        if all(same_object(obs['targets'][p], before[p]) for p in ORDER):
            status = 'ORIGINAL_CODE_PRESENT_READBACK_ONLY'
        return {'status': status, 'observation': obs, 'authority': False,
                'businessAcceptance': False}


def main():
    import native_guard
    host, mode, packet = globals()['HOST'], globals()['MODE'], globals()['SEALED_PACKET']
    need(os.getuid() == os.geteuid() == 0 and socket.gethostname() == host,
         'FIXED_ROOT_HOST_REQUIRED')
    need(mode in ('describe', 'review', 'update', 'readback', 'restore'), 'FIXED_MODE_REQUIRED')
    fs = s.FS()
    engine = Update(packet, host, fs, lambda: native_guard.native_root_context(host),
                    lambda: s.source19(fs, host),
                    lambda: Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    if mode == 'describe':
        return {'auditScope': audit_scope(), 'authority': False, 'businessAcceptance': False}
    if mode == 'readback': return engine.readback()
    action = 'restore' if mode == 'restore' else 'update'
    ch = engine.review(action);print(raw(ch).decode(), flush=True)
    if mode == 'review':
        print('REVIEW_ONLY_NO_AUTHORITY_CREATED', flush=True);return 0
    print('仅替换或恢复列明的三处只读代码；原件与全部审计保留。', flush=True)
    print('三文件不是整体原子替换；期间只读预检可暂不可用，已持有的旧只读代码可继续。', flush=True)
    print('不启停、不签发、不改配置、Owner或账本；未知结果先readback，不重跑update。', flush=True)
    verb = 'RESTORE_READONLY_CODE' if action == 'restore' else 'UPDATE_READONLY_CODE'
    print('本人准确输入：' + verb + ' ' + ('CLOUD' if host == s.CLOUD else 'LOCAL') +
          ' ' + digest(ch), flush=True)
    print('> ', end='', flush=True)
    line = __import__('sys').stdin.readline(256)
    need(0 < len(line) <= 160 and line.endswith('\n'), 'COMPLETE_NATIVE_INTENT_LINE_REQUIRED')
    engine.accept(ch, line[:-1])
    return engine.restore() if action == 'restore' else engine.update()
