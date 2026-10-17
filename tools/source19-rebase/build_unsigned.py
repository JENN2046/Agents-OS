#!/usr/bin/python3
"""Ordinary-user, unsigned R17 assembly from the exact public source19 base.

No service, credential, signer, provider, ledger or production configuration API.
The supplied public JSON is pinned to G1's independently verified public19.
"""
import argparse
import hashlib
import json
import os
import posixpath
from pathlib import Path
import re
import stat
import subprocess

PUBLIC_DIGEST = '56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec'
SOURCE_DELIVERY_HASH = 'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9'
SOURCE_RELEASE = 'r16-daily-20261015-r15-app-recovery-r6'
TARGET_RELEASE = 'r16-daily-20261012-r17'
BRIDGE_MANIFEST = Path('/opt/r16/releases/r16-daily-20261012-r15/bridge-manifest.json')
VERSIONS = {'app': '34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500',
            'bridge': '9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',
            'native': '2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4'}
BASE_REPAIRS = {'app/workspace-host.mjs': 'bfef60223b8fd186f2e96887b770678777bf99ff2a5c84a3c36273d8f172a6ab',
                'app/app-runner.mjs': 'feaf51d26f5ef56cdfe013b65fe3faef37f91bc26391835810deb655e51f14d7',
                'host/workspace-dispatcher.mjs': 'ba4ef78187a8701b97bd03461faed44771c4d71b8541681a6d573e3f35ed079c'}
GUARDS = {'app/workspace-host.mjs': (' function stopAdmission(){', ' return Object.freeze(', 'f7f4413c77e591af9ba2c3a570d5ddb2c9ab41772e8b5273ba2312f15cefddba'),
          'host/workspace-dispatcher.mjs': ('  function recoveryFence(', '  function authorizeCall(', '10ab0bce9f12555284ebe570cc8803bb0328bf0d273ea7648ca2b76c40fcd454')}
COMPONENTS = ('src', 'app', 'bridge', 'host', 'native', 'authority', 'deployment', 'r16_settings', 'packaging', 'human', 'release', 'migration')
PREFIXES = {'app': ('src/', 'app/', 'deployment/', 'authority/', 'r16_settings/', 'packaging/', 'migration/r17-one-time-recovery-admission.mjs'),
            'bridge': ('src/', 'bridge/', 'host/native-gateway.mjs', 'deployment/', 'authority/runtime-manifest.mjs', 'authority/transaction-publish.mjs', 'authority/recovery-handoff.mjs', 'authority/source-baseline.mjs', 'migration/r17-one-time-recovery-admission.mjs', 'app/upstream/node_modules/'),
            'native': ('src/', 'host/', 'native/', 'authority/', 'r16_settings/', 'packaging/', 'human/', 'release/', 'migration/')}
PRODUCT = 'execution/minimal-human-trust/'


class Refused(ValueError):
    pass


