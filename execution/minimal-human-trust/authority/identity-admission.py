#!/usr/bin/python3
"""HOST_ADMIN_CUSTODY admission. Default is descriptive; no import/path/key fallback.

The foreground pkexec entry admits one fixed oneshot. That oneshot creates two
Ed25519 keys in memory and seals them through systemd-creds stdin. This proves
key consistency and explicit local administrator custody, NOT Human-exclusive
possession, civil identity, enrollment, installation or production acceptance.
"""
import argparse
import base64
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import socket
import stat
import subprocess
import sys
import time

LIB = '/usr/lib/minimal-human-trust'
SCRIPT = LIB + '/authority/identity-admission.py'
WRAPPER = LIB + '/packaging/minimal-human-trust-identity-admission'
UNIT = 'minimal-human-trust-identity-admission.service'
UNIT_PATH = '/etc/systemd/system/' + UNIT
POLICY = '/usr/share/polkit-1/actions/org.jenn.r16.minimal-human-trust.identity-admission.policy'
FREEZE = '/etc/minimal-human-trust/identity-admission-code.json'
SOURCE = '/etc/minimal-human-trust/identity-key-source.json'
STATE = '/var/lib/minimal-human-trust/identity-admission'
CREDENTIAL_DIR = '/etc/credstore.encrypted/minimal-human-trust'
TARGETS = {role: CREDENTIAL_DIR + '/' + name + '.cred' for role, name in
           (('human', 'human-approval-key'), ('enrollment', 'enrollment-signing-key'))}
NAMES = {'human': 'human-approval-key', 'enrollment': 'enrollment-signing-key'}
MODEL = 'HOST_ADMIN_CUSTODY_NOT_HUMAN_EXCLUSIVE'
HOST = 'jenn-System-Product-Name'
PUB = '56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec'
DELIVERY = 'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9'
RELEASE = '70e76c7e563c0fda544f3e55ab2b2c98a4889912f3a5c45e39019738bc1fdffb'
GRANT = '00ac437d66143e627132975555d06396d69ff69616f630d19e3622627e15c5e6'
PUBLIC_PATH = '/run/r16-owner/public-config.json'
OWNER_PATH = '/var/lib/r16-owner/configuration/state.json'
MAX_MS = 300000
CODE_FILES = {SCRIPT, WRAPPER, UNIT_PATH, POLICY}


def need(ok, code):
    if not ok:
        raise ValueError(code)


def canonical(value):
    # Node key ordering is UTF-16, not Python Unicode code-point ordering.
    def ordered(v):
        if isinstance(v, dict):
            return {k: ordered(v[k]) for k in sorted(v, key=lambda x: x.encode('utf-16-be', 'surrogatepass'))}
        if isinstance(v, list):
            return [ordered(x) for x in v]
        need(v is None or type(v) in (str, int, bool), 'CANONICAL_VALUE_REFUSED')
        if type(v) is int:
            need(abs(v) <= 9007199254740991, 'NON_SAFE_INTEGER')
        return v
    return json.dumps(ordered(value), ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(canonical(value))


def now():
    return time.time_ns() // 1000000


def b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode()


def unb64(value):
    need(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_-]+', value), 'PUBLIC_ENCODING_REFUSED')
    return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))


