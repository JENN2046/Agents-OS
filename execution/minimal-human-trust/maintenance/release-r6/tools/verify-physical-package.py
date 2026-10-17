#!/usr/bin/python3
"""Independent, non-privileged offline R6 byte verifier. No builder imports."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from cryptography.hazmat.primitives.serialization import load_der_public_key, Encoding, PublicFormat
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey, Ed25519PrivateKey

BASE = Path('/opt/r16/releases/r16-daily-20261012-r15')
PUBLIC_DIGEST = 'be3ff2b5125f8212206d2848bb32889c3c6b50a8ca56aa3b1a4bc4359591bbdb'
COMMIT = '0cd4ed954052557341c9c8687febc62076d56a22'
TARGET = 'r16-daily-20261015-r15-app-recovery-r6'
DELTAS = {
    'app/workspace-host.mjs': 'bfef60223b8fd186f2e96887b770678777bf99ff2a5c84a3c36273d8f172a6ab',
    'app/app-runner.mjs': 'feaf51d26f5ef56cdfe013b65fe3faef37f91bc26391835810deb655e51f14d7',
    'host/workspace-dispatcher.mjs': 'ba4ef78187a8701b97bd03461faed44771c4d71b8541681a6d573e3f35ed079c',
}
VERSIONS = {
    'app': '34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500',
    'bridge': '9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',
    'native': '2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4',
}
METADATA = {'BASE_ROLE_MANIFESTS.json', 'CANDIDATE.json', 'PAYLOAD_INVENTORY.json',
            'R15_PUBLIC_CONFIG.json', 'SHA256SUMS_PAYLOAD.txt',
            'app-manifest.json', 'bridge-manifest.json', 'native-manifest.json'}


class Refused(Exception):
    pass


def require(value, code):
    if not value:
        raise Refused(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    """R16 JSON with independent UTF-16 property ordering, no number coercion."""
    if value is None or isinstance(value, (str, bool)):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    if isinstance(value, int):
        require(abs(value) <= 9007199254740991, 'NONCANONICAL_NUMBER')
        return str(value)
    if isinstance(value, list):
        return '[' + ','.join(canonical(v) for v in value) + ']'
    require(type(value) is dict and all(isinstance(k, str) for k in value), 'NONCANONICAL_JSON')
    keys = sorted(value, key=lambda k: k.encode('utf-16-be', 'surrogatepass'))
    return '{' + ','.join(canonical(k) + ':' + canonical(value[k]) for k in keys) + '}'


def digest(value):
    return sha(canonical(value).encode('utf-8'))


def parse(raw):
    def pairs(rows):
        result = {}
        for k, v in rows:
            require(k not in result, 'DUPLICATE_JSON_KEY')
            result[k] = v
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(Refused('JSON_CONSTANT')))


def relative(name):
    require(isinstance(name, str) and name and '\\' not in name and '\0' not in name
            and not name.startswith('/') and all(p not in ('', '.', '..') for p in name.split('/')),
            'UNSAFE_RELATIVE_PATH')
    require(not any(p in ('__proto__', 'constructor', 'prototype') for p in name.split('/')), 'UNSAFE_PROPERTY_PATH')
    return name


def read_regular(root, name):
    relative(name)
    path = root
    for component in name.split('/'):
        path /= component
        require(not stat.S_ISLNK(path.lstat().st_mode), 'SYMLINK_REFUSED')
    require(stat.S_ISREG(path.lstat().st_mode), 'UNSAFE_FILE')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and not before.st_mode & 0o7022 and before.st_size <= 64 * 1024 * 1024,
                'UNSAFE_FILE')
        chunks = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        raw = b''.join(chunks)
        after = os.fstat(fd)
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        require(identity(before) == identity(after) and len(raw) == before.st_size, 'FILE_CHANGED')
        return raw, stat.S_IMODE(before.st_mode)
    finally:
        os.close(fd)


def tree(root):
    require(root.is_dir() and not root.is_symlink(), 'ROOT_NOT_DIRECTORY')
    require(not root.lstat().st_mode & 0o7022, 'UNSAFE_DIRECTORY')
    found = set()
    for directory, directories, files in os.walk(root, followlinks=False):
        for name in directories:
            s = (Path(directory) / name).lstat()
            require(stat.S_ISDIR(s.st_mode) and not s.st_mode & 0o7022, 'UNSAFE_DIRECTORY')
        for name in files:
            rel = (Path(directory) / name).relative_to(root).as_posix()
            relative(rel)
            found.add(rel)
    return found


def b64(value):
    require(isinstance(value, str) and re.fullmatch('[A-Za-z0-9_-]+', value), 'INVALID_BASE64URL')
    raw = base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))
    require(base64.urlsafe_b64encode(raw).decode().rstrip('=') == value, 'NONCANONICAL_BASE64URL')
    return raw


def signed(envelope, public_key, schema):
    require(type(envelope) is dict and set(envelope) == {'body', 'signature'}
            and envelope['body'].get('schema') == schema, 'ENVELOPE_INVALID')
    key = load_der_public_key(b64(public_key))
    require(isinstance(key, Ed25519PublicKey), 'KEY_TYPE_INVALID')
    signature = b64(envelope['signature'])
    require(len(signature) == 64, 'SIGNATURE_LENGTH_INVALID')
    try:
        key.verify(signature, b'R16-SIGNED\0' + canonical(envelope['body']).encode())
    except Exception as exc:
        raise Refused('SIGNATURE_INVALID') from exc
    return envelope['body']


def verify(root):
    require(root.is_absolute() and root == Path(os.path.normpath(root)), 'ABSOLUTE_ROOT_REQUIRED')
    require(tree(root) == {'metadata/' + n for n in METADATA} |
            {'payload/' + n for n in tree(root / 'payload')}, 'PACKAGE_LAYOUT_DRIFT')
    rawmeta = {}
    for name in METADATA:
        raw, mode = read_regular(root, 'metadata/' + name)
        require(mode == 0o644, 'METADATA_MODE_DRIFT')
        rawmeta[name] = raw
    meta = {name: parse(raw) for name, raw in rawmeta.items() if name.endswith('.json')}
    public = meta['R15_PUBLIC_CONFIG.json']
    require(digest(public) == PUBLIC_DIGEST, 'SOURCE_PUBLIC_CONFIG_DRIFT')
    release = signed(public['release'], public['releasePublicKey'], 'r16.release.v1')
    grant = signed(public['grant'], public['issuerPublicKey'], 'r16.workspace.v1')
    require(release['id'] == BASE.name and grant['id'] == 'r16-projects-daily'
            and grant['version'] == 1 and grant['peers'] == public['peers']
            and grant['channel'] == public['channel'] and release['versions'] == public['versions']
            and release['actions'] == grant['actions'], 'ORIGINAL_AUTHORITY_BINDING_DRIFT')
    base = meta['BASE_ROLE_MANIFESTS.json']
    require(set(base) == set(VERSIONS), 'BASE_ROLES_DRIFT')
    union = {}
    bindings = 0
    for role in VERSIONS:
        original, current = base[role], meta[role + '-manifest.json']
        entry = {'app': 'app/app-runner.mjs', 'bridge': 'bridge/bridge-runner.mjs', 'native': 'host/native-runner.mjs'}[role]
        for manifest in (original, current):
            require(set(manifest) == {'schema', 'role', 'entry', 'files'}
                    and manifest['schema'] == 'r16.runtime-code.v1' and manifest['role'] == role
                    and manifest['entry'] == entry and entry in manifest['files'], 'ROLE_MANIFEST_INVALID')
        require(digest(original) == public['versions'][role], 'BASE_ROLE_SIGNATURE_BINDING_DRIFT')
        require(digest(current) == VERSIONS[role], 'TARGET_ROLE_VERSION_DRIFT')
        require(set(original['files']) == set(current['files']), 'ROLE_FILE_SET_DRIFT')
        for name, pin in original['files'].items():
            relative(name)
            require(re.fullmatch('[a-f0-9]{64}', pin) and (name not in union or union[name] == pin), 'BASE_FILE_OVERLAP_CONFLICT')
            union[name] = pin
            require(current['files'][name] == DELTAS.get(name, pin), 'NONREVIEWED_ROLE_DELTA')
        bindings += len(original['files'])
    require(len(union) == 12592 and bindings == 16591 and set(DELTAS) <= set(union), 'FILE_COUNTS_DRIFT')
    inventory = meta['PAYLOAD_INVENTORY.json']
    require(set(inventory) == set(union) == tree(root / 'payload'), 'PAYLOAD_SET_DRIFT')
    hashes, total, baseline_total, changed = {}, 0, 0, []
    for name in sorted(union):
        raw, mode = read_regular(root, 'payload/' + name)
        # Modes are absent from signed role manifests; independently read only
        # the original public file metadata and code bytes at the fixed base.
        original, original_mode = read_regular(BASE, name)
        require(sha(original) == union[name], 'ORIGINAL_BASE_BYTES_DRIFT')
        row, actual = inventory[name], sha(raw)
        require(set(row) == {'baselineSha256', 'bytes', 'mode', 'sha256', 'source'}, 'INVENTORY_FIELDS_DRIFT')
        require(actual == DELTAS.get(name, union[name]) and row['sha256'] == actual
                and type(row['bytes']) is int and row['bytes'] == len(raw)
                and type(row['mode']) is int and row['mode'] == mode == original_mode
                and row['baselineSha256'] == union[name], 'PAYLOAD_BYTES_OR_MODE_DRIFT')
        require(row['source'] == ('REVIEWED_R15_BACKPORT' if name in DELTAS else 'VERIFIED_SIGNED_R15_REUSE'), 'PROVENANCE_LABEL_DRIFT')
        if actual != union[name]:
            changed.append(name)
        hashes[name], total = actual, total + len(raw)
        baseline_total += len(original)
    require(set(changed) == set(DELTAS) and total == 149502002 and baseline_total == 149497453, 'BYTE_COUNTS_OR_DELTA_DRIFT')
    sums = ''.join(hashes[n] + '  ' + n + '\n' for n in sorted(hashes)).encode()
    require(rawmeta['SHA256SUMS_PAYLOAD.txt'] == sums, 'SHA256SUMS_DRIFT')
    candidate = meta['CANDIDATE.json']
    require(candidate['schema'] == 'g1d.r15-app-recovery-physical-candidate.v1'
            and candidate['status'] == 'ISOLATED_UNSIGNED_NOT_AUTHORIZED_FOR_INSTALL'
            and candidate['sourceFixCommit'] == COMMIT and candidate['proposedReleaseId'] == TARGET
            and candidate['changedFiles'] == sorted(DELTAS) and candidate['changedFileSha256'] == DELTAS
            and candidate['originalVersions'] == public['versions'] and candidate['candidateVersions'] == VERSIONS
            and candidate['baseReleaseId'] == BASE.name and candidate['basePublicConfigDigest'] == PUBLIC_DIGEST
            and candidate['payloadInventoryHash'] == digest(hashes)
            and candidate['payloadUniqueFiles'] == 12592 and candidate['roleBindings'] == 16591
            and candidate['payloadBytes'] == total and candidate['baseBytes'] == baseline_total,
            'CANDIDATE_SUMMARY_DRIFT')
    for field in ('authority', 'maySign', 'mayInstall', 'mayStartServices', 'maySettleUnknown', 'mayReplayUnknown', 'originalUnknownSettlementIncluded'):
        require(candidate[field] is False, 'AUTHORITY_CLAIM_DRIFT')
    require(candidate['issuerGrantKeysPeersAndScopeUnchanged'] is True
            and all(candidate[f] is None for f in ('releaseIssuedAt', 'releaseNotAfter', 'releaseSignature')), 'UNSIGNED_BOUNDARY_DRIFT')
    return {'schema': 'r16.app-recovery-r6-independent-physical-verification.v1',
            'result': 'PACKAGE_BYTES_PASS', 'packageRoot': str(root), 'sourceCommit': COMMIT,
            'originalReleaseAndGrantSignaturesVerified': True,
            'originalPublicConfigDigest': PUBLIC_DIGEST, 'targetReleaseId': TARGET,
            'filesVerified': len(hashes), 'originalFilesUnchanged': len(hashes) - len(changed),
            'roleBindingsVerified': bindings, 'payloadBytesVerified': total,
            'payloadInventoryHash': digest(hashes), 'candidateVersions': VERSIONS,
            'reviewedDeltaSha256': DELTAS,
            'metadataSha256': {n: sha(rawmeta[n]) for n in sorted(rawmeta)},
            'originalPublicBaselineCodeAndModesIndependentlyVerified': True,
            'baselineCodeReadRoot': str(BASE),
            'installationPreflight': {'result': 'BLOCKED_OLD_APP_STOP_UNPROVEN',
                'reason': 'Original running R15 App uses strict business close before listener close. Original UNKNOWN can block graceful exit. New package bytes do not modify a running old process.',
                'requiresActualStoppedProof': True, 'requiresMainAndControlPidZero': True,
                'requiresEmptyServiceCgroup': True, 'forceTerminationAuthorized': False},
            'productionAcceptance': False, 'authority': False, 'maySign': False,
            'mayInstall': False, 'mayReplayOrSettleUnknown': False}


def self_test():
    require(canonical({'\ue000': 1, '\U00010000': 2}) == '{"\U00010000":2,"\ue000":1}', 'UTF16_SORT_TEST')
    try:
        parse(b'{"x":1,"x":2}')
        raise AssertionError('duplicate accepted')
    except Refused:
        pass
    key = Ed25519PrivateKey.generate()
    encode = lambda raw: base64.urlsafe_b64encode(raw).decode().rstrip('=')
    public = encode(key.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo))
    body = {'schema': 'isolated.verifier-test.v1', 'value': 'synthetic'}
    envelope = {'body': body, 'signature': encode(key.sign(b'R16-SIGNED\0' + canonical(body).encode()))}
    require(signed(envelope, public, body['schema']) == body, 'VALID_SIGNATURE_TEST')
    wrong = bytearray(b64(envelope['signature']))
    wrong[0] ^= 1
    try:
        signed({**envelope, 'signature': encode(wrong)}, public, body['schema'])
        raise AssertionError('corrupt signature accepted')
    except Refused as error:
        require(str(error) == 'SIGNATURE_INVALID', 'BAD_SIGNATURE_TEST')
    with tempfile.TemporaryDirectory(prefix='r6-verifier-') as directory:
        root = Path(directory)
        (root / 'f').write_bytes(b'fixture')
        (root / 'f').chmod(0o644)
        os.mkfifo(root / 'fifo', 0o600)
        try:
            read_regular(root, 'fifo')
            raise AssertionError('FIFO accepted')
        except Refused:
            pass
        require(read_regular(root, 'f') == (b'fixture', 0o644), 'READ_TEST')
        (root / 'f').chmod(0o664)
        try:
            read_regular(root, 'f')
            raise AssertionError('writable mode accepted')
        except Refused:
            pass
        (root / 'f').chmod(0o644)
        (root / 's').symlink_to('f')
        for name in ('s',):
            try:
                read_regular(root, name)
                raise AssertionError('symlink accepted')
            except Refused:
                pass
        os.link(root / 'f', root / 'h')
        try:
            read_regular(root, 'f')
            raise AssertionError('hardlink accepted')
        except Refused:
            pass
    return {'selfTest': 'PASS', 'cases': 9}


def main():
    require(os.geteuid() != 0, 'NON_PRIVILEGED_VERIFICATION_REQUIRED')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        require(args.root is None and args.report is None, 'SELF_TEST_ARGUMENTS')
        print(json.dumps(self_test()))
        return
    require(args.root is not None and args.report is not None and args.report.is_absolute(), 'ROOT_AND_NEW_REPORT_REQUIRED')
    require(not args.report.exists() and not args.report.is_symlink(), 'REPORT_EXISTS')
    result = verify(args.root)
    result['verifierSha256'] = sha(Path(__file__).read_bytes())
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
    fd = os.open(args.report, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
    except Exception:
        raise
    print(json.dumps({'result': result['result'], 'filesVerified': result['filesVerified'],
                      'reportSha256': sha(raw), 'installationPreflight': result['installationPreflight']['result']}))


if __name__ == '__main__':
    try:
        main()
    except Refused as error:
        print(json.dumps({'result': 'REFUSED', 'code': str(error)}))
        sys.exit(1)
    except Exception:
        print(json.dumps({'result': 'REFUSED', 'code': 'INVALID_OR_UNREADABLE_INPUT'}))
        sys.exit(1)