def need(value, code):
    if not value:
        raise Refused(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    if value is None or type(value) in (str, bool):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    if type(value) is int:
        need(abs(value) <= 9007199254740991, 'UNSAFE_INTEGER')
        return str(value)
    if type(value) is list:
        return '[' + ','.join(canonical(x) for x in value) + ']'
    need(type(value) is dict and all(type(k) is str for k in value), 'CANONICAL_TYPE')
    return '{' + ','.join(canonical(k) + ':' + canonical(value[k]) for k in sorted(value, key=lambda s: s.encode('utf-16-be'))) + '}'


def digest(value):
    return sha(canonical(value).encode())


def parse(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def relative(name):
    need(type(name) is str and name and not name.startswith('/') and '\\' not in name and not any(ord(x) < 32 or ord(x) == 127 for x in name) and all(x not in ('', '.', '..') for x in name.split('/')), 'UNSAFE_PATH')
    need(not any(x in ('.git', 'secrets', 'credentials', 'tokens', 'state-private', '__pycache__') or x.startswith('.env') for x in name.split('/')) and not re.search(r'\.(?:key|pem|pfx|p12|cred|log|pyc)$', name), 'SENSITIVE_OR_GENERATED_PATH')
    return name


def stamp(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def read(path):
    path = Path(path)
    for p in (path, *path.parents):
        need(not p.is_symlink(), 'SYMLINK_SOURCE')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= 128 * 1024 * 1024, 'SOURCE_FILE_TYPE')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(128 * 1024 * 1024 + 1)
        need(len(raw) == before.st_size and stamp(before) == stamp(os.fstat(fd)) == stamp(path.lstat()), 'SOURCE_CHANGED_DURING_READ')
        return raw, stat.S_IMODE(before.st_mode)
    finally:
        os.close(fd)


def git(repo, *args):
    return subprocess.check_output(('/usr/bin/git', '-C', str(repo), *args), stderr=subprocess.DEVNULL)


def clean_head(repo, head):
    need(re.fullmatch('[0-9a-f]{40}', head) and git(repo, 'rev-parse', 'HEAD').decode().strip() == head and git(repo, 'status', '--porcelain=v1') == b'', 'CLEAN_EXACT_HEAD_REQUIRED')


def public_source(raw):
    pub = parse(raw)
    need(digest(pub) == PUBLIC_DIGEST, 'EXACT_PUBLIC19_DIGEST_REQUIRED')
    need(pub.get('versions') == VERSIONS and pub.get('release', {}).get('body', {}).get('versions') == VERSIONS and pub['release']['body'].get('id') == SOURCE_RELEASE and pub.get('grant', {}).get('body', {}).get('id') == 'r16-projects-daily', 'SOURCE19_RELEASE_OR_ROLES_DRIFT')
    return pub


def base_roles(base):
    paths = {'app': base / 'app-manifest.json', 'native': base / 'native-manifest.json', 'bridge': BRIDGE_MANIFEST}
    roles = {}
    for role, path in paths.items():
        raw, mode = read(path)
        manifest = parse(raw)
        need(mode == 0o644 and digest(manifest) == VERSIONS[role], 'SOURCE_ROLE_MANIFEST_DRIFT')
        need(set(manifest) == {'schema', 'role', 'entry', 'files'} and manifest['schema'] == 'r16.runtime-code.v1' and manifest['role'] == role and manifest['entry'] in manifest['files'], 'SOURCE_ROLE_MANIFEST_SHAPE')
        for name, pin in manifest['files'].items():
            relative(name)
            need(re.fullmatch('[0-9a-f]{64}', pin), 'SOURCE_ROLE_FILE_PIN')
        roles[role] = manifest
    return roles, {r: str(p) for r, p in paths.items()}


def base_payload(base, roles):
    union = {}
    for manifest in roles.values():
        for name, pin in manifest['files'].items():
            need(name not in union or union[name] == pin, 'SOURCE_ROLE_OVERLAP')
            union[name] = pin
    rows = {}
    for name, pin in sorted(union.items()):
        raw, mode = read(base / relative(name))
        need(sha(raw) == pin and mode in (0o644, 0o755), 'SOURCE_PAYLOAD_BYTES_OR_MODE_DRIFT')
        rows[name] = (raw, mode)
    # Do not open the root-only marker. It is not a role payload or permission.
    expected = set(union) | {'app-manifest.json', 'native-manifest.json', '.maintenance-capsule.json'}
    actual = set()
    actual_dirs = set()
    for directory, children, files in os.walk(base, followlinks=False, onerror=lambda e: (_ for _ in ()).throw(e)):
        path = Path(directory)
        actual_dirs.add(str(path.relative_to(base)))
        need(not path.is_symlink() and stat.S_IMODE(path.stat().st_mode) == 0o755 and all(not (path / c).is_symlink() for c in children), 'SOURCE_DIRECTORY_MODE_OR_LINK')
        for name in files:
            value = (path / name).lstat()
            need(stat.S_ISREG(value.st_mode) and value.st_nlink == 1, 'SOURCE_BASE_SPECIAL_FILE')
            actual.add(str((path / name).relative_to(base)))
    expected_dirs = {'.'} | {str(parent) for name in expected for parent in Path(name).parents}
    need(actual == expected and actual_dirs == expected_dirs, 'SOURCE_BASE_FILE_SET_DRIFT')
    return rows


def source_overlay(repo, head):
    overlay = {}
    for entry in git(repo, 'ls-files', '--stage', '-z', PRODUCT).split(b'\0'):
        if not entry:
            continue
        info, name = entry.split(b'\t', 1)
        mode, _, stage = info.decode().split()
        name = name.decode()
        rel = name[len(PRODUCT):]
        if rel.split('/')[0] not in COMPONENTS:
            continue
        relative(rel)
        need(stage == '0' and mode in ('100644', '100755'), 'TRACKED_SOURCE_TYPE')
        raw, _ = read(repo / name)
        need(raw == git(repo, 'show', head + ':' + name), 'TRACKED_SOURCE_BYTES_DRIFT')
        overlay[rel] = (raw, 0o755 if mode == '100755' else 0o644)
    need(overlay, 'EMPTY_PRODUCTION_OVERLAY')
    return overlay


def repair_guards(base, overlay):
    for name, pin in BASE_REPAIRS.items():
        need(name in overlay and sha(base[name][0]) == pin, 'SOURCE_REPAIR_BASE_NOT_EXACT')
    runner = 'app/app-runner.mjs'
    need(overlay[runner][0] == base[runner][0], 'APP_RUNNER_SHUTDOWN_REPAIR_LOST')
    result = {'schema': 'r17.source19.repair-preservation.v1', 'appRunnerSha256': sha(overlay[runner][0]), 'baseRepairFileHashes': BASE_REPAIRS.copy(), 'guardHashes': {}}
    for name, (begin, end, pin) in GUARDS.items():
        segments = []
        for raw in (base[name][0], overlay[name][0]):
            text = raw.decode()
            need(text.count(begin) == text.count(end) == 1, 'REPAIR_GUARD_MARKER_DRIFT')
            start = text.index(begin)
            segments.append(text[start:text.index(end, start)].encode())
        need(segments[0] == segments[1] and sha(segments[0]) == pin, 'PHYSICAL_SHUTDOWN_OR_RECOVERY_FENCE_REPAIR_LOST')
        result['guardHashes'][name] = pin
    return result


def reviewed_freeze(overlay, head):
    text = overlay['release/publisher-bootstrap.mjs'][0].decode()
    match = re.search(r'export const REVIEWED_SOURCE_FILES=Object\.freeze\(\[(.*?)\]\);', text, re.S)
    need(match is not None, 'REVIEWED_FREEZE_LIST_MISSING')
    names = re.findall(r"'([^']+)'", match[1])
    need(names and len(names) == len(set(names)) and all(n in overlay for n in names), 'REVIEWED_FREEZE_SCOPE_MISSING')
    return {'schema': 'mht.first-trust-code-freeze.v1', 'sourceCommit': head, 'files': {n: sha(overlay[n][0]) for n in sorted(names)}}


def without_comments(text):
    out = []
    i = 0
    quote = None
    while i < len(text):
        c = text[i]
        if quote:
            out.append(c)
            if c == '\\' and i + 1 < len(text):
                i += 1
                out.append(text[i])
            elif c == quote:
                quote = None
        elif c in ("'", '"', '`'):
            quote = c
            out.append(c)
        elif text.startswith('//', i) and (i == 0 or text[i - 1] != '\\'):
            end = text.find('\n', i)
            i = len(text) if end < 0 else end
            out.append('\n')
            continue
        elif text.startswith('/*', i) and (i == 0 or text[i - 1] != '\\'):
            end = text.find('*/', i + 2)
            need(end >= 0, 'UNTERMINATED_SOURCE_COMMENT')
            out.append(' ')
            i = end + 2
            continue
        else:
            out.append(c)
        i += 1
    return ''.join(out)


def relative_references(raw):
    text = without_comments(raw.decode())
    pattern = r"\b(?:from\s*|import\s*(?:\(\s*)?|require\s*\(\s*)(['\"])(\.[^'\"\n]+)\1"
    return [m.group(2) for m in re.finditer(pattern, text)]


def close_role_dependencies(files, available):
    # Initial signed upstream dependency trees are retained, not re-discovered.
    # Recursively bind literal relative imports of controlled source modules.
    queue = [n for n in files if n.endswith(('.mjs', '.js', '.cjs')) and '/node_modules/' not in n and '/upstream/' not in n]
    seen = set()
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        for spec in relative_references(available[name][0]):
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), spec))
            relative(resolved)
            candidates = [resolved, resolved + '.js', resolved + '.json', resolved + '.node', resolved + '/index.js', resolved + '/index.json']
            dependency = next((n for n in candidates if n in available), None)
            need(dependency is not None, 'RELATIVE_DEPENDENCY_NOT_IN_VERIFIED_SOURCE_UNION')
            files[dependency] = sha(available[dependency][0])
            if dependency.endswith(('.mjs', '.js', '.cjs')) and '/node_modules/' not in dependency:
                queue.append(dependency)
    return files