def identity(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_gid, st.st_nlink,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def secure_read(name, limit=1048576, mode=None):
    p = Path(name)
    for q in reversed(p.parents):
        st = q.lstat()
        need(stat.S_ISDIR(st.st_mode) and st.st_uid == 0 and not st.st_mode & 0o022, 'ROOT_PARENT_REFUSED')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        st = os.fstat(fd)
        need(stat.S_ISREG(st.st_mode) and st.st_uid == 0 and st.st_gid == 0 and st.st_nlink == 1
             and not st.st_mode & 0o022 and st.st_size <= limit
             and (mode is None or stat.S_IMODE(st.st_mode) == mode), 'ROOT_FILE_REFUSED')
        raw = bytearray()
        while len(raw) <= limit:
            part = os.read(fd, min(65536, limit + 1 - len(raw)))
            if not part:
                break
            raw.extend(part)
        need(len(raw) == st.st_size and identity(st) == identity(os.fstat(fd)) == identity(p.lstat()), 'ROOT_FILE_CHANGED')
        return bytes(raw)
    finally:
        os.close(fd)


def checked_command(argv, data=None, timeout=20):
    try:
        r = subprocess.run(argv, input=data, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           timeout=timeout, check=False, env={'PATH': '/usr/bin:/bin', 'LANG': 'C'}, close_fds=True)
    except subprocess.TimeoutExpired:
        raise ValueError('FIXED_COMMAND_TIMEOUT') from None
    need(r.returncode == 0 and len(r.stdout) <= 1048576, 'FIXED_COMMAND_FAILED')
    return r.stdout


def start_ticks(pid):
    raw = Path('/proc/' + str(pid) + '/stat').read_text()
    return raw[raw.rfind(')') + 2:].split()[19]


def verify_signed(envelope, public_key, schema):
    from cryptography.hazmat.primitives.serialization import load_der_public_key
    need(set(envelope) == {'body', 'signature'} and envelope['body'].get('schema') == schema, 'SIGNED_SCOPE_REFUSED')
    load_der_public_key(unb64(public_key)).verify(unb64(envelope['signature']), b'R16-SIGNED\0' + canonical(envelope['body']))
    return envelope['body']


def source19(read=secure_read):
    pub = json.loads(read(PUBLIC_PATH))
    configuration = json.loads(read(OWNER_PATH, 32 * 1024 * 1024))['data']
    need(digest(pub) == PUB and digest(pub['release']) == RELEASE and digest(pub['grant']) == GRANT, 'SOURCE19_PUBLIC_DRIFT')
    release = verify_signed(pub['release'], pub['releasePublicKey'], 'r16.release.v1')
    grant = verify_signed(pub['grant'], pub['issuerPublicKey'], 'r16.workspace.v1')
    d = configuration['delivery']
    need(configuration['kind'] == 'r16.owner.configuration.v1' and d['revision'] == 19
         and digest(d['envelope']) == DELIVERY, 'SOURCE19_DELIVERY_DRIFT')
    body = verify_signed(d['envelope'], pub['issuerPublicKey'], 'r16.configuration-delivery.v1')
    need(body['revision'] == 19 and body['publicConfig'] == pub and body['control'] ==
         {'grantId': 'r16-projects-daily', 'grantVersion': 1, 'status': 'ACTIVE', 'connectRequested': True}
         and release['id'] == 'r16-daily-20261015-r15-app-recovery-r6' and grant['id'] == 'r16-projects-daily'
         and grant['version'] == 1, 'SOURCE19_SCOPE_DRIFT')
    need(d['hash'] == digest({'publicConfig': pub, 'control': body['control'], 'connectionNonce': configuration.get('connectionNonce', 0)}), 'OWNER_CACHE_DRIFT')
    need(pub['issuerPublicKey'] != pub['releasePublicKey'], 'ROOT_KEYS_NOT_DISTINCT')
    return {'publicConfigDigest': PUB, 'acceptedDeliveryHash': DELIVERY, 'revision': 19,
            'issuerPublicKey': pub['issuerPublicKey'], 'releasePublicKey': pub['releasePublicKey']}


def code_freeze():
    raw = secure_read(FREEZE)
    f = json.loads(raw)
    need(f.get('schema') == 'mht.identity-admission-code-freeze.v1' and set(f['files']) == CODE_FILES
         and re.fullmatch(r'[a-f0-9]{40}', f.get('sourceCommit', '')), 'IDENTITY_CODE_FREEZE_REQUIRED')
    for p, h in f['files'].items():
        need(re.fullmatch(r'[a-f0-9]{64}', h) and sha(secure_read(p)) == h, 'IDENTITY_CODE_DRIFT')
    need(str(Path(__file__)) == SCRIPT, 'FIXED_ENTRY_REQUIRED')
    return sha(raw)


def native_identity():
    need(os.getuid() == os.geteuid() == 0 and os.environ.get('PKEXEC_UID') == '1000'
         and socket.gethostname() == HOST, 'LOCAL_JENN_ROOT_REQUIRED')
    need(re.search(r'^ID=ubuntu$', Path('/etc/os-release').read_text(), re.M), 'UBUNTU_REQUIRED')
    user = pwd.getpwuid(1000)
    need(user.pw_name == 'jenn' and user.pw_gid == 1000, 'JENN_SUBJECT_REQUIRED')
    rows = [os.fstat(i) for i in range(3)]
    path = os.ttyname(0)
    need(re.fullmatch(r'/dev/pts/[0-9]+', path) and all(os.isatty(i) for i in range(3)), 'ACTUAL_PTY_REQUIRED')
    key = lambda s: (s.st_dev, s.st_ino, s.st_rdev, s.st_uid, s.st_gid, stat.S_IMODE(s.st_mode))
    need(all(stat.S_ISCHR(s.st_mode) and s.st_uid == 1000 and stat.S_IMODE(s.st_mode) in (0o600, 0o620)
             and key(s) == key(rows[0]) for s in rows), 'PTY_IDENTITY_REFUSED')
    # Open each ancestor without following aliases; /dev/tty itself is only a
    # controlling-terminal proof, never mistaken for the actual pts inode.
    d = os.open('/dev', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        pts = os.open('pts', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=d)
        try:
            fd = os.open(path.rsplit('/', 1)[1], os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=pts)
            try:
                need(key(os.fstat(fd)) == key(rows[0]), 'PTY_NODE_DRIFT')
            finally:
                os.close(fd)
        finally:
            os.close(pts)
    finally:
        os.close(d)
    tty = os.open('/dev/tty', os.O_RDWR | os.O_NOFOLLOW)
    try:
        need(all(os.tcgetpgrp(i) == os.getpgrp() == os.tcgetpgrp(tty) for i in range(3)), 'NATIVE_FOREGROUND_REQUIRED')
        session = checked_command(['/usr/bin/loginctl', 'show-user', '1000', '-p', 'Display', '--value']).decode().strip()
        need(re.fullmatch(r'[A-Za-z0-9_-]{1,64}', session), 'LOCAL_GUI_REQUIRED')
        text = checked_command(['/usr/bin/loginctl', 'show-session', session, '-p', 'User', '-p', 'Name', '-p', 'Active',
                                '-p', 'Remote', '-p', 'Type', '-p', 'Class', '-p', 'State']).decode()
        props = dict(x.split('=', 1) for x in text.splitlines())
        need(all(props.get(k) == v for k, v in {'User': '1000', 'Name': 'jenn', 'Active': 'yes', 'Remote': 'no',
                 'Class': 'user', 'State': 'active'}.items()) and props.get('Type') in ('x11', 'wayland'), 'LOCAL_ACTIVE_GUI_REQUIRED')
        return tty, {'uid': 1000, 'subject': 'local-human:1000', 'session': session,
                     'pid': os.getpid(), 'startTicks': start_ticks(os.getpid()), 'tty': path}
    except BaseException:
        os.close(tty)
        raise


def check_authority(a, clock=now):
    need(a.get('schema') == 'mht.identity-native-authority.v1' and a.get('custodyModel') == MODEL
         and type(a.get('acceptedAt')) is int and type(a.get('expiresAt')) is int
         and a['expiresAt'] - a['acceptedAt'] == MAX_MS and a['acceptedAt'] <= clock() < a['expiresAt']
         and re.fullmatch(r'[0-9]{1,20}', a.get('acceptedMonotonicNs', ''))
         and 0 <= time.monotonic_ns() - int(a['acceptedMonotonicNs']) < MAX_MS * 1000000
         and a.get('bootId') == Path('/proc/sys/kernel/random/boot_id').read_text().strip()
         and re.fullmatch(r'[a-f0-9]{32}', a.get('nonce', '')) and a.get('targets') == TARGETS,
         'IDENTITY_AUTHORITY_EXPIRED_OR_INVALID')


def challenge(facts, freeze_hash, actor):
    return {'schema': 'mht.identity-native-challenge.v1', 'title': 'HOST_ADMIN_CUSTODY', 'custodyModel': MODEL,
            'nonce': secrets.token_hex(16), 'source': facts, 'codeFreezeHash': freeze_hash, 'actor': actor,
            'targets': TARGETS, 'validForMs': MAX_MS,
            'effects': ['GENERATE_TWO_ED25519_KEYS_IN_MEMORY', 'SEAL_TO_FIXED_SYSTEMD_CREDS_TARGETS',
                        'WRITE_PUBLIC_CUSTODY_SOURCE_AND_RECEIPT', 'RELOAD_MANAGER_AND_START_ONLY_IDENTITY_ONESHOT'],
            'notEnrollment': True, 'notHumanExclusivePossession': True, 'ownerUnchanged': True}


def approve_native(c):
    tty, actor = native_identity()
    try:
        need(actor == c['actor'], 'NATIVE_ACTOR_DRIFT')
        line = 'ADMIT HOST_ADMIN_CUSTODY ' + digest(c)
        message = ('将由本机管理员托管生成 Human 与独立 Enrollment 两把密钥，并密封到固定凭据目标。\n'
                   '这不是 Human 独占私钥持有证明，不登记身份、不签发 Release、不切换 Owner。\n'
                   '会重新加载 systemd 并启动一次专用密封服务；中途失败不会自动重新生成。\n'
                   + canonical(c).decode() + '\n本人批准请输入整行：\n' + line + '\n> ')
        os.write(tty, message.encode())
        response = bytearray()
        # A fixed 180s input bound; reading time does not consume the new permit.
        import select
        deadline = time.monotonic() + 180
        while len(response) < 256:
            remaining = deadline - time.monotonic()
            need(remaining > 0 and select.select([tty], [], [], remaining)[0], 'NATIVE_CONFIRMATION_TIMEOUT')
            b = os.read(tty, 1)
            need(bool(b), 'NATIVE_CONFIRMATION_CANCELLED')
            if b == b'\n':
                break
            response.extend(b)
        need(response.decode() == line, 'NATIVE_CONFIRMATION_CANCELLED')
        fd, again = native_identity()
        os.close(fd)
        need(again == actor, 'NATIVE_ACTOR_DRIFT')
        accepted = now()
        return {'schema': 'mht.identity-native-authority.v1', 'custodyModel': MODEL, 'nonce': c['nonce'],
                'challengeHash': digest(c), 'codeFreezeHash': c['codeFreezeHash'], 'source': c['source'],
                'actor': actor, 'targets': TARGETS, 'acceptedAt': accepted, 'expiresAt': accepted + MAX_MS,
                'acceptedMonotonicNs': str(time.monotonic_ns()),
                'bootId': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    finally:
        os.close(tty)


class FixedBackend:
    """Production paths are constants. Protocol tests inject a separate fake."""
    def __init__(self, clock=now):
        self.clock = clock
        self.authority = None

    def effects_guard(self):
        need(self.authority is not None, 'NATIVE_AUTHORITY_REQUIRED')
        check_authority(self.authority, self.clock)

    def exists(self, p):
        return os.path.lexists(p)

    def load(self, name):
        need(name in ('authority', 'keygen-intent', 'result', 'launch-intent', 'reload-intent',
                      'human-intent', 'human-result', 'enrollment-intent', 'enrollment-result'), 'RECORD_SCOPE_REFUSED')
        p = STATE + '/' + name + '.json'
        return json.loads(secure_read(p, mode=0o600)) if self.exists(p) else None

    def mkdir(self, p, mode):
        path = Path(p)
        missing = []
        while not path.exists():
            missing.append(path)
            path = path.parent
        for q in (path, *path.parents):
            st = q.lstat()
            need(stat.S_ISDIR(st.st_mode) and st.st_uid == st.st_gid == 0 and not st.st_mode & 0o022, 'ROOT_PARENT_REFUSED')
        for q in reversed(missing):
            self.effects_guard()
            q.mkdir(mode=mode)
            self.effects_guard()
            q.chmod(mode)
        if p in (STATE, CREDENTIAL_DIR):
            need(stat.S_IMODE(Path(p).lstat().st_mode) == 0o700, 'PRIVATE_DIRECTORY_MODE_REQUIRED')

    def put(self, path, raw, guard=lambda: None):
        # Durable fixed pending name is never overwritten. A crash/pending file
        # requires readback; no private material is ever passed to this method.
        self.mkdir(str(Path(path).parent), 0o700)
        pending = path + '.pending'
        self.effects_guard()
        guard()
        fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            at = 0
            while at < len(raw):
                self.effects_guard()
                guard()
                at += os.write(fd, raw[at:])
            os.fsync(fd)
        finally:
            os.close(fd)
        libc = ctypes.CDLL(None, use_errno=True)
        self.effects_guard()
        guard()
        need(libc.renameat2(-100, pending.encode(), -100, path.encode(), 1) == 0, 'EXCLUSIVE_PUBLICATION_REFUSED')
        d = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(d)
        finally:
            os.close(d)

    def record(self, name, value):
        need(name in ('authority', 'keygen-intent', 'result', 'launch-intent', 'reload-intent',
                      'human-intent', 'human-result', 'enrollment-intent', 'enrollment-result'), 'RECORD_SCOPE_REFUSED')
        self.put(STATE + '/' + name + '.json', canonical(value))

    def fresh(self, a):
        check_authority(a)
        need(code_freeze() == a['codeFreezeHash'] and source19() == a['source'], 'ADMITTED_SOURCE_DRIFT')
        need(start_ticks(a['actor']['pid']) == a['actor']['startTicks'], 'NATIVE_FRONTEND_GONE')
        check_authority(a)
        self.authority = a

    def seal(self, role, private, a):
        self.fresh(a)
        encrypted = checked_command(['/usr/bin/systemd-creds', 'encrypt', '--with-key=host', '--name=' + NAMES[role], '-', '-'], private)
        self.fresh(a)
        opened = checked_command(['/usr/bin/systemd-creds', 'decrypt', '--name=' + NAMES[role], '-', '-'], encrypted)
        return encrypted, bytearray(opened)

    def publish(self, role, encrypted, a):
        self.fresh(a)
        self.put(TARGETS[role], encrypted, lambda: check_authority(a))

    def publish_source(self, value, a):
        self.fresh(a)
        self.put(SOURCE, canonical(value), lambda: check_authority(a))

    def historical(self, r):
        need(sha(secure_read(SOURCE, mode=0o600)) == r['publicSourceSha256'], 'CUSTODY_PUBLIC_SOURCE_DRIFT')
        for role in TARGETS:
            need(sha(secure_read(TARGETS[role], mode=0o600)) == r['ciphertextSha256'][role], 'SEALED_CREDENTIAL_DRIFT')
        return dict(r, historicalReadOnly=True)


def keypair():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    key = Ed25519PrivateKey.generate()
    private = bytearray(key.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    public = b64(key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo))
    return private, public


def pair_proof(private, public, message):
    from cryptography.hazmat.primitives.serialization import load_der_private_key, load_der_public_key
    key = load_der_private_key(bytes(private), None)
    signature = key.sign(canonical(message))
    load_der_public_key(unb64(public)).verify(signature, canonical(message))
    return b64(signature)


def work(b, a, generate=keypair, clock=now):
    result = b.load('result')
    if result:
        return b.historical(result)
    need(b.load('keygen-intent') is None, 'PARTIAL_SEAL_NO_REGENERATION_READBACK_REQUIRED')
    check_authority(a, clock)
    b.fresh(a)
    for p in (*TARGETS.values(), SOURCE):
        need(not b.exists(p), 'IDENTITY_TARGET_ALREADY_EXISTS')
    b.record('keygen-intent', {'authorityHash': digest(a), 'nonce': a['nonce'], 'custodyModel': MODEL})
    rows = {}
    encrypted_hashes = {}
    roots = {a['source']['issuerPublicKey'], a['source']['releasePublicKey']}
    for role in ('human', 'enrollment'):
        private = opened = None
        try:
            check_authority(a, clock)
            b.fresh(a)
            private, public = generate()
            need(public not in roots, 'FOUR_PUBLIC_KEYS_MUST_BE_DISTINCT')
            roots.add(public)
            msg = {'schema': 'mht.host-admin-keypair-proof.v1', 'role': role, 'nonce': a['nonce'],
                   'authorityHash': digest(a), 'publicKey': public, 'custodyModel': MODEL}
            proof = pair_proof(private, public, msg)
            b.record(role + '-intent', {'publicKey': public, 'target': TARGETS[role], 'authorityHash': digest(a)})
            encrypted, opened = b.seal(role, private, a)
            need(pair_proof(opened, public, msg) == proof, 'SEALED_KEYPAIR_DRIFT')
            check_authority(a, clock)
            b.publish(role, encrypted, a)
            encrypted_hashes[role] = sha(encrypted)
            rows[role] = {'publicKey': public, 'target': TARGETS[role], 'ciphertextSha256': sha(encrypted),
                          'keypairProof': {'message': msg, 'signature': proof}, 'origin': 'HOST_ADMIN_GENERATED_IN_ADMITTED_ONESHOT'}
            b.record(role + '-result', rows[role])
        finally:
            for buffer in (private, opened):
                if buffer is not None:
                    buffer[:] = b'\0' * len(buffer)
    need(len(roots) == 4, 'FOUR_PUBLIC_KEYS_MUST_BE_DISTINCT')
    public_source = {'schema': 'mht.identity-key-source.v1', 'title': 'HOST_ADMIN_CUSTODY', 'custodyModel': MODEL,
                     'humanExclusivePossession': False, 'civilIdentityVerified': False, 'enrolled': False,
                     'subject': 'local-human:1000', 'uid': 1000, 'authorityHash': digest(a), 'source': a['source'],
                     'keys': rows, 'nativeIntent': {'nonce': a['nonce'], 'challengeHash': a['challengeHash'],
                     'acceptedAt': a['acceptedAt'], 'expiresAt': a['expiresAt']}}
    check_authority(a, clock)
    b.publish_source(public_source, a)
    b.fresh(a)
    check_authority(a, clock)
    result = {'schema': 'mht.identity-admission-result.v1', 'status': 'HOST_ADMIN_CUSTODY_SEALED_NOT_ENROLLED',
              'custodyModel': MODEL, 'authorityHash': digest(a), 'publicSourceSha256': digest(public_source),
              'publicKeys': {k: v['publicKey'] for k, v in rows.items()}, 'ciphertextSha256': encrypted_hashes,
              'completedAt': clock(), 'enrolled': False, 'ownerChanged': False, 'businessAcceptance': False}
    b.record('result', result)
    return result


def description():
    return {'schema': 'mht.identity-admission-description.v1', 'title': 'HOST_ADMIN_CUSTODY', 'custodyModel': MODEL,
            'defaultEffects': 0, 'targets': TARGETS, 'publicSource': SOURCE, 'unit': UNIT,
            'requiresRealNativeConfirmation': True, 'humanExclusivePossession': False, 'enrolled': False,
            'productionSigning': 0, 'ownerChanged': False}


def worker_admission(b):
    need(os.getuid() == os.geteuid() == 0 and socket.gethostname() == HOST, 'FIXED_ROOT_HOST_REQUIRED')
    need(Path('/proc/self/cgroup').read_text().strip() == '0::/system.slice/' + UNIT, 'FIXED_ONESHOT_REQUIRED')
    props = dict(x.split('=', 1) for x in checked_command(['/usr/bin/systemctl', 'show', UNIT, '-p', 'MemorySwapMax', '-p', 'LimitCORE']).decode().splitlines())
    need(props.get('MemorySwapMax') == props.get('LimitCORE') == '0', 'NO_SWAP_NO_CORE_REQUIRED')
    a = b.load('authority')
    b.fresh(a)
    host_key_metadata()
    need(ctypes.CDLL(None).prctl(4, 0, 0, 0, 0) == 0, 'NO_DUMP_REQUIRED')
    return a


def host_key_metadata():
    st = Path('/var/lib/systemd/credential.secret').lstat()  # Metadata only; never read the host secret.
    need(stat.S_ISREG(st.st_mode) and st.st_uid == st.st_gid == 0 and st.st_nlink == 1
         and stat.S_IMODE(st.st_mode) == 0o600, 'EXISTING_SYSTEMD_HOST_KEY_REQUIRED')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', choices=('describe', 'preflight', 'admit', 'service', 'status'), default='describe')
    args = parser.parse_args(argv)
    if args.action == 'describe':
        return description()
    need(os.getuid() == os.geteuid() == 0, 'ROOT_REQUIRED')
    freeze_hash = code_freeze()
    b = FixedBackend()
    if args.action == 'preflight':
        facts = source19()
        host_key_metadata()
        return {'status': 'IDENTITY_ADMISSION_READONLY', 'codeFreezeHash': freeze_hash, 'source': facts,
                'targetsAbsent': all(not b.exists(x) for x in (*TARGETS.values(), SOURCE)), 'effects': 0}
    if args.action == 'status':
        result = b.load('result')
        return b.historical(result) if result else {'status': 'PARTIAL_READBACK_REQUIRED' if b.exists(STATE) else 'NOT_ADMITTED', 'effects': 0}
    if args.action == 'service':
        a = worker_admission(b)
        b.effects_guard()
        fd = os.open(STATE + '/worker.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            st = os.fstat(fd)
            need(stat.S_ISREG(st.st_mode) and st.st_uid == st.st_gid == 0 and st.st_nlink == 1
                 and stat.S_IMODE(st.st_mode) == 0o600, 'WORKER_LOCK_REFUSED')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return work(b, a)
        finally:
            os.close(fd)
    tty, actor = native_identity()
    os.close(tty)
    facts = source19()
    host_key_metadata()
    need(not b.exists(STATE) and all(not b.exists(x) for x in (*TARGETS.values(), SOURCE)), 'ADMISSION_ALREADY_STARTED_NO_REPEAT')
    a = approve_native(challenge(facts, freeze_hash, actor))
    b.fresh(a)
    b.mkdir(STATE, 0o700)
    b.record('authority', a)
    b.mkdir(CREDENTIAL_DIR, 0o700)
    check_authority(a)
    b.record('reload-intent', {'authorityHash': digest(a)})
    b.fresh(a)
    checked_command(['/usr/bin/systemctl', 'daemon-reload'])
    b.record('launch-intent', {'authorityHash': digest(a), 'unit': UNIT})
    b.fresh(a)
    # Foreground remains alive while the worker validates that exact native PID.
    checked_command(['/usr/bin/systemctl', 'start', UNIT], timeout=180)
    result = b.load('result')
    need(result is not None, 'SEALING_RESULT_UNPROVEN_NO_RETRY')
    return b.historical(result)


if __name__ == '__main__':
    try:
        print(json.dumps(main(), sort_keys=True, separators=(',', ':')))
    except Exception as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r'[A-Z0-9_]+', str(error)) else 'IDENTITY_ADMISSION_REFUSED'
        print(json.dumps({'status': 'REFUSED_OR_PARTIAL_NO_RETRY', 'code': code, 'businessAcceptance': False}))
        sys.exit(78)
