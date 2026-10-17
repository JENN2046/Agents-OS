#!/usr/bin/env python3
"""Generate content-bound unsigned review objects. No native installation or signing API."""
import argparse
import hashlib
import json
import re
import stat
from pathlib import Path

PUBLIC = '56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec'
DELIVERY = 'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9'
TARGET = '/opt/r16/releases/r16-daily-20261012-r17'


def demand(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def file_sha(path):
    cursor = Path(path.anchor)
    for part in path.parts[1:]:
        cursor /= part
        st = cursor.lstat()
        demand(not stat.S_ISLNK(st.st_mode), 'SOURCE_LINK_REFUSED')
    st = path.lstat()
    demand(stat.S_ISREG(st.st_mode) and st.st_nlink == 1
           and st.st_size <= 128 * 1024 * 1024, 'SOURCE_NOT_REGULAR')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(name):
    demand(isinstance(name, str) and bool(name) and not name.startswith('/')
           and '\\' not in name and not any(ord(c) < 32 or ord(c) == 127 for c in name)
           and all(p not in ('', '.', '..') for p in name.split('/')), 'UNSAFE_RELATIVE_PATH')
    demand(not any(p in ('secrets', 'credentials', 'tokens', 'cookies', 'state-private', '.git')
                   or p.startswith('.env') for p in name.split('/'))
           and not name.endswith(('.key', '.pem', '.cred', '.p12', '.pfx', '.log')),
           'SENSITIVE_PATH_REFUSED')
    return name


def generate(delivery, package):
    meta = package / 'metadata'
    def read(path):
        file_sha(path)
        return json.loads(path.read_text())
    public = read(meta / 'SOURCE_PUBLIC_CONFIG.json')
    demand(digest(public) == PUBLIC, 'SOURCE19_PUBLIC_DRIFT')
    baseline = read(delivery / 'G1_FROZEN_SOURCE19_BASELINE.json')
    readiness = read(delivery / 'G4_FIRST_TRUST_READINESS.json')
    revisions = read(delivery / 'REVISION_INVENTORY.json')
    demand(baseline['configurationRevision'] == revisions['acceptedRevision'] == 19
           and baseline['publicConfigHash'] == PUBLIC
           and baseline['deliveryHash'] == DELIVERY, 'SOURCE19_BASELINE_DRIFT')
    demand(readiness['human']['realPublicKey'] is None
           and readiness['enrollmentAuthority']['realPublicKey'] is None
           and not readiness['signable'], 'REAL_KEY_ADMISSION_REQUIRES_NEW_REVIEW')
    inv = read(meta / 'PAYLOAD_INVENTORY.json')
    freeze = read(meta / 'REVIEWED_SOURCE_FREEZE.json')
    demand(inv['uniqueFiles'] == len(inv['files']), 'INVENTORY_COUNT_DRIFT')
    head = inv['sourceHead']
    demand(re.fullmatch('[a-f0-9]{40}', head) and freeze['sourceCommit'] == head,
           'SOURCE_HEAD_DRIFT')
    files = []
    targets = set()

    def bind(source, target, mode):
        demand(target.startswith(TARGET + '/')
               or target.startswith('/usr/lib/minimal-human-trust/')
               or target in fixed_targets, 'UNREVIEWED_TARGET')
        demand(target not in targets, 'DUPLICATE_TARGET')
        targets.add(target)
        demand(source.is_file() and not source.is_symlink(), 'SOURCE_NOT_REGULAR')
        files.append({'source': str(source.relative_to(package)), 'sha256': file_sha(source),
                      'bytes': source.stat().st_size, 'target': target,
                      'uid': 0, 'gid': 0, 'mode': mode, 'operation': 'EXCLUSIVE_CREATE_IF_ABSENT'})

    fixed = {
        'minimal-human-trust-proposal.service': '/etc/systemd/system/minimal-human-trust-proposal.service',
        'minimal-human-trust-publisher.service': '/etc/systemd/system/minimal-human-trust-publisher.service',
        'minimal-human-trust-approval.socket': '/etc/systemd/system/minimal-human-trust-approval.socket',
        'minimal-human-trust-approval@.service': '/etc/systemd/system/minimal-human-trust-approval@.service',
        'minimal-human-trust-approval.desktop': '/usr/share/applications/minimal-human-trust-approval.desktop',
        'minimal-human-trust-first-cutover.desktop': '/usr/share/applications/minimal-human-trust-first-cutover.desktop',
        'org.jenn.r16.minimal-human-trust.policy': '/usr/share/polkit-1/actions/org.jenn.r16.minimal-human-trust.policy',
    }
    fixed_targets = set(fixed.values()) | {
        '/etc/minimal-human-trust/first-trust-code.json',
        '/etc/minimal-human-trust/stage-installer-reviewed.mjs',
    }
    for name, row in sorted(inv['files'].items()):
        name = relative(name)
        source = package / 'payload' / name
        demand(file_sha(source) == row['sha256'], 'PAYLOAD_DRIFT')
        demand(row['mode'] in (0o644, 0o755)
               and stat.S_IMODE(source.lstat().st_mode) == row['mode'], 'PAYLOAD_MODE_DRIFT')
        bind(source, TARGET + '/' + name, format(row['mode'], '04o'))
    for role in ('app', 'bridge', 'native'):
        bind(meta / (role + '-manifest.json'), TARGET + '/' + role + '-manifest.json', '0644')
    for name, expected in sorted(freeze['files'].items()):
        name = relative(name)
        source = package / 'payload' / name
        demand(file_sha(source) == expected, 'FREEZE_SOURCE_DRIFT')
        bind(source, '/usr/lib/minimal-human-trust/' + name, '0644')
    bind(meta / 'REVIEWED_SOURCE_FREEZE.json', '/etc/minimal-human-trust/first-trust-code.json', '0600')
    bind(package / 'payload/release/stage-installer-reviewed.mjs',
         '/etc/minimal-human-trust/stage-installer-reviewed.mjs', '0644')
    for name, target in fixed.items():
        bind(package / 'payload/packaging' / name, target, '0644')
    forbidden = ['SIGN', 'KEY_GENERATE_OR_PROVISION', 'ENROLL', 'RELEASE_INSTALL_OR_SELECT',
                 'DAEMON_RELOAD', 'SERVICE_START_STOP_ENABLE', 'OWNER_SWITCH', 'GRANT_CHANGE',
                 'UNKNOWN_REPLAY_OR_SETTLEMENT', 'OLD_PLAN_RESUME_OR_DEADLINE_EXTENSION']
    preparation = {
        'schema': 'r17.source19.protected-code-preparation-review.v1',
        'status': 'CONTENT_BOUND_UNSIGNED_REVIEW_ONLY_WAIT_REAL_NATIVE_ADMISSION',
        'task': 'R17_SOURCE19_REBASE_AND_FIRST_TRUST_PREAUTH_R1', 'sourceHead': head,
        'authority': False, 'signable': False, 'executable': False,
        'trustModel': 'TRUSTED_HOST_ADMIN', 'host': 'jenn-System-Product-Name',
        'sourceRevision': 19, 'sourcePublicConfigHash': PUBLIC,
        'sourceDeliveryHash': baseline['deliveryHash'],
        'packageInventorySha256': file_sha(meta / 'PAYLOAD_INVENTORY.json'),
        'sourceFreezeHash': digest(freeze), 'targets': files,
        'contentRoot': digest(files),
        'allowedEffectsAfterSeparateNativeApproval': ['EXCLUSIVE_CREATE_ONLY_EXACT_NEW_CODE_AND_MANIFEST_FILES'],
        'forbiddenEffects': forbidden,
        'timeWindow': {'active': False, 'acceptedAt': None, 'expiresAt': None,
                       'maximumMsFromFutureNativeAcceptance': 300000,
                       'requireFreshSourceAndFullInventoryBeforeAcceptance': True,
                       'driftPolicy': 'REFUSE_WITHOUT_RENUMBERING_REHASHING_OR_RENEWAL'},
        'preconditions': ['Independent exact-head candidate acceptance passes',
                          'Actual foreground local administrator reviews exact complete target list and content root',
                          'All destination files remain absent; conflict refuses without overwrite',
                          'No previous request, approval, publication or cutover use at destination'],
        'rollbackBeforeAnyUse': {'scope': 'Only files exclusively created by the new approved preparation transaction',
                                'requires': ['Exact file identity, digest and ownership unchanged',
                                             'No Human request/intent/result, enrollment or publication usage exists'],
                                'actions': ['Preserve new operation evidence', 'Remove only authenticated newly created files'],
                                'ifUsedOrOutcomeUnknown': 'Preserve state and require a new exact reviewed recovery object; no old driver',
                                'serviceStartOrStop': False, 'restoreHistoricalLedger': False},
        'currentExecution': 'NO_NATIVE_INSTALL_ENTRY_EXECUTED_OR_AUTHORITY_CREATED',
        'businessAcceptance': False,
    }
    next_plan = max(revisions['acceptedRevision'], revisions['highestObservedSignedRevision'],
                    revisions['highestHistoricalReservedRevision']) + 1
    blocked = {
        'schema': 'r17.source19.production-approval-preauth-gaps.v1',
        'status': 'NON_SIGNABLE_NO_REAL_HUMAN_OR_ENROLLMENT_KEY_ADMISSION',
        'task': preparation['task'], 'sourceHead': head, 'authority': False,
        'signable': False, 'executable': False, 'sourceRevision': 19,
        'sourcePublicConfigHash': PUBLIC, 'sourceDeliveryHash': baseline['deliveryHash'],
        'packageInventorySha256': preparation['packageInventorySha256'],
        'sourceFreezeHash': preparation['sourceFreezeHash'],
        'protectedPreparationObjectHash': digest(preparation),
        'realKeysNotSubstituted': True, 'missingRealEvidence': [
            'Human canonical public SPKI, fingerprint and holder/source/possession admission',
            'Independent Enrollment authority canonical public SPKI and actual root admission',
            'Sealed credential provenance and exact public/private identity match under native key ceremony',
            'Protected candidate placement and exact short-lived signed pending proposal',
            'Real foreground local Human confirmation and durable exact OS result',
        ],
        'unsignedVersionPlanning': {'observedAcceptedRevision': 19,
                                   'observedKnownSignedMaximum': revisions['highestObservedSignedRevision'],
                                   'historicalReservedMaximum': revisions['highestHistoricalReservedRevision'],
                                   'candidateForward': next_plan, 'candidateRecovery': next_plan + 1,
                                   'oldReserved20IsAuthority': False,
                                   'notAllocatedOrSigned': True,
                                   'executionPrerequisite': 'Future admitted issuer delivery path must explicitly support this new plan; current automatic next revision is not accepted as proof',
                                   'freshNativeApprovalMustRecomputeAndRefuseDrift': True},
        'futureTimingPolicy': {'activeAuthority': False, 'maximumProposalAgeMs': 300000,
                              'newNonceAndRealNativeAcceptanceRequired': True,
                              'absoluteExpiry': None,
                              'dependencyCap': 'Minimum of fresh evidence/review, current source release, enrollment and newly approved action windows',
                              'oldRecoveryDeadlineInherited': False},
        'rollbackConditions': ['Preserve current source19 App/Native repair and current ledgers',
                               'Never restore stopped historical ledger bytes or replay UNKNOWN',
                               'Before Owner handoff, cancel unused stage without selecting target',
                               'After any future signature, ambiguous outcome or Owner fence, require its own admitted once-only recovery; never rerun old APPLY'],
        'ownerRetirement': 'Separate first-cutover native approval and actual single-writer/three-role/snapshot admission required; not performed here',
        'oldPlanRenewed': False, 'productionEffects': 0, 'businessAcceptance': False,
    }
    return preparation, blocked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery', type=Path, required=True)
    parser.add_argument('--package', type=Path, required=True)
    args = parser.parse_args()
    prepared, blocked = generate(args.delivery, args.package)
    for name, value in [('G5_PROTECTED_CODE_PREPARATION_REVIEW.json', prepared),
                        ('G5_PRODUCTION_APPROVAL_PREAUTH_GAPS.json', blocked)]:
        with (args.delivery / name).open('x') as f:
            json.dump(value, f, ensure_ascii=False, sort_keys=True, indent=2)
            f.write('\n')
    print(json.dumps({'status': 'UNSIGNED_REVIEW_OBJECTS_CREATED_NO_AUTHORITY',
                      'exactCodeTargets': len(prepared['targets']),
                      'contentRoot': prepared['contentRoot'], 'productionApprovalSignable': False}))


if __name__ == '__main__':
    main()
