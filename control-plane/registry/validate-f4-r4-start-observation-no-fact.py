#!/usr/bin/env python3
import hashlib, json
from pathlib import Path

P = Path(__file__).with_name("examples") / "2026-07-16-agents-os-f4-r4-start-observation-no-fact-vectors-v0.1.json"
raw = P.read_bytes()
d = json.loads(raw)
mapping = {
    "VALID_RESOLVED": ("FACT_INPUT_RESOLVED", "ACCEPTANCE_RESOLVED"),
    "VALID_NOT_FOUND": ("NO_FACT", "ACCEPTANCE_NOT_FOUND"),
    "VALID_LOOKUP_UNAVAILABLE": ("NO_FACT", "ACCEPTANCE_LOOKUP_UNAVAILABLE"),
    "VALID_INTEGRITY_CONFLICT": ("NO_FACT", "ACCEPTANCE_INTEGRITY_CONFLICT"),
    "INVALID": ("NO_FACT", "INVALID_ACCEPTANCE_REF"),
}
precedence = ["INTEGRITY_FAILURE", "HOST_UNAUTHENTICATED", "FENCED", "EPOCH_STALE", "EXPIRED", "SECRET_HANDLE_STALE", "ATTESTATION_STALE", "HUMAN_PRESENCE_STALE"]
for c in d["preflight_cases"]:
    assert mapping[c["ref_state"]] == (c["expected_outcome"], c["expected_reason"])
    assert (c["fingerprint"] is not None) == (c["expected_outcome"] == "FACT_INPUT_RESOLVED")
def reduce(states):
    negatives = [x for x in states if x in precedence]
    if negatives:
        return "NOT_STARTED", min(negatives, key=precedence.index)
    if "INDETERMINATE" in states:
        return "INDETERMINATE", "OBSERVATION_UNAVAILABLE"
    return "START_AUTHORITY_CURRENT", "ALL_RECHECKS_PASS"
for c in d["reducer_cases"]:
    assert reduce(c["states"]) == (c["expected_result"], c["expected_reason"])
assert d["forbidden_fact_reasons"] == ["ACCEPTANCE_MISSING"]
mutations = 0
for bad in [("NO_FACT", "ACCEPTANCE_RESOLVED", None), ("FACT_INPUT_RESOLVED", "ACCEPTANCE_NOT_FOUND", "a"*64), ("NO_FACT", "ACCEPTANCE_NOT_FOUND", "a"*64)]:
    outcome, reason, fingerprint = bad
    legal = (outcome == "FACT_INPUT_RESOLVED" and reason == "ACCEPTANCE_RESOLVED" and fingerprint is not None) or (outcome == "NO_FACT" and reason != "ACCEPTANCE_RESOLVED" and fingerprint is None)
    assert not legal
    mutations += 1
out = {"contract_version":d["contract_version"],"external_effect_count":0,"fixture_canonical_sha256":hashlib.sha256(json.dumps(d,sort_keys=True,separators=(",",":")).encode()).hexdigest(),"fixture_file_sha256":hashlib.sha256(raw).hexdigest(),"negative_mutations_rejected":mutations,"preflight_case_count":len(d["preflight_cases"]),"provider_call_count":0,"raw_secret_count":0,"reducer_case_count":len(d["reducer_cases"]),"result":"PASS","total_case_count":len(d["preflight_cases"])+len(d["reducer_cases"])}
print(json.dumps(out, sort_keys=True, separators=(",",":")))
