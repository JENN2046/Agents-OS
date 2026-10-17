#!/usr/bin/python3
"""Fixed-role OS quiescence adapter. Production admission belongs to the installer.

No public JSON/boolean can mint a permit. The CLI intentionally cannot stop any
service before the independently implemented protected installer is integrated.
No ledger, credential, database, environment or business protocol is read here.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import socket
import stat
import subprocess
import sys
import time
from dataclasses import dataclass, field
from types import MappingProxyType

LOCAL = 'jenn-System-Product-Name'
CLOUD = 'VM-0-12-ubuntu'
ROLE_HOST = {'r16-owner.service': LOCAL, 'r16-native.service': LOCAL,
             'r16-app.service': CLOUD, 'r16-bridge.service': CLOUD}
STOP_ORDER = ('r16-app.service', 'r16-native.service', 'r16-bridge.service', 'r16-owner.service')
START_ORDER = ('r16-owner.service', 'r16-bridge.service', 'r16-native.service', 'r16-app.service')
REMOTE_HELPER = '/usr/libexec/r16-maintenance-os-r5'
SSH = ('/usr/bin/ssh', '-F', '/dev/null', '-T', '-o', 'BatchMode=yes', '-o', 'IdentityAgent=none',
       '-o', 'IdentitiesOnly=yes', '-i', '/home/jenn/.ssh/TXY_159_75_139_246_ed25519',
       '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
       '-o', 'UserKnownHostsFile=/etc/r16-owner/ssh_known_hosts',
       '-o', 'GlobalKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=8',
       '-o', 'ClearAllForwardings=yes', 'ubuntu@159.75.139.246')
PROPERTIES = ('Id', 'ActiveState', 'SubState', 'MainPID', 'ControlPID', 'ControlGroup',
              'NRestarts', 'Restart', 'RefuseManualStart', 'DropInPaths', 'NeedDaemonReload',
              'SendSIGKILL', 'KillSignal')
CGROUP_ROOT = '/sys/fs/cgroup'
FENCE_ROOT = '/run/r16-maintenance-os-r5'
BLOCKED_START_PATH = FENCE_ROOT + '/business-start-is-not-authorized'
DROPIN_NAME = '90-r16-maintenance-os-r5.conf'
ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'SYSTEMD_PAGER': 'cat', 'SYSTEMD_COLORS': '0'}
CODE_PINS = {
    'r16-owner.service': {'/usr/lib/r16-owner/authority/owner_daemon.py': '85da39438068cfc6b80f3c0743dee8fa920e3fa7c1ac0ba628f1a40e6f413e9b'},
    'r16-native.service': {'/opt/r16/trust/trusted-launcher.mjs': '4583ddd8c1fca94881b5a05919ae59a173743682ae6d121c05bc6ffd10885e27', '/opt/r16/releases/r16-daily-20261012-r15/host/native-runner.mjs': '0f30ebe457764265b2b8dad630f1a68f6e7251911c94da8a48362c6a0bfe089c'},
    'r16-app.service': {'/opt/r16/trust/cloud-trusted-launcher.mjs': '5e4963c4078636b4c1bd9de22e12589734bfecc5c77f452f2017009921ff6231', '/opt/r16/releases/r16-daily-20261012-r15/app/app-runner.mjs': '9fa13d0fe708d62e8ec34db680212d9d1857014c4e08bbaf1b00c60c8f602737'},
    'r16-bridge.service': {'/opt/r16/trust/cloud-trusted-launcher.mjs': '5e4963c4078636b4c1bd9de22e12589734bfecc5c77f452f2017009921ff6231', '/opt/r16/releases/r16-daily-20261012-r15/bridge/bridge-runner.mjs': 'ac3d043618b6bdec7170820f3baa2f9bfdc4a6035fcf12bc0caab86f643dc584'},
}
_BRAND = object()


class Refused(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def need(value, code):
    if not value:
        raise Refused(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_unit(unit):
    need(unit in ROLE_HOST, 'FIXED_UNIT_REQUIRED')


def dropin(unit):
    validate_unit(unit)
    return '/run/systemd/system/' + unit + '.d/' + DROPIN_NAME


def fence_bytes(plan_hash):
    need(re.fullmatch('[a-f0-9]{64}', plan_hash) is not None, 'PLAN_HASH_REQUIRED')
    return ('# Exact admitted maintenance plan ' + plan_hash + '\n[Unit]\nRefuseManualStart=yes\nConditionPathExists=' + BLOCKED_START_PATH + '\n[Service]\nRestart=no\n').encode()


@dataclass(frozen=True)
class Snapshot:
    unit: str
    host: str
    active: str
    sub: str
    main_pid: int
    control_pid: int
    main_start: int
    control_start: int
    members: tuple
    restarts: int
    code_hashes: tuple
    fence_hash: str | None
    fence_effective: bool
    daemon_reload_needed: bool = False
    send_sigkill: str | None = None
    kill_signal: str | None = None

    def graceful_only(self):
        # systemctl show represents SIGTERM numerically as KillSignal=15.
        # Missing/unknown metadata is not evidence of a safe stop policy.
        return self.send_sigkill == 'no' and self.kill_signal == '15'

    def process_identity(self):
        return (self.main_pid, self.main_start, self.control_pid, self.control_start)

    def stopped(self):
        return self.active in ('inactive', 'failed') and self.main_pid == 0 and self.control_pid == 0 and not self.members


@dataclass(eq=False)
class _Permit:
    """Internal installer handoff; never constructed from caller JSON or a bool.

    The future protected installer must hold the private brand after authentic
    native admission and durable INTENT. No CLI path currently mints it.
    """
    brand: object
    plan_hash: str
    expires_at: float
    baseline: dict
    native_scope: str = 'STOP_FIXED_ROLES_PRESERVE_ALL_LEDGERS'
    state: str = 'NEW'
    touched: list = field(default_factory=list)
    stop_attempts: list = field(default_factory=list)
    stopped: list = field(default_factory=list)
    def __post_init__(self):
        self.baseline = MappingProxyType(dict(self.baseline))

    def check(self, now, states):
        need(self.brand is _BRAND and self.native_scope == 'STOP_FIXED_ROLES_PRESERVE_ALL_LEDGERS', 'PROTECTED_INSTALLER_ADMISSION_REQUIRED')
        need(isinstance(self.plan_hash, str) and re.fullmatch('[a-f0-9]{64}', self.plan_hash), 'PLAN_HASH_REQUIRED')
        need(set(self.baseline) == set(ROLE_HOST) and all(isinstance(x, Snapshot) and x.unit == u and x.host == ROLE_HOST[u] for u, x in self.baseline.items()), 'BRANDED_BASELINE_REQUIRED')
        need(now < self.expires_at, 'ADMISSION_EXPIRED')
        need(self.state in states, 'ONCE_OPERATION_ALREADY_USED')


def production_admission(*_args, **_kwargs):
    raise Refused('PROTECTED_INSTALLER_ADMISSION_REQUIRED')


class RealBackend:
    """Actual fixed OS commands. Tests never instantiate this for mutation."""
    def __init__(self):
        self.host = socket.gethostname()
        need(self.host in (LOCAL, CLOUD), 'HOST_REFUSED')
        self._admitted = None

    def _root(self):
        need(os.geteuid() == 0 and self.host == socket.gethostname(), 'ROOT_REQUIRED')

    def _bind_admitted(self, permit):
        self._root()
        need(isinstance(permit, _Permit) and permit.brand is _BRAND, 'PROTECTED_INSTALLER_ADMISSION_REQUIRED')
        self._admitted = permit

    def _require_admitted(self, plan_hash):
        self._root()
        p = self._admitted
        need(isinstance(p, _Permit) and p.brand is _BRAND and p.plan_hash == plan_hash and
             p.state in ('FENCING', 'STOPPING', 'ABORT_RESTORING'), 'PROTECTED_INSTALLER_ADMISSION_REQUIRED')
        need(p.state == 'ABORT_RESTORING' or time.monotonic() < p.expires_at, 'ADMISSION_EXPIRED')

    def _run(self, argv, timeout=10):
        self._root()
        result = subprocess.run(tuple(argv), input=b'', stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=ENV, timeout=timeout, check=False)
        need(result.returncode == 0 and len(result.stdout) <= 262144, 'OS_COMMAND_FAILED')
        return result.stdout

    def _remote(self, unit, operation, plan_hash=''):
        validate_unit(unit)
        need(self.host == LOCAL and ROLE_HOST[unit] == CLOUD, 'REMOTE_SCOPE_REFUSED')
        need(operation in ('inspect', 'fence', 'unfence', 'stop', 'start'), 'REMOTE_OPERATION_REFUSED')
        # A protected fixed remote helper/admission is installed separately. No
        # generic sudo Python/shell permission or new SSH identity is requested.
        if operation != 'inspect': self._require_admitted(plan_hash)
        command = shlex.join(('/usr/bin/sudo', '-n', REMOTE_HELPER, operation, unit, plan_hash))
        try:
            return json.loads(self._run((*SSH, command), timeout=15))
        except Refused:
            raise
        except Exception:
            raise Refused('REMOTE_READBACK_REFUSED') from None

    def _local(self, unit):
        validate_unit(unit)
        need(ROLE_HOST[unit] == self.host, 'WRONG_ROLE_HOST')

    def _read_regular(self, filename):
        current = Path('/')
        for part in Path(filename).parts[1:-1]:
            current /= part
            info = current.lstat()
            need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022, 'OS_PATH_REFUSED')
        fd = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            before = os.fstat(fd)
            need(stat.S_ISREG(before.st_mode) and before.st_uid == 0 and before.st_nlink == 1 and not before.st_mode & 0o022 and before.st_size <= 262144, 'OS_FILE_REFUSED')
            raw = os.read(fd, 262145)
            after = os.fstat(fd)
            fields = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            need(len(raw) == before.st_size and fields(before) == fields(after), 'OS_FILE_DRIFT')
            return raw
        finally:
            os.close(fd)

    def _start(self, pid, expected_cgroup):
        if not pid:
            return 0
        try:
            raw = Path('/proc/%d/stat' % pid).read_bytes()
            ticks = int(raw[raw.rfind(b')') + 2:].split()[19])
            groups = Path('/proc/%d/cgroup' % pid).read_text().splitlines()
            need(any(line.split(':', 2)[-1] == expected_cgroup for line in groups), 'PID_CGROUP_DRIFT')
            return ticks
        except Refused:
            raise
        except Exception:
            raise Refused('PID_IDENTITY_UNAVAILABLE') from None

    def _members(self, unit):
        root = Path(CGROUP_ROOT + '/system.slice/' + unit)
        if not root.exists():
            return ()
        members = set()
        for directory, subdirs, _ in os.walk(root, followlinks=False):
            need(not Path(directory).is_symlink() and all(not (Path(directory) / n).is_symlink() for n in subdirs), 'CGROUP_SYMLINK')
            for value in (Path(directory) / 'cgroup.procs').read_text().split():
                need(value.isdigit(), 'CGROUP_CONTENT_REFUSED')
                members.add(int(value))
            need(len(members) <= 8192, 'CGROUP_CAPACITY_REFUSED')
        return tuple(sorted(members))

    def inspect(self, unit, plan_hash=''):
        validate_unit(unit)
        if ROLE_HOST[unit] != self.host:
            raw = self._remote(unit, 'inspect', plan_hash)
            try:
                raw['members'] = tuple(raw['members']);raw['code_hashes'] = tuple(tuple(x) for x in raw['code_hashes'])
                value = Snapshot(**raw)
                need(value.unit == unit and value.host == ROLE_HOST[unit], 'REMOTE_IDENTITY_REFUSED')
                need(value.graceful_only(), 'UNSAFE_MANAGER_STOP_POLICY')
                return value
            except Refused:
                raise
            except Exception:
                raise Refused('REMOTE_READBACK_REFUSED') from None
        self._root();self._local(unit)
        raw = self._run(('/usr/bin/systemctl', 'show', unit, '--property=' + ','.join(PROPERTIES))).decode()
        data = dict(line.split('=', 1) for line in raw.splitlines() if '=' in line)
        need(data.get('Id') == unit, 'UNIT_IDENTITY_REFUSED')
        need(data.get('SendSIGKILL') == 'no' and data.get('KillSignal') == '15', 'UNSAFE_MANAGER_STOP_POLICY')
        pid, control = int(data['MainPID']), int(data['ControlPID'])
        group = '/system.slice/' + unit
        need(data['ControlGroup'] == group or data['ControlGroup'] == '' and not pid and not control, 'UNIT_CGROUP_DRIFT')
        code_hashes = tuple((path, sha(self._read_regular(path))) for path in CODE_PINS[unit])
        need(dict(code_hashes) == CODE_PINS[unit], 'CODE_PIN_DRIFT')
        main_start, control_start = self._start(pid, group), self._start(control, group)
        members = self._members(unit)
        if pid: need(pid in members, 'MAIN_PID_OUTSIDE_CGROUP')
        if control: need(control in members, 'CONTROL_PID_OUTSIDE_CGROUP')
        need(main_start == self._start(pid, group) and control_start == self._start(control, group), 'PID_REUSED_DURING_INSPECTION')
        fence_hash = None
        try:
            fence_hash = sha(self._read_regular(dropin(unit)))
        except FileNotFoundError:
            pass
        object_path = '/org/freedesktop/systemd1/unit/' + unit.replace('-', '_2d').replace('.', '_2e')
        condition_record = json.loads(self._run(('/usr/bin/busctl', '--system', '--json=short', 'get-property',
                                               'org.freedesktop.systemd1', object_path,
                                               'org.freedesktop.systemd1.Unit', 'Conditions')))
        need(condition_record.get('type') == 'a(sbbsi)' and isinstance(condition_record.get('data'), list), 'CONDITION_METADATA_REFUSED')
        conditions = condition_record['data']
        need(all(isinstance(x, list) and len(x) == 5 and isinstance(x[0], str) and type(x[1]) is bool and
                 type(x[2]) is bool and isinstance(x[3], str) and type(x[4]) is int for x in conditions), 'CONDITION_METADATA_REFUSED')
        # Last-result fields are historical. The configured mandatory, unnegated
        # false path condition, not ConditionResult, prevents future admission.
        mandatory_guard = any(x[0] == 'ConditionPathExists' and x[1] is False and x[2] is False and x[3] == BLOCKED_START_PATH for x in conditions)
        expected = sha(fence_bytes(plan_hash)) if plan_hash else None
        effective = bool(expected and fence_hash == expected and data.get('DropInPaths', '').split() and
                         data['DropInPaths'].split()[-1] == dropin(unit) and
                         data.get('Restart') == 'no' and data.get('RefuseManualStart') == 'yes' and
                         data.get('NeedDaemonReload') == 'no' and mandatory_guard and not Path(BLOCKED_START_PATH).exists())
        return Snapshot(unit, self.host, data['ActiveState'], data['SubState'], pid, control, main_start,
                        control_start, members, int(data['NRestarts']), code_hashes, fence_hash, effective,
                        data.get('NeedDaemonReload') != 'no', data['SendSIGKILL'], data['KillSignal'])

    def _mkdir_root(self, directory, mode):
        path = Path(directory)
        path.mkdir(mode=mode, parents=True, exist_ok=True)
        cursor = Path('/')
        for part in path.parts[1:]:
            cursor /= part
            value = cursor.lstat()
            need(stat.S_ISDIR(value.st_mode) and not stat.S_ISLNK(value.st_mode) and value.st_uid == 0 and not value.st_mode & 0o022, 'FENCE_DIRECTORY_REFUSED')

    def fence(self, unit, plan_hash):
        validate_unit(unit)
        self._require_admitted(plan_hash)
        if ROLE_HOST[unit] != self.host:
            return self._remote(unit, 'fence', plan_hash)
        self._root();self._local(unit)
        self._mkdir_root(FENCE_ROOT, 0o700)
        need(not Path(BLOCKED_START_PATH).exists(), 'START_GUARD_ALREADY_EXISTS')
        path = dropin(unit);self._mkdir_root(str(Path(path).parent), 0o755)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        try:
            raw = fence_bytes(plan_hash)
            offset = 0
            while offset < len(raw): offset += os.write(fd, raw[offset:])
            os.fsync(fd)
        finally:
            os.close(fd)
        self._run(('/usr/bin/systemctl', 'daemon-reload'))
        need(self.inspect(unit, plan_hash).fence_effective, 'FENCE_NOT_EFFECTIVE')

    def unfence(self, unit, plan_hash):
        validate_unit(unit)
        self._require_admitted(plan_hash)
        if ROLE_HOST[unit] != self.host:
            return self._remote(unit, 'unfence', plan_hash)
        self._root();self._local(unit)
        need(self._read_regular(dropin(unit)) == fence_bytes(plan_hash), 'FOREIGN_FENCE_REFUSED')
        os.unlink(dropin(unit))
        self._run(('/usr/bin/systemctl', 'daemon-reload'))
        need(self.inspect(unit, plan_hash).fence_hash is None, 'FENCE_REMOVAL_UNCONFIRMED')

    def stop(self, unit, plan_hash):
        validate_unit(unit)
        self._require_admitted(plan_hash)
        current = self.inspect(unit, plan_hash)
        need(current.graceful_only(), 'UNSAFE_MANAGER_STOP_POLICY')
        need(current.fence_effective, 'STOP_REQUIRES_EFFECTIVE_FENCE')
        if ROLE_HOST[unit] != self.host:
            return self._remote(unit, 'stop', plan_hash)
        self._root();self._local(unit)
        self._run(('/usr/bin/systemctl', 'stop', '--no-block', unit))

    def start(self, unit, plan_hash):
        validate_unit(unit)
        self._require_admitted(plan_hash)
        if ROLE_HOST[unit] != self.host:
            return self._remote(unit, 'start', plan_hash)
        self._root();self._local(unit)
        need(self.inspect(unit, plan_hash).fence_hash is None, 'START_WHILE_FENCED_REFUSED')
        self._run(('/usr/bin/systemctl', 'start', '--no-block', unit))


class Controller:
    def __init__(self, backend=None, now=time.monotonic, sleep=time.sleep):
        self.backend = RealBackend() if backend is None else backend
        self.now = now
        self.sleep = sleep

    def baseline(self, plan_hash=''):
        if plan_hash: need(re.fullmatch('[a-f0-9]{64}', plan_hash) is not None, 'PLAN_HASH_REQUIRED')
        result = {unit: self.backend.inspect(unit, plan_hash) if plan_hash else self.backend.inspect(unit) for unit in ROLE_HOST}
        for unit, row in result.items():
            need(row.unit == unit and row.host == ROLE_HOST[unit] and row.active in ('active', 'inactive', 'failed'), 'BASELINE_UNSTABLE')
            need(row.graceful_only(), 'UNSAFE_MANAGER_STOP_POLICY')
            need(not row.fence_hash and not row.daemon_reload_needed, 'PREEXISTING_FENCE_OR_UNIT_DRIFT')
        return result

    def _same_original(self, original, observed):
        need(original.graceful_only() and observed.graceful_only(), 'UNSAFE_MANAGER_STOP_POLICY')
        need(observed.unit == original.unit and observed.host == original.host and observed.process_identity() == original.process_identity(), 'PID_OR_STARTTIME_DRIFT')
        need(observed.code_hashes == original.code_hashes and observed.restarts == original.restarts, 'CODE_OR_RESTART_DRIFT')
        need(observed.active == original.active and observed.sub == original.sub, 'UNIT_STATE_DRIFT')

    def quiesce(self, permit, graceful_seconds=120, settle_seconds=1):
        need(isinstance(permit, _Permit), 'PROTECTED_INSTALLER_ADMISSION_REQUIRED')
        permit.check(self.now(), ('NEW',))
        need(1 <= graceful_seconds <= 120 and 0 < settle_seconds <= 5, 'TIME_BOUND_REFUSED')
        if isinstance(self.backend, RealBackend): self.backend._bind_admitted(permit)
        permit.state = 'FENCING'
        try:
            for unit in ROLE_HOST:
                permit.check(self.now(), ('FENCING',))
                current = self.backend.inspect(unit, permit.plan_hash)
                self._same_original(permit.baseline[unit], current)
                permit.touched.append(unit)  # Before effect; lost reply is uncertain.
                self.backend.fence(unit, permit.plan_hash)
                need(self.backend.inspect(unit, permit.plan_hash).fence_effective, 'FENCE_NOT_EFFECTIVE')
            permit.state = 'STOPPING'
            for unit in STOP_ORDER:
                permit.check(self.now(), ('STOPPING',))
                current = self.backend.inspect(unit, permit.plan_hash)
                self._same_original(permit.baseline[unit], current)
                need(current.fence_effective, 'FENCE_DRIFT')
                if current.stopped():
                    continue
                permit.stop_attempts.append(unit)  # Never blindly retry this effect.
                self.backend.stop(unit, permit.plan_hash)
                end = self.now() + graceful_seconds
                while True:
                    current = self.backend.inspect(unit, permit.plan_hash)
                    need(current.graceful_only(), 'UNSAFE_MANAGER_STOP_POLICY')
                    need(current.fence_effective, 'FENCE_DRIFT')
                    need(current.restarts == permit.baseline[unit].restarts, 'AUTOMATIC_RESTART_DETECTED')
                    if current.stopped(): break
                    need(current.main_pid in (0, permit.baseline[unit].main_pid) and
                         (not current.main_pid or current.main_start == permit.baseline[unit].main_start), 'PID_REUSE_OR_NEW_WRITER')
                    need(self.now() < end and self.now() < permit.expires_at, 'GRACEFUL_STOP_INCOMPLETE')
                    self.sleep(0.05)
                permit.stopped.append(unit)
            first = self.observe(permit)
            self.sleep(settle_seconds)
            second = self.observe(permit)
            need(first == second, 'QUIESCENCE_STATE_DRIFT')
            permit.state = 'QUIESCENT'
            return {'status': 'OS_QUIESCENT_FIXED_ROLES_ONLY', 'planHash': permit.plan_hash,
                    'actors': second, 'businessRecordsClosed': False, 'adapterLedgerMutationPerformed': False,
                    'globalSameEpochBusinessStopClaim': False, 'forceTerminationUsed': False,
                    'authority': False, 'mayInstall': False, 'permissionWindowStillCurrent': self.now() < permit.expires_at}
        except Exception:
            permit.state = 'ABORT_REQUIRED'
            raise

    def observe(self, permit):
        need(isinstance(permit, _Permit) and permit.brand is _BRAND, 'PROTECTED_INSTALLER_ADMISSION_REQUIRED')
        rows = []
        for unit in ROLE_HOST:
            current = self.backend.inspect(unit, permit.plan_hash)
            need(current.graceful_only(), 'UNSAFE_MANAGER_STOP_POLICY')
            need(current.stopped() and current.fence_effective and not current.daemon_reload_needed, 'LIVE_WRITER_OR_UNFENCED')
            need(current.restarts == permit.baseline[unit].restarts and current.code_hashes == permit.baseline[unit].code_hashes, 'AUTOMATIC_RESTART_OR_CODE_DRIFT')
            rows.append({'unit': unit, 'host': current.host, 'mainPid': 0, 'controlPid': 0,
                         'cgroupEmpty': True, 'automaticStartFenced': True,
                         'restarts': current.restarts, 'fenceHash': current.fence_hash})
        return rows

    def abort_restore(self, permit, timeout_seconds=15):
        need(isinstance(permit, _Permit) and permit.brand is _BRAND, 'PROTECTED_INSTALLER_ADMISSION_REQUIRED')
        need(permit.state == 'ABORT_REQUIRED' and 1 <= timeout_seconds <= 120, 'ABORT_STATE_REQUIRED')
        permit.state = 'ABORT_RESTORING'
        errors, resumed = [], []
        for unit in reversed(permit.touched):
            try:
                current = self.backend.inspect(unit, permit.plan_hash)
                if current.fence_hash:
                    self.backend.unfence(unit, permit.plan_hash)
            except Exception:
                errors.append(unit)
        for unit in START_ORDER:
            if permit.baseline[unit].active != 'active' or unit not in permit.stop_attempts:
                continue
            try:
                current = self.backend.inspect(unit, permit.plan_hash)
                need(current.code_hashes == permit.baseline[unit].code_hashes, 'ABORT_CODE_DRIFT')
                if current.active == 'active' and current.process_identity() == permit.baseline[unit].process_identity():
                    need(current.sub == 'running' and not current.fence_hash, 'ABORT_RESTORE_UNCONFIRMED')
                else:
                    need(current.stopped() and not current.fence_hash, 'ABORT_RESTORE_UNCONFIRMED')
                    self.backend.start(unit, permit.plan_hash)
                    end = self.now() + timeout_seconds
                    while True:
                        current = self.backend.inspect(unit, permit.plan_hash)
                        if current.active == 'active' and current.sub == 'running' and current.main_pid and not current.fence_hash: break
                        need(self.now() < end, 'ABORT_RESTORE_UNCONFIRMED')
                        self.sleep(0.05)
                resumed.append(unit)
            except Exception:
                errors.append(unit)
        permit.state = 'ABORT_RESTORED_OS_ONLY' if not errors else 'ABORT_RESTORE_PARTIAL'
        return {'status': permit.state, 'resumedUnits': resumed, 'unconfirmedUnits': sorted(set(errors)),
                'businessReadinessClaim': False, 'ledgerRestoredOrRewritten': False}


def main():
    if sys.argv[1:] == ['describe']:
        print(json.dumps({'schema': 'r16.maintenance-os-adapter-capabilities.v1', 'fixedUnits': ROLE_HOST,
                          'productionAdmissionImplemented': False, 'remoteProtectedHelperInstalled': False,
                          'forceTerminationImplemented': False, 'productionExecutionPerformed': False}))
        return 0
    print(json.dumps({'refused': True, 'code': 'PROTECTED_INSTALLER_ADMISSION_REQUIRED'}))
    return 78


if __name__ == '__main__':
    raise SystemExit(main())
