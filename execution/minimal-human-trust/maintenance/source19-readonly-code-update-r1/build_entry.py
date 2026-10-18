"""Ordinary, offline source packet builder; no target, SSH, sudo or keys."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

HERE = Path(__file__).parent
BUNDLE = Path('/home/jenn/AGENTS_OS_Workspace/ops/source19-app-history-schema-20261017-r1/code-bytes-candidate-not-install-entry')
PREVIOUS = Path('/home/jenn/Documents/Codex/2026-10-17/SOURCE19_PROTECTED_PREFLIGHT_R1/code-bundle-r2')
FIXTURES = HERE / 'fixtures'
OUTPUT = Path('/home/jenn/Documents/Codex/2026-10-17/SOURCE19_READONLY_CODE_UPDATE_R1')


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    obj = importlib.util.module_from_spec(spec);sys.modules[name] = obj
    spec.loader.exec_module(obj);return obj


def packet_sources():
    core = module('support_admission', HERE / 'support_admission.py')
    update = module('code_update', HERE / 'code_update.py')
    packet = {n: (HERE / n).read_bytes() for n in
              ('code_update.py', 'support_admission.py', 'native_guard.py', 'launch_code_update.py')}
    packet['legacy_supplement.json'] = (FIXTURES / 'legacy_supplement.json').read_bytes()
    core.need(core.sha(packet['legacy_supplement.json']) ==
              'a38138c0c4197f31746aa413d9d580f48ac430955e35de55c7ac1992a988cced',
              'LEGACY_SUPPLEMENT_DRIFT')
    # Portable public-code fixtures: no installed state and no /home/jenn
    # artifact dependency in CI. Final build separately verifies physical input.
    for prefix in ('bundle/', 'previous/'):
        metadata = FIXTURES / prefix[:-1]
        for name, source in [('CODE_ADMISSION_CANDIDATE.json', 'CODE_ADMISSION_CANDIDATE.json'),
                             ('BUILD_RECEIPT.json', 'BUILD_RECEIPT.json'),
                             ('root/ENTRY_FREEZE.json', 'ENTRY_FREEZE.json'),
                             ('installed-entry-pin.json', 'installed-entry-pin.json')]:
            packet[prefix + name] = (metadata / source).read_bytes()
        freeze = core.parse(packet[prefix + 'root/ENTRY_FREEZE.json'])
        for name in freeze['files']:
            p = HERE.parents[1] / name
            if prefix == 'previous/' and name.endswith('/checkpoint_public.mjs'):
                p = FIXTURES / 'checkpoint_public_before_schema_fix.mjs.txt'
            packet[prefix + 'root/runtime/' + name] = p.read_bytes()
        for name in ('r16-source19-native-transition-r1-rpc', 'r16-source19-native-transition-r1.sudoers'):
            packet[prefix + 'cloud-policy/' + name] = packet[prefix +
                'root/runtime/maintenance/source19-native-transition-r1/entry/' + name]
    _, old, new = update.targets(packet, core.CLOUD)
    entry_head = subprocess.check_output(['git', '-C', str(HERE), 'rev-parse', 'HEAD'], text=True).strip()
    review = {'schema': 'r16.source19-readonly-code-update.supplement-review.v1',
              'sourceHead': update.HEAD, 'entrySourceHead': entry_head,
              'oldCapsuleHash': core.CAPSULE, 'newCapsuleHash': update.CAPSULE,
              'changes': [{'path': p, 'before': old[p][0], 'after': new[p][0]} for p in update.ORDER],
              'supportSources': {n: core.sha(packet[n]) for n in
                  ('code_update.py', 'support_admission.py', 'native_guard.py', 'launch_code_update.py')},
              'auditScope': update.audit_scope(),
              'scope': 'EXACT_THREE_PUBLIC_READONLY_CODE_OBJECTS_ONLY',
              'permission': 'NEW_GENUINE_NATIVE_HOSTADMIN_CONFIRMATION_REQUIRED',
              'sourceBaseline': {'configurationRevision': 19, 'publicConfigSha256': core.PUB,
                                'acceptedDeliverySha256': core.DELIVERY, 'grantSha256': core.GRANT},
              'oldInstallationRequired': {'localTargets': 30, 'cloudTargets': 32,
                                          'exactReceiptAndIdentityReadback': True},
              'unchangedTargetsRequireFullIdentity': True,
              'lockOrder': [core.STATE + '/.lock', update.STATE + '/.lock'],
              'writePolicy': 'EXACT_PREIMAGE_SAME_FS_RENAMEAT2_NOREPLACE_KEEP_ALL_HISTORY',
              'publicationOrder': list(update.ORDER), 'pinPublishedLast': True,
              'threeFileAtomicityClaimed': False,
              'possibleInterruption': 'READONLY_PREFLIGHT_MAY_REFUSE_DURING_UPDATE; HELD_OLD_READONLY_BYTES_MAY_CONTINUE',
              'failurePolicy': 'NO_UPDATE_REPLAY; READBACK_THEN_SEPARATE_FRESH_NATIVE_RESTORE',
              'restoreScope': 'ONLY_ORIGINAL_RECORDED_INODES_AND_KNOWN_NEW_STAGE_INODES',
              'validForMsFromAcceptance': 300000, 'oldApprovalOrDeadlineReused': False,
              'forbidden': ['SERVICE_ACTION', 'SIGNING', 'KEY_GENERATION_OR_PRIVATE_KEY_READ',
                            'CONFIGURATION_CHANGE', 'SELECTOR_CHANGE', 'OWNER_SWITCH',
                            'BUSINESS_LEDGER_WRITE', 'UNKNOWN_REPLAY_OR_SETTLEMENT',
                            'OLD_PLAN_OR_DEADLINE_EXTENSION'],
              'authority': False, 'humanIdentityConfirmed': False, 'businessAcceptance': False}
    packet['review.json'] = core.raw(review) + b'\n'
    return packet


def build(output):
    if os.getuid() != os.geteuid() or os.getuid() == 0 or output.exists():
        raise ValueError('NEW_ORDINARY_OUTPUT_REQUIRED')
    packet = packet_sources()
    # Source build must still bind the real, retained old/new physical bundles.
    for prefix, directory in [('bundle/', BUNDLE), ('previous/', PREVIOUS)]:
        actual = {prefix + p.relative_to(directory).as_posix(): p for p in directory.rglob('*') if p.is_file()}
        expected = {n for n in packet if n.startswith(prefix)}
        if set(actual) != expected or any(p.is_symlink() for p in directory.rglob('*')):
            raise ValueError('PHYSICAL_BUNDLE_SET_DRIFT')
        for name, p in actual.items():
            st = p.lstat()
            if (st.st_uid != os.getuid() or st.st_nlink != 1 or not stat.S_ISREG(st.st_mode)
                    or st.st_mode & 0o022 or p.read_bytes() != packet[name]):
                raise ValueError('PHYSICAL_BUNDLE_BYTES_OR_METADATA_DRIFT')
    output.mkdir(mode=0o700);source = output / 'source';source.mkdir(mode=0o700)
    manifest = {}
    for name, value in packet.items():
        if name.startswith(('bundle/', 'previous/')):
            directory = BUNDLE if name.startswith('bundle/') else PREVIOUS
            p = directory / name.split('/', 1)[1];mode = stat.S_IMODE(p.stat().st_mode)
        else:
            mode = 0o644;p = source / name;p.write_bytes(value);p.chmod(mode)
        manifest[name] = {'path': name, 'sha256': hashlib.sha256(value).hexdigest(),
                          'bytes': len(value), 'mode': mode}
    raw = json.dumps({'schema': 'r16.source19-readonly-code-update.entry-freeze.v1',
                      'files': manifest, 'authority': False, 'businessAcceptance': False},
                     sort_keys=True, separators=(',', ':')).encode() + b'\n'
    (source / 'ENTRY_FREEZE.json').write_bytes(raw);(source / 'ENTRY_FREEZE.json').chmod(0o600)
    payload = json.dumps({'entryFreeze': base64.b64encode(raw).decode(),
                         'sources': {n: base64.b64encode(b).decode() for n, b in packet.items()}},
                        separators=(',', ':')).encode()
    if len(payload) > 2 * 1024 * 1024:raise ValueError('PACKET_CAPACITY')
    out = output / 'SOURCE19_READONLY_CODE_UPDATE_PACKET.json';out.write_bytes(payload);out.chmod(0o600)
    return {'status': 'SOURCE_ONLY_ENTRY_BUILT_NOT_EXECUTED', 'sourceFiles': len(manifest),
            'packetSha256': hashlib.sha256(payload).hexdigest(), 'packetBytes': len(payload),
            'entryFreezeSha256': hashlib.sha256(raw).hexdigest(), 'authority': False,
            'productionEffects': 0, 'businessAcceptance': False}


if __name__ == '__main__':
    print(json.dumps(build(OUTPUT)))