def assemble(repo, base, public_json, head):
    clean_head(repo, head)
    public_raw, _ = read(public_json)
    public_source(public_raw)
    original, paths = base_roles(base)
    baseline = base_payload(base, original)
    overlay = source_overlay(repo, head)
    guards = repair_guards(baseline, overlay)
    freeze = reviewed_freeze(overlay, head)
    roles = {}
    available = {**baseline, **overlay}
    assigned = set()
    for role, manifest in original.items():
        files = dict(manifest['files'])
        for name, (raw, _) in overlay.items():
            if name in files or any(name.startswith(p) if p.endswith('/') else name == p for p in PREFIXES[role]):
                files[name] = sha(raw)
                assigned.add(name)
        close_role_dependencies(files, available)
        assigned.update(set(files) & set(overlay))
        roles[role] = {**manifest, 'files': dict(sorted(files.items()))}
    need(assigned == set(overlay), 'PRODUCTION_OVERLAY_UNBOUND')
    final = {}
    bindings = []
    for role in sorted(roles):
        for name, pin in roles[role]['files'].items():
            need(name not in final or final[name] == pin, 'TARGET_ROLE_OVERLAP')
            final[name] = pin
            bindings.append({'role': role, 'artifactPath': name, 'path': '/opt/r16/releases/' + TARGET_RELEASE + '/' + name, 'sha256': pin})
    payload = {}
    inventory = {}
    for name, pin in sorted(final.items()):
        raw, mode = overlay[name] if name in overlay else baseline[name]
        need(sha(raw) == pin, 'FINAL_PAYLOAD_PROVENANCE_DRIFT')
        payload[name] = (raw, mode)
        inventory[name] = {'sha256': pin, 'bytes': len(raw), 'mode': mode, 'sourceKind': 'EXACT_HEAD_OVERLAY' if name in overlay else 'SIGNED_SOURCE19_BASE'}
    versions = {r: digest(m) for r, m in roles.items()}
    scope = {'status': 'UNSIGNED_ISOLATED_NOT_ACTIVATED', 'sourceHead': head, 'sourcePublicConfigDigest': PUBLIC_DIGEST, 'sourceConfigurationRevision': 19, 'expectedSourceDeliveryHash': SOURCE_DELIVERY_HASH, 'sourceReleaseId': SOURCE_RELEASE, 'targetReleaseId': TARGET_RELEASE, 'targetVersions': versions, 'roleCounts': {r: len(m['files']) for r, m in roles.items()}, 'uniqueFiles': len(final), 'roleBindings': len(bindings), 'issuedAt': None, 'notAfter': None, 'plannedConfigurationRevision': None, 'reservedRevision20Authorized': False, 'maySign': False, 'mayInstall': False, 'mayActivate': False, 'mayChangeOwner': False, 'maySettleUnknown': False}
    provenance = {'schema': 'r17.source19.provenance.v1', 'sourceHead': head, 'sourcePublicConfigDigest': PUBLIC_DIGEST, 'sourceReleaseId': SOURCE_RELEASE, 'sourceVersions': VERSIONS, 'sourceRoleManifestPaths': paths, 'baseDirectory': str(base), 'sourceSignatureAuthority': 'EXACT_PUBLIC_DIGEST_VERIFIED_BY_EXTERNAL_G1', 'independentG1CryptoAndFresh19ReceiptRequired': True, 'liveConfigurationOrBusinessStateRead': False, 'rootMarkerRead': False, 'baseFiles': len(baseline), 'baseBytes': sum(len(v[0]) for v in baseline.values()), 'overlayFiles': {n: sha(v[0]) for n, v in sorted(overlay.items())}, 'sourceFreezeDigest': digest(freeze), 'repairGuards': guards, 'authority': False}
    metadata = {'UNSIGNED_CONTENT.json': {'schema': 'r17.source19.unsigned-content.v1', **scope}, 'ROLE_MANIFESTS.json': {'schema': 'r17.source19.role-manifests.v1', 'sourceHead': head, 'artifacts': roles}, 'SOURCE_ROLE_MANIFESTS.json': original, 'LOCAL_FILE_BINDINGS.json': {'schema': 'r17.source19.local-file-bindings.v1', 'sourceHead': head, 'files': bindings}, 'PROVENANCE.json': provenance, 'PAYLOAD_INVENTORY.json': {'schema': 'r17.source19.payload-inventory.v1', 'sourceHead': head, 'files': inventory, 'uniqueFiles': len(inventory), 'totalBytes': sum(v['bytes'] for v in inventory.values())}, 'REVIEWED_SOURCE_FREEZE.json': freeze, 'REPAIR_GUARDS.json': guards}
    identity_sources = {
        '/usr/lib/minimal-human-trust/authority/identity-admission.py': 'authority/identity-admission.py',
        '/usr/lib/minimal-human-trust/packaging/minimal-human-trust-identity-admission': 'packaging/minimal-human-trust-identity-admission',
        '/etc/systemd/system/minimal-human-trust-identity-admission.service': 'packaging/minimal-human-trust-identity-admission.service',
        '/usr/share/polkit-1/actions/org.jenn.r16.minimal-human-trust.identity-admission.policy': 'packaging/org.jenn.r16.minimal-human-trust.identity-admission.policy',
    }
    need(all(n in payload for n in identity_sources.values()), 'IDENTITY_ADMISSION_SOURCE_REQUIRED')
    metadata['IDENTITY_ADMISSION_FREEZE.json'] = {'schema': 'mht.identity-admission-code-freeze.v1',
        'sourceCommit': head, 'files': {target: sha(payload[n][0]) for target, n in sorted(identity_sources.items())}}
    for role, manifest in roles.items():
        metadata[role + '-manifest.json'] = manifest
    raw_metadata = {n: (canonical(v) + '\n').encode() for n, v in metadata.items()}
    raw_metadata['SOURCE_PUBLIC_CONFIG.json'] = public_raw
    raw_metadata['SHA256SUMS_PAYLOAD.txt'] = ''.join(row['sha256'] + '  payload/' + n + '\n' for n, row in inventory.items()).encode()
    clean_head(repo, head)
    return payload, raw_metadata, scope


