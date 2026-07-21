#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path('/home/jenn/AGENTS_OS_Workspace')
VALIDATOR = ROOT / 'control-plane/registry/validate-phase-5b-m0b-plan-r1-witness.py'
FIXTURE = ROOT / 'control-plane/registry/examples/2026-07-21-agents-os-phase-5b-m0b-plan-r1-synthetic-witness-v0.1.json'
OUT = Path('/tmp/2026-07-21-agents-os-phase-5b-m0b-plan-r1-independent-case-results.json')

spec = importlib.util.spec_from_file_location('m0b_r1_validator', VALIDATOR)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)
baseline = mod.load_strict(FIXTURE)

records = []

def fully_resigned(name, mutate, expected='REJECT'):
    value = copy.deepcopy(baseline)
    mutate(value)
    mod.resign(value)
    errors = mod.validate(value)
    accepted = not errors
    records.append({
        'case_id': name,
        'kind': 'fully_resigned_attack',
        'expected': expected,
        'accepted': accepted,
        'target_semantic_rejection': bool(errors),
        'error_count': len(errors),
        'errors': errors[:8],
    })

fully_resigned('A01_replace_no_promotion_case_with_favorable', lambda v: v['case_catalog'][5].update({
    'raw_input': copy.deepcopy(v['case_catalog'][7]['raw_input']),
    'derived_output': copy.deepcopy(v['case_catalog'][7]['derived_output']),
}))
fully_resigned('A02_implicit_life_stream_favorable', lambda v: v['case_catalog'][6].update({
    'derived_output': copy.deepcopy(v['case_catalog'][7]['derived_output'])
}))
fully_resigned('A03_implicit_memory_favorable', lambda v: v['case_catalog'][11].update({
    'derived_output': copy.deepcopy(v['case_catalog'][10]['derived_output'])
}))
fully_resigned('A04_implicit_intent_favorable', lambda v: v['case_catalog'][13].update({
    'derived_output': copy.deepcopy(v['case_catalog'][12]['derived_output'])
}))
fully_resigned('A05_phantom_handoff_without_request', lambda v: v['case_catalog'][12].update({
    'derived_output': copy.deepcopy(v['case_catalog'][14]['derived_output'])
}))
fully_resigned('A06_F3_commit_without_F8_candidate', lambda v: v['case_catalog'][12]['raw_input'].update({
    'f3_outcome': 'SYNTHETIC_TEST_COMMITTED'
}))
fully_resigned('A07_Home_direct_Task_write_favorable', lambda v: v['case_catalog'][18].update({
    'derived_output': copy.deepcopy(v['case_catalog'][0]['derived_output'])
}))
fully_resigned('A08_Home_direct_Command_commit_favorable', lambda v: v['case_catalog'][19].update({
    'derived_output': copy.deepcopy(v['case_catalog'][0]['derived_output'])
}))
fully_resigned('A09_relationship_authority_favorable', lambda v: v['case_catalog'][20].update({
    'derived_output': copy.deepcopy(v['case_catalog'][0]['derived_output'])
}))
fully_resigned('A10_PBL_no_match_permission_favorable', lambda v: v['case_catalog'][21].update({
    'derived_output': copy.deepcopy(v['case_catalog'][0]['derived_output'])
}))
fully_resigned('A11_raw_content_favorable', lambda v: v['case_catalog'][22].update({
    'derived_output': copy.deepcopy(v['case_catalog'][0]['derived_output'])
}))
fully_resigned('A12_formal_Memory_write_favorable', lambda v: v['case_catalog'][23].update({
    'derived_output': copy.deepcopy(v['case_catalog'][10]['derived_output'])
}))
fully_resigned('A13_production_profile_favorable', lambda v: v['case_catalog'][24].update({
    'derived_output': copy.deepcopy(v['case_catalog'][0]['derived_output'])
}))
fully_resigned('A14_stale_upstream_favorable', lambda v: v['case_catalog'][25].update({
    'derived_output': copy.deepcopy(v['case_catalog'][0]['derived_output'])
}))
fully_resigned('A15_F8_rejected_favorable', lambda v: v['case_catalog'][26].update({
    'derived_output': copy.deepcopy(v['case_catalog'][14]['derived_output'])
}))
fully_resigned('A16_F8_indeterminate_favorable', lambda v: v['case_catalog'][27].update({
    'derived_output': copy.deepcopy(v['case_catalog'][14]['derived_output'])
}))
fully_resigned('A17_make_runtime_usable', lambda v: v['profile'].update({'runtime_usable': True}))
fully_resigned('A18_make_production_compatible', lambda v: v['profile'].update({'production_compatible': True}))
fully_resigned('A19_add_second_writer_boundary_key', lambda v: v['boundary_assertions'].update({'second_writer': False}))
fully_resigned('A20_authorize_implementation', lambda v: v['boundary_assertions'].update({'implementation_authorized': True}))
fully_resigned('A21_add_unknown_raw_private_field', lambda v: v['case_catalog'][0]['raw_input'].update({'private_memory_payload': 'x'}))
fully_resigned('A22_replace_case_id', lambda v: v['case_catalog'][0].update({'case_id': 'C99'}))
fully_resigned('A23_swap_case_order', lambda v: v['case_catalog'].__setitem__(slice(0,2), [v['case_catalog'][1],v['case_catalog'][0]]))
fully_resigned('A24_nonzero_real_Command', lambda v: v['integrated_witness'].update({'real_Command_count': 1}))
fully_resigned('A25_nonzero_provider_call', lambda v: v['integrated_witness'].update({'provider_call_count': 1}))
fully_resigned('A26_unknown_root_service', lambda v: v.update({'sidecar_enabled': False}))

