#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path('/tmp/phase5b-r5-independent-extract/workspace')
VP = ROOT / 'control-plane/registry/validate-phase-5b-m0b-plan-r5-strict-integer-witness.py'
FIX = ROOT / 'control-plane/registry/examples/2026-07-21-agents-os-phase-5b-m0b-plan-r5-strict-integer-witness-v0.1.json'


def module(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V = module(VP, 'independent_r5_validator')
base = json.loads(FIX.read_text())
TARGET = V.TARGET


def set_site(obj, site: str, value):
    if site == 'derived':
        obj['R4_fixture']['derived_sealed_binding']['claimed_principal_revision'] = value
    elif site == 'command':
        obj['R4_fixture']['R3_fixture']['F3']['command']['claimed_principal_revision'] = value
    elif site == 'both':
        set_site(obj, 'derived', value)
        set_site(obj, 'command', value)
    else:
        raise AssertionError(site)


rows = []
assert V.validate_semantics(base) == []
assert V.validate_fixed_fixture(base) == []
rows.append({'case_id': 'positive_integer_1_baseline', 'accepted': True})

invalid = [
    ('bool_true', True), ('bool_false', False), ('float_one', 1.0),
    ('float_zero', 0.0), ('null', None), ('string', '1'),
    ('array', [1]), ('object', {'value': 1}), ('zero', 0),
    ('negative', -1), ('other_integer', 2), ('unsafe_integer', 9007199254740992),
]
for site in ('derived', 'command', 'both'):
    for label, value in invalid:
        f = copy.deepcopy(base)
        set_site(f, site, value)
        V.resign(f)
        semantic = V.validate_semantics(f)
        seal = V.validate_fixed_fixture(f)
        ok = TARGET in semantic and seal == ['R5_FIXED_FIXTURE_SEAL_MISMATCH']
        rows.append({
            'case_id': f'{site}_{label}',
            'accepted': False,
            'target_semantic_rejected': ok,
            'semantic_errors': semantic,
            'seal_errors': seal,
        })
        assert ok, rows[-1]

# Independent positive control: rebuild and fully resign with legal integer 1.
f = copy.deepcopy(base)
set_site(f, 'both', 1)
V.resign(f)
assert V.validate_semantics(f) == []
rows.append({'case_id': 'positive_integer_1_fully_resigned', 'accepted': True})

# Caller-controlled observation cannot conceal an invalid consumed type.
f = copy.deepcopy(base)
set_site(f, 'command', True)
V.resign(f)
f['strict_integer_observations'][1].update(
    value=1, JSON_category='integer', host_type='int', strict_integer_one=True
)
f['root_fingerprint'] = V.digest([
    'agents-os.m0b.r5.strict-integer-root.v0.1',
    {k: v for k, v in f.items() if k != 'root_fingerprint'},
])
semantic = V.validate_semantics(f)
assert TARGET in semantic and 'R5_OBSERVATION_BINDING_INVALID' in semantic
rows.append({'case_id': 'forged_observation_cannot_hide_bool', 'target_semantic_rejected': True, 'semantic_errors': semantic})

# Wrapper/profile/root rewrites cannot alter the consumed primitive rule.
f = copy.deepcopy(base)
f['profile_fingerprint'] = '0' * 64
V.resign(f)
semantic = V.validate_semantics(f)
assert 'R5_PROFILE_FINGERPRINT_INVALID' in semantic
rows.append({'case_id': 'profile_wrapper_rewrite_rejected', 'semantic_rejected': True, 'semantic_errors': semantic})

# Boundary expansion remains rejected.
f = copy.deepcopy(base)
f['boundary']['implementation_authorized'] = True
V.resign(f)
semantic = V.validate_semantics(f)
assert 'R5_BOUNDARY_EXPANSION' in semantic
rows.append({'case_id': 'implementation_boundary_expansion_rejected', 'semantic_rejected': True, 'semantic_errors': semantic})

# Raw parser forms: exponent notation is a float and is rejected semantically.
f = copy.deepcopy(base)
set_site(f, 'command', 1.0)
V.resign(f)
raw = V.jcs(f) + b'\n'
needle = b'"claimed_principal_revision":1.0'
assert needle in raw
raw_exp = raw.replace(needle, b'"claimed_principal_revision":1e0', 1)
with tempfile.NamedTemporaryFile(suffix='.json') as tf:
    tf.write(raw_exp); tf.flush()
    parsed = V.strict_json(pathlib.Path(tf.name))
    semantic = V.validate_semantics(parsed)
assert TARGET in semantic
rows.append({'case_id': 'command_exponent_1e0', 'target_semantic_rejected': True, 'semantic_errors': semantic})

parser_rows = []
for case_id, raw_bad in [
    ('duplicate_key', b'{"x":1,"x":2}\n'),
    ('malformed', b'{"x":\n'),
    ('nan', b'{"x":NaN}\n'),
    ('infinity', b'{"x":Infinity}\n'),
    ('root_array', b'[]\n'),
]:
    with tempfile.NamedTemporaryFile(suffix='.json') as tf:
        tf.write(raw_bad); tf.flush()
        p = subprocess.run(['python3', str(VP), tf.name], cwd=ROOT, text=True, capture_output=True)
    ok = p.returncode == 1 and '"result": "BLOCK"' in p.stdout
    parser_rows.append({'case_id': case_id, 'stable_block': ok, 'returncode': p.returncode})
    assert ok, (case_id, p.returncode, p.stdout, p.stderr)

out = {
    'schema_version': 'agents-os.independent-case-results.v0.1',
    'review_unit': 'PHASE_5B_M0B_PLAN_BUILD_PROFILE_V0_1_R5_ATOMIC_BUNDLE',
    'result': 'PASS',
    'baseline_positive_controls': 2,
    'fully_resigned_invalid_cases': 36,
    'additional_coordinated_cases': 4,
    'parser_cases': parser_rows,
    'target_semantic_rejections': sum(bool(x.get('target_semantic_rejected')) for x in rows),
    'semantic_rejections_total': sum(bool(x.get('target_semantic_rejected') or x.get('semantic_rejected')) for x in rows),
    'favorable_invalid_path_count': 0,
    'legal_input_over_rejection_count': 0,
    'uncaught_exception_count': 0,
    'rows': rows,
}
print(json.dumps(out, sort_keys=True, indent=2))