def build(repo, base, output, public_json, head, plan_only=False):
    need(os.geteuid() != 0 and all(p.is_absolute() for p in (repo, base, output, public_json)), 'ORDINARY_USER_ABSOLUTE_PATHS_REQUIRED')
    need(not any(p.is_symlink() for p in (output, *output.parents)), 'OUTPUT_SYMLINK_PATH_REFUSED')
    need(not output.exists() and not output.is_symlink() and not output.is_relative_to(base) and not output.is_relative_to(repo / PRODUCT), 'NEW_ISOLATED_OUTPUT_REQUIRED')
    payload, metadata, scope = assemble(repo, base, public_json, head)
    if not plan_only:
        output.mkdir(parents=True, mode=0o755)
        output.chmod(0o755)
        for prefix, rows in (('payload', payload), ('metadata', {n: (b, 0o644) for n, b in metadata.items()})):
            for name, (raw, mode) in rows.items():
                path = output / prefix / relative(name)
                path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
                parent = path.parent
                while parent != output:
                    parent.chmod(0o755)
                    parent = parent.parent
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(raw)
                path.chmod(mode)
    return {'schema': 'r17.source19.unsigned-build-receipt.v1', **scope, 'outputCreated': not plan_only, 'payloadBytes': sum(len(v[0]) for v in payload.values()), 'metadataFiles': len(metadata), 'inventorySha256': sha(metadata['PAYLOAD_INVENTORY.json']), 'metadataSha256': {n: sha(v) for n, v in metadata.items()}, 'signaturesIssued': 0, 'productionEffectsIssued': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo', 'base', 'output', 'source-public-json'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--source-head', required=True)
    parser.add_argument('--plan-only', action='store_true')
    args = parser.parse_args()
    try:
        result = build(args.repo, args.base, args.output, args.source_public_json, args.source_head, args.plan_only)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        print('{"status":"UNSIGNED_BUILD_REFUSED","productionEffectsIssued":0}')
        return 78


if __name__ == '__main__':
    raise SystemExit(main())
