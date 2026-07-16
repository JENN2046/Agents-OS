#!/usr/bin/env python3
import hashlib, json
from pathlib import Path

P=Path(__file__).with_name("examples")/"2026-07-16-agents-os-f4-r5-cross-phase-authority-closure-vectors-v0.1.json"
raw=P.read_bytes(); d=json.loads(raw)
def authorization(c):
    if c["policy"]=="PROHIBITED": return "PROHIBITED"
    if c["policy"]=="EXACT_JENN" and not c["Jenn"]: return "REJECTED"
    return "ISSUABLE"
def host(c):
    return "AUTHENTICATED" if (c["actor"],c["principal"],c["binding"])==("EXECUTION_HOST_ACTIVE","HOST_PROCESS_ACTIVE","ACTIVE_MATCH") else "REJECTED"
def handoff(c):
    if c["authority"]=="REJECTED": return "AUTHORITY_STALE"
    if c["host"]=="REJECTED": return "HOST_UNAUTHENTICATED"
    if c["fence"]=="REJECTED": return "FENCED"
    if "INDETERMINATE" in (c["authority"],c["host"],c["fence"]): return "INDETERMINATE"
    return "START_AUTHORITY_CURRENT"
def effect(c):
    return "EXECUTABLE" if (c["claim"],c["time"],c["authority"])==("FIRST","CURRENT","CURRENT") else "NOT_EXECUTABLE"
def grant(c):
    if c["containment"]=="UNAVAILABLE": return "INDETERMINATE"
    return "VALID" if (c["definition"],c["operation"],c["containment"])==("CURRENT","KNOWN","PROVED") else "REJECTED"
def invocation(c): return "VALID" if (c["max_invocations"],c["ordinal"])==(1,1) else "REJECTED"
groups=[("authorization_cases",authorization),("host_cases",host),("handoff_cases",handoff),("effect_boundary_cases",effect),("grant_cases",grant),("invocation_cases",invocation)]
for name,fn in groups:
    for c in d[name]: assert fn(c)==c["expected"],c["id"]
mutations=0
for c in [dict(d["authorization_cases"][3],expected="ISSUABLE"),dict(d["host_cases"][1],expected="AUTHENTICATED"),dict(d["effect_boundary_cases"][2],expected="EXECUTABLE"),dict(d["invocation_cases"][1],expected="VALID")]:
    name=next(n for n,_ in groups if c["id"] in {x["id"] for x in d[n]})
    fn=dict(groups)[name]
    assert fn(c)!=c["expected"]; mutations+=1
assert d["expected_external_effect_count"]==d["expected_provider_call_count"]==d["expected_raw_secret_count"]==0
counts={name:len(d[name]) for name,_ in groups}
out={"contract_version":d["contract_version"],"external_effect_count":0,"fixture_canonical_sha256":hashlib.sha256(json.dumps(d,sort_keys=True,separators=(",",":")).encode()).hexdigest(),"fixture_file_sha256":hashlib.sha256(raw).hexdigest(),"negative_mutations_rejected":mutations,"provider_call_count":0,"raw_secret_count":0,"result":"PASS","total_case_count":sum(counts.values()),**counts}
print(json.dumps(out,sort_keys=True,separators=(",",":")))
