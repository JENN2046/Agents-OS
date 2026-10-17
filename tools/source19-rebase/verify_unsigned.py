#!/usr/bin/python3
"""Independent stdlib verifier: does not import the collector or any runtime.

An external inventory SHA and source HEAD are mandatory. --repo/--base add a
fresh read-only provenance check. No signatures, live-state claims or effects.
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

PUBLIC = '56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec'
DELIVERY = 'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9'
SOURCE = 'r16-daily-20261015-r15-app-recovery-r6'
TARGET = 'r16-daily-20261012-r17'
BRIDGE = Path('/opt/r16/releases/r16-daily-20261012-r15/bridge-manifest.json')
VERSIONS = {'app': '34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500', 'bridge': '9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352', 'native': '2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4'}
BASE_REPAIRS = {'app/workspace-host.mjs': 'bfef60223b8fd186f2e96887b770678777bf99ff2a5c84a3c36273d8f172a6ab', 'app/app-runner.mjs': 'feaf51d26f5ef56cdfe013b65fe3faef37f91bc26391835810deb655e51f14d7', 'host/workspace-dispatcher.mjs': 'ba4ef78187a8701b97bd03461faed44771c4d71b8541681a6d573e3f35ed079c'}
GUARDS = {'app/workspace-host.mjs': (' function stopAdmission(){', ' return Object.freeze(', 'f7f4413c77e591af9ba2c3a570d5ddb2c9ab41772e8b5273ba2312f15cefddba'), 'host/workspace-dispatcher.mjs': ('  function recoveryFence(', '  function authorizeCall(', '10ab0bce9f12555284ebe570cc8803bb0328bf0d273ea7648ca2b76c40fcd454')}
COMPONENTS = {'src', 'app', 'bridge', 'host', 'native', 'authority', 'deployment', 'r16_settings', 'packaging', 'human', 'release', 'migration'}
ROLE_PREFIXES = {'app': ('src/', 'app/', 'deployment/', 'authority/', 'r16_settings/', 'packaging/', 'migration/r17-one-time-recovery-admission.mjs'), 'bridge': ('src/', 'bridge/', 'host/native-gateway.mjs', 'deployment/', 'authority/runtime-manifest.mjs', 'authority/transaction-publish.mjs', 'authority/recovery-handoff.mjs', 'authority/source-baseline.mjs', 'migration/r17-one-time-recovery-admission.mjs', 'app/upstream/node_modules/'), 'native': ('src/', 'host/', 'native/', 'authority/', 'r16_settings/', 'packaging/', 'human/', 'release/', 'migration/')}
META = {'IDENTITY_ADMISSION_FREEZE.json', 'UNSIGNED_CONTENT.json', 'ROLE_MANIFESTS.json', 'SOURCE_ROLE_MANIFESTS.json', 'LOCAL_FILE_BINDINGS.json', 'PROVENANCE.json', 'PAYLOAD_INVENTORY.json', 'REVIEWED_SOURCE_FREEZE.json', 'REPAIR_GUARDS.json', 'SOURCE_PUBLIC_CONFIG.json', 'SHA256SUMS_PAYLOAD.txt', 'app-manifest.json', 'bridge-manifest.json', 'native-manifest.json'}


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canon(v):
    if v is None or type(v) in (str, bool):
        return json.dumps(v, ensure_ascii=False, separators=(',', ':'))
    if type(v) is int:
        require(abs(v) <= 9007199254740991, 'UNSAFE_INTEGER')
        return str(v)
    if type(v) is list:
        return '[' + ','.join(map(canon, v)) + ']'
    require(type(v) is dict and all(type(k) is str for k in v), 'CANONICAL_TYPE')
    return '{' + ','.join(canon(k) + ':' + canon(v[k]) for k in sorted(v, key=lambda s: s.encode('utf-16-be'))) + '}'


def digest(v):
    return sha(canon(v).encode())


def decode(raw):
    def pairs(items):
        out = {}
        for k, v in items:
            require(k not in out, 'DUPLICATE_JSON_KEY')
            out[k] = v
        return out
    return json.loads(raw, object_pairs_hook=pairs)


def safe(name):
    require(type(name) is str and name and not name.startswith('/') and '\\' not in name and all(x not in ('', '.', '..') for x in name.split('/')) and not any(ord(c) < 32 or ord(c) == 127 for c in name), 'UNSAFE_PATH')
    return name


def read(path):
    path = Path(path)
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'LINK_IN_PATH')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        first = os.fstat(fd)
        require(stat.S_ISREG(first.st_mode) and first.st_nlink == 1 and first.st_size <= 128 * 1024 * 1024, 'FILE_METADATA')
        with os.fdopen(fd, 'rb', closefd=False) as f:
            raw = f.read(128 * 1024 * 1024 + 1)
        key = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        require(len(raw) == first.st_size and key(first) == key(os.fstat(fd)) == key(path.lstat()), 'FILE_CHANGED')
        return raw, stat.S_IMODE(first.st_mode)
    finally:
        os.close(fd)


def exact_tree(root, expected):
    files, dirs = set(), set()
    for directory, children, names in os.walk(root, followlinks=False, onerror=lambda e: (_ for _ in ()).throw(e)):
        p = Path(directory)
        require(p.is_dir() and not p.is_symlink() and stat.S_IMODE(p.stat().st_mode) == 0o755, 'DIRECTORY_MODE')
        dirs.add(str(p.relative_to(root)))
        require(all(not (p / c).is_symlink() for c in children), 'DIRECTORY_LINK')
        for name in names:
            st = (p / name).lstat()
            require(stat.S_ISREG(st.st_mode) and st.st_nlink == 1, 'LINK_OR_SPECIAL_FILE')
            files.add(str((p / name).relative_to(root)))
    required_dirs = {'.'} | {str(p) for name in expected for p in Path(name).parents}
    require(files == expected and dirs == required_dirs, 'EXACT_FILE_OR_DIRECTORY_SET')


def check_manifest(manifest, role):
    require(type(manifest) is dict and set(manifest) == {'schema', 'role', 'entry', 'files'} and manifest['schema'] == 'r16.runtime-code.v1' and manifest['role'] == role and manifest['entry'] in manifest['files'], 'ROLE_MANIFEST_SHAPE')
    for path, pin in manifest['files'].items():
        safe(path)
        require(type(pin) is str and re.fullmatch('[0-9a-f]{64}', pin), 'ROLE_FILE_PIN')


def provenance_check(repo, base, head, originals, rows, expected_overlay, paths):
    def git(*args):
        return subprocess.check_output(('/usr/bin/git', '-C', str(repo), *args), stderr=subprocess.DEVNULL)
    require(git('rev-parse', 'HEAD').decode().strip() == head and git('status', '--porcelain=v1') == b'', 'LIVE_CLEAN_HEAD')
    manifests = {'app': base / 'app-manifest.json', 'native': base / 'native-manifest.json', 'bridge': BRIDGE}
    require(paths == {r: str(p) for r, p in manifests.items()}, 'LIVE_ROLE_PATH_MAPPING')
    union = {}
    for role, path in manifests.items():
        raw, mode = read(path)
        require(decode(raw) == originals[role] and mode == 0o644, 'LIVE_BASE_MANIFEST')
        for name, pin in originals[role]['files'].items():
            require(name not in union or union[name] == pin, 'LIVE_BASE_OVERLAP')
            union[name] = pin
    base_count = 0
    for name, pin in union.items():
        raw, mode = read(base / name)
        require(sha(raw) == pin and mode in (0o644, 0o755), 'LIVE_BASE_FILE_BYTES_OR_MODE')
        if name not in expected_overlay:
            require(rows[name]['mode'] == mode, 'LIVE_BASE_MODE_NOT_PRESERVED')
        base_count += 1
    exact_tree(base, set(union) | {'app-manifest.json', 'native-manifest.json', '.maintenance-capsule.json'})
    actual_overlay = set()
    for entry in git('ls-files', '--stage', '-z', 'execution/minimal-human-trust/').split(b'\0'):
        if not entry:
            continue
        record, path = entry.split(b'\t', 1)
        mode, _, stage = record.decode().split()
        path = path.decode()
        name = path[len('execution/minimal-human-trust/'):]
        if name.split('/')[0] not in COMPONENTS:
            continue
        require(stage == '0' and mode in ('100644', '100755'), 'LIVE_SOURCE_MODE')
        actual_overlay.add(name)
        raw, _ = read(repo / path)
        require(raw == git('show', head + ':' + path) and sha(raw) == expected_overlay[name] == rows[name]['sha256'] and rows[name]['mode'] == (0o755 if mode == '100755' else 0o644), 'LIVE_EXACT_HEAD_OVERLAY')
    require(actual_overlay == set(expected_overlay), 'LIVE_OVERLAY_FILE_SET')
    require(git('rev-parse', 'HEAD').decode().strip() == head and git('status', '--porcelain=v1') == b'', 'LIVE_HEAD_CHANGED')
    return {'sourceBaseFilesVerified': base_count, 'exactHeadOverlayFilesVerified': len(actual_overlay)}


def module_specifiers(raw):
    # Separate scanner in the verifier: comments are lexical trivia; literal
    # import/export/require operands are read from the delivered source itself.
    text = raw.decode()
    tokens = []
    index = 0
    while index < len(text):
        if text[index].isspace():
            index += 1
        elif text.startswith('//', index):
            end = text.find('\n', index + 2)
            index = len(text) if end < 0 else end + 1
        elif text.startswith('/*', index):
            end = text.find('*/', index + 2)
            require(end >= 0, 'SOURCE_COMMENT_UNTERMINATED')
            index = end + 2
        elif text[index] in ("'", '"', '`'):
            quote = text[index]
            end = index + 1
            escaped = False
            while end < len(text):
                if text[end] == '\\':
                    escaped = True
                    end += 2
                elif text[end] == quote:
                    break
                else:
                    end += 1
            require(end < len(text), 'SOURCE_STRING_UNTERMINATED')
            tokens.append(('literal' if quote != '`' else 'template', text[index + 1:end], escaped))
            index = end + 1
        elif text[index].isalpha() or text[index] in '_$':
            end = index + 1
            while end < len(text) and (text[end].isalnum() or text[end] in '_$'):
                end += 1
            tokens.append(('word', text[index:end], False))
            index = end
        else:
            tokens.append(('punct', text[index], False))
            index += 1
    refs = []
    for i, token in enumerate(tokens):
        if token[0] != 'literal' or not token[1].startswith('.'):
            continue
        previous = tokens[i - 1] if i else None
        earlier = tokens[i - 2] if i > 1 else None
        literal_import = previous and previous[:2] in (('word', 'from'), ('word', 'import'))
        literal_call = previous and previous[:2] == ('punct', '(') and earlier and earlier[:2] in (('word', 'import'), ('word', 'require'))
        if literal_import or literal_call:
            require(not token[2], 'ESCAPED_RELATIVE_SPECIFIER_REFUSED')
            refs.append(token[1])
    return refs


def require_role_closure(files, payload):
    pending = [n for n in files if n.endswith(('.mjs', '.js', '.cjs')) and '/upstream/' not in n and '/node_modules/' not in n]
    inspected = set()
    while pending:
        name = pending.pop()
        if name in inspected:
            continue
        inspected.add(name)
        for spec in module_specifiers(payload[name]):
            relative = posixpath.normpath(posixpath.join(posixpath.dirname(name), spec))
            safe(relative)
            options = (relative, relative + '.js', relative + '.json', relative + '.node', relative + '/index.js', relative + '/index.json')
            target = next((n for n in options if n in payload), None)
            require(target is not None, 'STATIC_RELATIVE_DEPENDENCY_MISSING')
            files[target] = sha(payload[target])
            if target.endswith(('.mjs', '.js', '.cjs')) and '/node_modules/' not in target:
                pending.append(target)


def verify(package, inventory_hash, head, repo=None, base=None):
    require(os.geteuid() != 0 and re.fullmatch('[0-9a-f]{40}', head) and re.fullmatch('[0-9a-f]{64}', inventory_hash), 'ORDINARY_USER_EXTERNAL_PINS_REQUIRED')
    require((repo is None) == (base is None), 'BOTH_LIVE_PROVENANCE_PATHS_REQUIRED')
    raw, mode = read(package / 'metadata/PAYLOAD_INVENTORY.json')
    require(sha(raw) == inventory_hash and mode == 0o644, 'EXTERNAL_INVENTORY_SHA')
    inv = decode(raw)
    require(set(inv) == {'schema', 'sourceHead', 'files', 'uniqueFiles', 'totalBytes'} and inv['schema'] == 'r17.source19.payload-inventory.v1' and inv['sourceHead'] == head, 'INVENTORY_SCOPE')
    rows = inv['files']
    require(type(rows) is dict and rows and inv['uniqueFiles'] == len(rows), 'INVENTORY_COUNT')
    exact_tree(package, {'payload/' + safe(n) for n in rows} | {'metadata/' + n for n in META})
    metadata = {}
    for name in META:
        raw, mode = read(package / 'metadata' / name)
        require(mode == 0o644, 'METADATA_MODE')
        metadata[name] = raw
    doc = lambda n: decode(metadata[n])
    pub = doc('SOURCE_PUBLIC_CONFIG.json')
    require(digest(pub) == PUBLIC and pub.get('versions') == VERSIONS and pub.get('release', {}).get('body', {}).get('id') == SOURCE and pub['release']['body'].get('versions') == VERSIONS, 'PINNED_PUBLIC19')
    originals = doc('SOURCE_ROLE_MANIFESTS.json')
    require(set(originals) == set(VERSIONS), 'SOURCE_ROLES')
    for role, manifest in originals.items():
        check_manifest(manifest, role)
        require(digest(manifest) == VERSIONS[role], 'SOURCE_SIGNED_ROLE_VERSION')
    base_union = {}
    for manifest in originals.values():
        for name, pin in manifest['files'].items():
            require(name not in base_union or base_union[name] == pin, 'SOURCE_ROLE_OVERLAP')
            base_union[name] = pin
    overlays = {}
    payload = {}
    total = 0
    for name, row in rows.items():
        require(set(row) == {'sha256', 'bytes', 'mode', 'sourceKind'} and type(row['mode']) is int and row['mode'] in (0o644, 0o755), 'INVENTORY_ROW')
        raw, mode = read(package / 'payload' / name)
        payload[name] = raw
        require(sha(raw) == row['sha256'] and len(raw) == row['bytes'] and mode == row['mode'], 'PAYLOAD_BYTES_OR_MODE')
        require(row['sourceKind'] in ('EXACT_HEAD_OVERLAY', 'SIGNED_SOURCE19_BASE'), 'FILE_PROVENANCE_KIND')
        if row['sourceKind'] == 'EXACT_HEAD_OVERLAY':
            overlays[name] = row['sha256']
        else:
            require(base_union.get(name) == row['sha256'], 'BASE_FILE_PROVENANCE')
        total += len(raw)
    require(total == inv['totalBytes'], 'TOTAL_BYTES')
    target_roles = {}
    assigned = set()
    for role, manifest in originals.items():
        files = dict(manifest['files'])
        for name, pin in overlays.items():
            if name in files or any(name.startswith(prefix) if prefix.endswith('/') else name == prefix for prefix in ROLE_PREFIXES[role]):
                files[name] = pin
                assigned.add(name)
        require_role_closure(files, payload)
        assigned.update(set(files) & set(overlays))
        target_roles[role] = {**manifest, 'files': dict(sorted(files.items()))}
    require(assigned == set(overlays), 'UNBOUND_OVERLAY')
    packet = doc('ROLE_MANIFESTS.json')
    require(packet == {'schema': 'r17.source19.role-manifests.v1', 'sourceHead': head, 'artifacts': target_roles}, 'TARGET_ROLE_BINDINGS')
    target_union = {}
    bindings = []
    for role in sorted(target_roles):
        require(doc(role + '-manifest.json') == target_roles[role], 'ROLE_MANIFEST_COPY')
        for name, pin in target_roles[role]['files'].items():
            require(name not in target_union or target_union[name] == pin, 'TARGET_ROLE_OVERLAP')
            target_union[name] = pin
            bindings.append({'role': role, 'artifactPath': name, 'path': '/opt/r16/releases/' + TARGET + '/' + name, 'sha256': pin})
    require(set(target_union) == set(rows) and all(rows[n]['sha256'] == h for n, h in target_union.items()), 'COMPLETE_ROLE_UNION')
    require(doc('LOCAL_FILE_BINDINGS.json') == {'schema': 'r17.source19.local-file-bindings.v1', 'sourceHead': head, 'files': bindings}, 'LOCAL_BINDING_SET')
    versions = {r: digest(m) for r, m in target_roles.items()}
    expected_summary = {'schema': 'r17.source19.unsigned-content.v1', 'status': 'UNSIGNED_ISOLATED_NOT_ACTIVATED', 'sourceHead': head, 'sourcePublicConfigDigest': PUBLIC, 'sourceConfigurationRevision': 19, 'expectedSourceDeliveryHash': DELIVERY, 'sourceReleaseId': SOURCE, 'targetReleaseId': TARGET, 'targetVersions': versions, 'roleCounts': {r: len(m['files']) for r, m in target_roles.items()}, 'uniqueFiles': len(rows), 'roleBindings': len(bindings), 'issuedAt': None, 'notAfter': None, 'plannedConfigurationRevision': None, 'reservedRevision20Authorized': False, 'maySign': False, 'mayInstall': False, 'mayActivate': False, 'mayChangeOwner': False, 'maySettleUnknown': False}
    require(doc('UNSIGNED_CONTENT.json') == expected_summary, 'UNSIGNED_SCOPE_OR_TOTALS')
    guards = {'schema': 'r17.source19.repair-preservation.v1', 'appRunnerSha256': BASE_REPAIRS['app/app-runner.mjs'], 'baseRepairFileHashes': BASE_REPAIRS.copy(), 'guardHashes': {}}
    require(rows['app/app-runner.mjs']['sha256'] == BASE_REPAIRS['app/app-runner.mjs'], 'APP_RUNNER_REPAIR_LOST')
    for name, (begin, end, pin) in GUARDS.items():
        text = read(package / 'payload' / name)[0].decode()
        require(text.count(begin) == text.count(end) == 1, 'REPAIR_SECTION_SHAPE')
        start = text.index(begin)
        require(sha(text[start:text.index(end, start)].encode()) == pin, 'PHYSICAL_SHUTDOWN_OR_RECOVERY_REPAIR_LOST')
        require(base_union.get(name) == BASE_REPAIRS[name], 'BASE_REPAIR_VERSION_DRIFT')
        guards['guardHashes'][name] = pin
    require(doc('REPAIR_GUARDS.json') == guards, 'REPAIR_RECEIPT_DRIFT')
    publisher = read(package / 'payload/release/publisher-bootstrap.mjs')[0].decode()
    match = re.search(r'export const REVIEWED_SOURCE_FILES=Object\.freeze\(\[(.*?)\]\);', publisher, re.S)
    require(match is not None, 'FREEZE_LIST')
    names = re.findall(r"'([^']+)'", match[1])
    require(names and len(names) == len(set(names)) and all(n in overlays for n in names), 'FREEZE_SCOPE')
    freeze = {'schema': 'mht.first-trust-code-freeze.v1', 'sourceCommit': head, 'files': {n: overlays[n] for n in sorted(names)}}
    require(doc('REVIEWED_SOURCE_FREEZE.json') == freeze and all(target_roles['native']['files'].get(n) == h for n, h in freeze['files'].items()), 'EXACT_NATIVE_FREEZE')
    identity_sources = {
        '/usr/lib/minimal-human-trust/authority/identity-admission.py': 'authority/identity-admission.py',
        '/usr/lib/minimal-human-trust/packaging/minimal-human-trust-identity-admission': 'packaging/minimal-human-trust-identity-admission',
        '/etc/systemd/system/minimal-human-trust-identity-admission.service': 'packaging/minimal-human-trust-identity-admission.service',
        '/usr/share/polkit-1/actions/org.jenn.r16.minimal-human-trust.identity-admission.policy': 'packaging/org.jenn.r16.minimal-human-trust.identity-admission.policy',
    }
    require(all(n in overlays for n in identity_sources.values()), 'IDENTITY_ADMISSION_EXACT_HEAD_REQUIRED')
    identity_freeze = {'schema': 'mht.identity-admission-code-freeze.v1', 'sourceCommit': head,
        'files': {p: overlays[n] for p, n in sorted(identity_sources.items())}}
    require(doc('IDENTITY_ADMISSION_FREEZE.json') == identity_freeze, 'IDENTITY_ADMISSION_FREEZE_DRIFT')
    provenance = doc('PROVENANCE.json')
    require(provenance['schema'] == 'r17.source19.provenance.v1' and provenance['sourceHead'] == head and provenance['sourcePublicConfigDigest'] == PUBLIC and provenance['sourceReleaseId'] == SOURCE and provenance['sourceVersions'] == VERSIONS and provenance['overlayFiles'] == overlays and provenance['sourceFreezeDigest'] == digest(freeze) and provenance['repairGuards'] == guards and provenance['baseFiles'] == len(base_union) and provenance['independentG1CryptoAndFresh19ReceiptRequired'] is True and provenance['sourceSignatureAuthority'] == 'EXACT_PUBLIC_DIGEST_VERIFIED_BY_EXTERNAL_G1' and provenance['liveConfigurationOrBusinessStateRead'] is False and provenance['rootMarkerRead'] is False and provenance['authority'] is False, 'PROVENANCE_SCOPE')
    require(metadata['SHA256SUMS_PAYLOAD.txt'].decode() == ''.join(rows[n]['sha256'] + '  payload/' + n + '\n' for n in sorted(rows)), 'EXACT_SHA256SUMS')
    live = None
    if repo is not None:
        require(provenance['baseDirectory'] == str(base), 'LIVE_BASE_PATH')
        live = provenance_check(repo, base, head, originals, rows, overlays, provenance['sourceRoleManifestPaths'])
    return {'schema': 'r17.source19.independent-package-verification.v1', 'status': 'PASS_UNSIGNED_PACKAGE_WITH_LIVE_PROVENANCE' if live else 'PASS_EXTERNALLY_PINNED_UNSIGNED_PACKAGE_BYTES', 'sourceHead': head, 'inventorySha256': inventory_hash, 'payloadFiles': len(rows), 'payloadBytes': total, 'roleBindings': len(bindings), 'targetVersions': versions, 'metadataSha256': {n: sha(raw) for n, raw in sorted(metadata.items())}, 'liveProvenance': live, 'source19CryptoAndFreshReadback': 'SEPARATE_G1_RECEIPT_REQUIRED', 'sourceRepairGuardsPreserved': True, 'controlledStaticRelativeImportClosureVerified': True, 'source19PublicConfigDigest': PUBLIC, 'signaturesIssued': 0, 'productionEffectsIssued': 0, 'businessAcceptance': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', required=True, type=Path)
    parser.add_argument('--inventory-sha256', required=True)
    parser.add_argument('--source-head', required=True)
    parser.add_argument('--repo', type=Path)
    parser.add_argument('--base', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.package, args.inventory_sha256, args.source_head, args.repo, args.base), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        print('{"status":"UNSIGNED_PACKAGE_VERIFICATION_REFUSED","productionEffectsIssued":0}')
        return 78


if __name__ == '__main__':
    raise SystemExit(main())