# Parser-level attacks are not "fully re-signed" because duplicate keys and
# floats are rejected before a semantic graph exists.
parser_records = []
raw = FIXTURE.read_text(encoding='utf-8')
for name, payload in [
    ('P01_duplicate_root_key', raw[:-2] + ',"schema_version":"x"}\n'),
    ('P02_float', raw.replace('"ordinal":1', '"ordinal":1.0', 1)),
    ('P03_NaN', raw.replace('"ordinal":1', '"ordinal":NaN', 1)),
    ('P04_non_NFC', raw.replace('C01_EPHEMERAL_ONLY', 'Cafe\u0301', 1)),
]:
    path = Path('/tmp') / f'{name}.json'
    path.write_text(payload, encoding='utf-8')
    try:
        value = mod.load_strict(path)
        errors = mod.validate(value)
        rejected = bool(errors)
        detail = errors[:4]
    except Exception as exc:
        rejected = True
        detail = [f'{type(exc).__name__}: {exc}']
    parser_records.append({'case_id': name, 'kind': 'parser_probe', 'rejected': rejected, 'detail': detail})

# Exact baseline/source compatibility checks. These are independently derived
# from the sealed Phase 5A source bytes, not from author claims.
command_intake = (ROOT/'extensions/agents-os-resident/src/reducers/command_intake.rs').read_text()
napi_frame = (ROOT/'extensions/agents-os-resident/src/napi_frame.rs').read_text()
profile = (ROOT/'control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-build-profile-v0.1-r1.yaml').read_text()
source_checks = {
    'new_command_type_present_in_closed_registry': 'M0_SYNTHETIC_SUBMIT_HOME_INTENT' in command_intake,
    'new_command_type_present_in_NAPI_dispatch': 'M0_SYNTHETIC_SUBMIT_HOME_INTENT' in napi_frame,
    'command_payload_can_bind_handoff_tuple': all(x in command_intake for x in ['handoff_candidate_ref','handoff_candidate_revision','handoff_candidate_fingerprint']),
    'command_intake_rs_in_modify_inventory': 'extensions/agents-os-resident/src/reducers/command_intake.rs' in profile,
    'napi_frame_rs_in_modify_inventory': 'extensions/agents-os-resident/src/napi_frame.rs' in profile,
    'profile_requires_no_napi_frame_change': 'NAPI_frame_change_expected: false' in profile,
}

out = {
    'schema_version': 'agents-os.phase-5b-m0b-plan-r1-independent-probes.v0.1',
    'fixture_sha256': hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
    'fully_resigned_attack_count': len(records),
    'fully_resigned_attack_rejected_count': sum(not r['accepted'] for r in records),
    'favorable_invalid_path_count': sum(r['accepted'] for r in records),
    'parser_probe_count': len(parser_records),
    'parser_probe_rejected_count': sum(r['rejected'] for r in parser_records),
    'records': records,
    'parser_records': parser_records,
    'sealed_source_compatibility': source_checks,
}
OUT.write_text(json.dumps(out, ensure_ascii=True, sort_keys=True, indent=2)+'\n', encoding='ascii')
print(json.dumps({k:v for k,v in out.items() if k not in {'records','parser_records'}}, indent=2))
