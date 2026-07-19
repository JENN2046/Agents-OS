#!/usr/bin/env python3
"""Fresh independent coordinated re-signing probe for the F8 R5 review bundle.

The probe reads only an extracted package, imports the hash-bound validators,
mutates deep copies, and never edits review subjects.
"""
from __future__ import annotations
import argparse, copy, hashlib, importlib.util, json, math, os, subprocess, tempfile
from pathlib import Path
from typing import Any, Callable

EXPECTED_R2_FIXTURE_SHA256 = "36d60ffc0ff0b184c7d306b6293601a3661a22affe1cab8b00da609cb280f501"
EXPECTED_R2_VALIDATOR_SHA256 = "9ac243f7aecc0519da5b5bb7266cd604260894861f2c4a3edf98039adbaba65d"
FAVORABLE = {"CANDIDATE_FORMED", "ACKNOWLEDGED_COMMITTED"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


class Probe:
    def __init__(self, package: Path):
        self.package = package
        self.v = load_module("f8_r5_review_subject", package / "validator/validate-f8-r5-witness.py")
        self.v2 = load_module("f8_r2_review_subject", package / "validator/validate-f8-r2-witness.py")
        self.fixture = load_json(package / "fixture/F8-R5-synthetic-witness.json")
        self.r2 = load_json(package / "fixture/F8-R2-synthetic-witness.json")
        self.records: list[dict[str, Any]] = []
        self.direct_controls: list[dict[str, Any]] = []
        if sha(package / "fixture/F8-R2-synthetic-witness.json") != EXPECTED_R2_FIXTURE_SHA256:
            raise RuntimeError("R2 fixture hash mismatch")
        if sha(package / "validator/validate-f8-r2-witness.py") != EXPECTED_R2_VALIDATOR_SHA256:
            raise RuntimeError("R2 validator hash mismatch")

    def resign(self, f: dict[str, Any]) -> None:
        v = self.v
        for row in f.get("schema_inventory", []):
            if isinstance(row, dict) and "schema_fingerprint" in row:
                row["schema_fingerprint"] = v.digest(v.DOMAIN + ":schema", v.without(row, "schema_fingerprint"))
        for row in f.get("trusted_H01_owner_commitment_source", []):
            if isinstance(row, dict) and "commitment_fingerprint" in row:
                row["commitment_fingerprint"] = v.digest(v.DOMAIN + ":trusted-owner-commitment", v.without(row, "commitment_fingerprint"))
        rows = f.get("merged_H01_derivation_cases", [])
        if isinstance(rows, list):
            for merged in rows:
                if not isinstance(merged, dict):
                    continue
                for row in merged.get("owner_commitment_resolutions", []) if isinstance(merged.get("owner_commitment_resolutions"), list) else []:
                    if isinstance(row, dict) and "row_fingerprint" in row:
                        row["row_fingerprint"] = v.digest(v.DOMAIN + ":owner-resolution", v.without(row, "row_fingerprint"))
                if "row_fingerprint" in merged:
                    merged["row_fingerprint"] = v.digest(v.DOMAIN + ":merged-H01-derivation", v.without(merged, "row_fingerprint"))
        for row in f.get("stable_ref_vectors", []):
            if isinstance(row, dict) and "row_fingerprint" in row:
                row["row_fingerprint"] = v.digest(v.DOMAIN + ":stable-ref-vector", v.without(row, "row_fingerprint"))
        names = ["schema_inventory", "trusted_H01_owner_commitment_source", "merged_H01_derivation_cases", "stable_ref_vectors", "boundary_assertions"]
        if isinstance(f.get("section_fingerprints"), dict) and all(name in f for name in names):
            f["section_fingerprints"] = {name: v.digest(v.DOMAIN + ":section:" + name, f[name]) for name in names}
        if "root_fingerprint" in f:
            f["root_fingerprint"] = v.digest(v.DOMAIN + ":root", v.without(f, "root_fingerprint"))

    def validate(self, f: dict[str, Any]) -> tuple[list[str], str | None]:
        try:
            errors = self.v.validate_fixture(f, self.r2, self.v2)
            result = None
            try:
                result = f["merged_H01_derivation_cases"][0]["derived_decision"]["result"]
            except Exception:
                pass
            return errors, result
        except Exception as exc:
            return [f"stable BLOCK ({type(exc).__name__}): {exc}"], None

    def record(self, attack_id: str, title: str, f: dict[str, Any], target: str | None = None,
               category: str = "fully_resigned_attack", invalid: bool = True,
               legal_input: bool = False, notes: str | None = None) -> None:
        self.resign(f)
        errors, result = self.validate(f)
        accepted = not errors
        target_hit = True if target is None else any(target in e for e in errors)
        favorable_invalid = bool(invalid and accepted and result in FAVORABLE)
        legal_over = bool(legal_input and not accepted)
        stale_markers = [e for e in errors if any(x in e.lower() for x in ("row fingerprint mismatch", "section_fingerprints", "root_fingerprint"))]
        passed = (accepted if not invalid else (not accepted and target_hit)) and not legal_over
        self.records.append({
            "attack_id": attack_id, "category": category, "title": title,
            "fully_resigned": category == "fully_resigned_attack",
            "invalid_graph": invalid, "legal_input": legal_input,
            "accepted": accepted, "observed_result": result,
            "expected_error_substring": target, "target_error_observed": target_hit,
            "errors": errors[:20], "stale_hash_errors": stale_markers,
            "rejection_class": None if accepted else ("stale_hash_or_unpropagated_dependency" if stale_markers else "target_contract_semantic_or_fixed_anchor"),
            "favorable_invalid_path": favorable_invalid,
            "legal_input_over_rejection": legal_over,
            "passed": passed, "notes": notes,
        })

    def source(self, f: dict[str, Any], role: str) -> dict[str, Any]:
        return next(x for x in f["trusted_H01_owner_commitment_source"] if x["role"] == role)

    def consumer(self, f: dict[str, Any], role: str) -> dict[str, Any]:
        return f["merged_H01_derivation_cases"][0]["upgraded_consumers"][role]

    def resolution(self, f: dict[str, Any], role: str) -> dict[str, Any]:
        return next(x for x in f["merged_H01_derivation_cases"][0]["owner_commitment_resolutions"] if x["role"] == role)

    def sync_resolution_consumer(self, f: dict[str, Any], role: str) -> None:
        self.resolution(f, role)["consumer"] = copy.deepcopy(self.consumer(f, role))

    def positive_controls(self) -> None:
        errors, result = self.validate(copy.deepcopy(self.fixture))
        self.records.append({
            "attack_id":"PC01","category":"positive_control","title":"canonical fixed R5 fixture",
            "fully_resigned":False,"invalid_graph":False,"legal_input":True,"accepted":not errors,
            "observed_result":result,"expected_error_substring":None,"target_error_observed":True,
            "errors":errors,"stale_hash_errors":[],"rejection_class":None,
            "favorable_invalid_path":False,"legal_input_over_rejection":bool(errors),"passed":not errors and result=="CANDIDATE_FORMED","notes":None,
        })
        tests = [
            ("PC02","NFC internal-space stable_ref", "synthetic://owner commitment/h01", True),
            ("PC03","all-whitespace nonempty stable_ref", "   ", True),
            ("PC04","non-NFC stable_ref", "synthetic://cafe\u0301", False),
            ("PC05","empty stable_ref", "", False),
            ("PC06","integer stable_ref", 1, False),
            ("PC07","null stable_ref", None, False),
        ]
        for pid,title,value,expected in tests:
            actual=self.v.stable_ref(value)
            self.direct_controls.append({"probe_id":pid,"title":title,"value_repr":repr(value),"expected":expected,"actual":actual,"passed":actual is expected})

    def run(self) -> None:
        self.positive_controls()
        b=self.fixture
        # Exact consumer commitment substitutions.
        for idx,(field,repl,target) in enumerate([
            ("owner_commitment_ref","synthetic://attacker/commitment@1","exact owner commitment mismatch"),
            ("expected_owner_commitment_revision",2,"exact owner commitment mismatch"),
            ("expected_owner_commitment_fingerprint","f"*64,"exact owner commitment mismatch"),
        ],1):
            f=copy.deepcopy(b); c=self.consumer(f,"f7_intent_currentness"); c[field]=repl; self.sync_resolution_consumer(f,"f7_intent_currentness")
            self.record(f"R5-A{idx:03d}",f"consumer {field} substitution",f,target)
        n=4
        # Cross-role exact commitment tuple.
        f=copy.deepcopy(b); src=self.consumer(f,"actor_identity"); c=self.consumer(f,"f7_intent_currentness")
        for k in self.v.CONSUMER_FIELDS[3:]: c[k]=src[k]
        self.sync_resolution_consumer(f,"f7_intent_currentness")
        self.record(f"R5-A{n:03d}","cross-role commitment tuple substitution",f,"exact owner commitment mismatch"); n+=1
        # Fully coordinated source + consumer + resolution rewrite, including graph-local anchor.
        f=copy.deepcopy(b); s=self.source(f,"f7_intent_currentness"); s["commitment_ref"]="synthetic://attacker/source/rewrite@1"
        s["issued_event_ref"]="synthetic://attacker/event/rewrite"; s["issued_event_sequence"]+=5
        event={"owner_contract":s["owner_contract"],"role":s["role"],"assessment_id":s["assessment_id"],"assessment_revision":s["assessment_revision"],"issued_event_ref":s["issued_event_ref"],"issued_event_sequence":s["issued_event_sequence"]}
        s["issued_event_fingerprint"]=self.v.digest(self.v.DOMAIN+":owner-issued-event",event)
        s["commitment_fingerprint"]=self.v.digest(self.v.DOMAIN+":trusted-owner-commitment",self.v.without(s,"commitment_fingerprint"))
        c=self.consumer(f,"f7_intent_currentness"); c["owner_commitment_ref"]=s["commitment_ref"]; c["expected_owner_commitment_fingerprint"]=s["commitment_fingerprint"]
        r=self.resolution(f,"f7_intent_currentness"); r["consumer"]=copy.deepcopy(c); r["resolved_commitment_ref"]=s["commitment_ref"]; r["resolved_commitment_fingerprint"]=s["commitment_fingerprint"]
        f["merged_H01_derivation_cases"][0]["trusted_owner_source_anchor"]=self.v.digest(self.v.DOMAIN+":trusted-owner-source-anchor",f["trusted_H01_owner_commitment_source"])
        self.record(f"R5-A{n:03d}","coordinated source consumer resolution and graph-anchor rewrite",f,"immutable trusted anchor mismatch"); n+=1
        # Source inventory attacks.
        for title,mut,target in [
            ("trusted source row deletion",lambda rows: rows.pop(),"expected seven rows"),
            ("trusted source row duplication",lambda rows: rows.append(copy.deepcopy(rows[-1])),"expected seven rows"),
            ("trusted source row reorder",lambda rows: rows.reverse(),"canonical role order mismatch"),
        ]:
            f=copy.deepcopy(b); mut(f["trusted_H01_owner_commitment_source"]); f["merged_H01_derivation_cases"][0]["trusted_owner_source_anchor"]=self.v.digest(self.v.DOMAIN+":trusted-owner-source-anchor",f["trusted_H01_owner_commitment_source"])
            self.record(f"R5-A{n:03d}",title,f,target); n+=1
        # Claimed result and authority projection attacks.
        decision_attacks=[
            ("result","REJECTED","claimed decision not independently derived"),
            ("primary_reason","UPSTREAM_CURRENTNESS_UNAVAILABLE","claimed decision not independently derived"),
            ("reason_codes",["UPSTREAM_CURRENTNESS_UNAVAILABLE"],"claimed decision not independently derived"),
            ("runtime_usable",True,"claimed decision not independently derived"),
            ("command_authority",True,"claimed decision not independently derived"),
            ("task_write_authority",True,"claimed decision not independently derived"),
            ("effect_authority",True,"claimed decision not independently derived"),
            ("F3_recheck_required",False,"claimed decision not independently derived"),
            ("F3_command_ref","synthetic://attacker/command","claimed decision not independently derived"),
            ("F3_intake_ref","synthetic://attacker/intake","claimed decision not independently derived"),
        ]
        for field,repl,target in decision_attacks:
            f=copy.deepcopy(b); f["merged_H01_derivation_cases"][0]["derived_decision"][field]=repl
            self.record(f"R5-A{n:03d}",f"derived decision {field} forgery",f,target); n+=1
        # Assessment tuple changes against fixed source and fixed R2 downprojection.
        for field,repl in [
            ("assessment_id","synthetic://attacker/assessment"),
            ("expected_assessment_revision",2),
            ("expected_assessment_fingerprint","e"*64),
        ]:
            f=copy.deepcopy(b); self.consumer(f,"actor_identity")[field]=repl; self.sync_resolution_consumer(f,"actor_identity")
            self.record(f"R5-A{n:03d}",f"R2 assessment tuple {field} substitution",f,"committed assessment mismatch"); n+=1
        # Source semantic fields coordinated inside caller graph.
        source_changes=[
            ("owner_contract","ATTACKER"),
            ("assessment_id","synthetic://attacker/assessment"),
            ("assessment_revision",2),
            ("assessment_fingerprint","a"*64),
            ("issued_event_ref","synthetic://attacker/event"),
            ("issued_event_sequence",999),
        ]
        for field,repl in source_changes:
            f=copy.deepcopy(b); s=self.source(f,"f7_intent_currentness"); s[field]=repl
            # Recompute event and commitment, propagate all consumer/resolution fields that can follow.
            event={"owner_contract":s["owner_contract"],"role":s["role"],"assessment_id":s["assessment_id"],"assessment_revision":s["assessment_revision"],"issued_event_ref":s["issued_event_ref"],"issued_event_sequence":s["issued_event_sequence"]}
            s["issued_event_fingerprint"]=self.v.digest(self.v.DOMAIN+":owner-issued-event",event)
            s["commitment_fingerprint"]=self.v.digest(self.v.DOMAIN+":trusted-owner-commitment",self.v.without(s,"commitment_fingerprint"))
            c=self.consumer(f,"f7_intent_currentness")
            c.update({"assessment_id":s["assessment_id"],"expected_assessment_revision":s["assessment_revision"],"expected_assessment_fingerprint":s["assessment_fingerprint"],"owner_commitment_ref":s["commitment_ref"],"expected_owner_commitment_revision":s["commitment_revision"],"expected_owner_commitment_fingerprint":s["commitment_fingerprint"]})
            r=self.resolution(f,"f7_intent_currentness"); r["consumer"]=copy.deepcopy(c); r["resolved_commitment_ref"]=s["commitment_ref"]; r["resolved_commitment_revision"]=s["commitment_revision"]; r["resolved_commitment_fingerprint"]=s["commitment_fingerprint"]
            f["merged_H01_derivation_cases"][0]["trusted_owner_source_anchor"]=self.v.digest(self.v.DOMAIN+":trusted-owner-source-anchor",f["trusted_H01_owner_commitment_source"])
            self.record(f"R5-A{n:03d}",f"coordinated trusted source {field} rewrite",f,"immutable trusted anchor mismatch"); n+=1
        # Schema inventory, exact-field and wrong-type attacks.
        schema_attacks: list[tuple[str,Callable[[dict[str,Any]],None],str]] = [
            ("unknown root field",lambda f:f.__setitem__("unknown_root",False),"exact fields required"),
            ("missing root contract_id",lambda f:f.pop("contract_id"),"exact fields required"),
            ("unknown source field",lambda f:self.source(f,"actor_identity").__setitem__("unknown",0),"exact fields required"),
            ("missing source field",lambda f:self.source(f,"actor_identity").pop("issued_event_ref"),"exact fields required"),
            ("unknown consumer field",lambda f:self.consumer(f,"actor_identity").__setitem__("unknown",0),"exact fields required"),
            ("missing consumer field",lambda f:self.consumer(f,"actor_identity").pop("assessment_id"),"exact fields required"),
            ("unknown resolution field",lambda f:self.resolution(f,"actor_identity").__setitem__("unknown",0),"owner resolution inventory not independently derived"),
            ("missing resolution field",lambda f:self.resolution(f,"actor_identity").pop("resolution"),"owner resolution inventory not independently derived"),
            ("unknown merged field",lambda f:f["merged_H01_derivation_cases"][0].__setitem__("unknown",0),"exact fields required"),
            ("missing merged field",lambda f:f["merged_H01_derivation_cases"][0].pop("source_case_id"),"exact fields required"),
            ("unknown stable vector field",lambda f:f["stable_ref_vectors"][0].__setitem__("unknown",0),"exact fields required"),
            ("unknown boundary field",lambda f:f["boundary_assertions"].__setitem__("unknown",0),"exact fields required"),
            ("boolean as commitment revision",lambda f:self.consumer(f,"actor_identity").__setitem__("expected_owner_commitment_revision",True),"positive safe integer required"),
            ("float commitment revision",lambda f:self.consumer(f,"actor_identity").__setitem__("expected_owner_commitment_revision",1.0),"float forbidden"),
            ("unsafe commitment revision",lambda f:self.consumer(f,"actor_identity").__setitem__("expected_owner_commitment_revision",9007199254740992),"integer outside JSON safe range"),
            ("uppercase commitment fingerprint",lambda f:self.consumer(f,"actor_identity").__setitem__("expected_owner_commitment_fingerprint","A"*64),"lowercase SHA-256 required"),
            ("short commitment fingerprint",lambda f:self.consumer(f,"actor_identity").__setitem__("expected_owner_commitment_fingerprint","a"*63),"lowercase SHA-256 required"),
            ("empty commitment ref",lambda f:self.consumer(f,"actor_identity").__setitem__("owner_commitment_ref",""),"stable_ref required"),
            ("null commitment ref mixed tuple",lambda f:self.consumer(f,"actor_identity").__setitem__("owner_commitment_ref",None),"MIXED_NULL_INVALID"),
            ("integer commitment ref",lambda f:self.consumer(f,"actor_identity").__setitem__("owner_commitment_ref",1),"stable_ref required"),
            ("non-NFC commitment ref",lambda f:self.consumer(f,"actor_identity").__setitem__("owner_commitment_ref","synthetic://cafe\u0301"),"non-NFC string"),
            ("unknown environment",lambda f:f.__setitem__("environment","ATTACKER"),"synthetic boundary mismatch"),
            ("root runtime usable",lambda f:f.__setitem__("runtime_usable",True),"synthetic boundary mismatch"),
        ]
        for title,mut,target in schema_attacks:
            f=copy.deepcopy(b); mut(f)
            # Keep mirrored resolution consumer coherent when possible.
            if "consumer" in title or "commitment" in title:
                try:self.sync_resolution_consumer(f,"actor_identity")
                except Exception:pass
            self.record(f"R5-A{n:03d}",title,f,target); n+=1
        # R4 nullability totality: all 62 mixed-null patterns on optional consumer.
        valid=copy.deepcopy(self.consumer(b,"actor_identity")); fields=list(self.v.CONSUMER_FIELDS)
        for mask in range(1,63):
            f=copy.deepcopy(b); c={field:(valid[field] if (mask & (1<<i)) else None) for i,field in enumerate(fields)}
            f["merged_H01_derivation_cases"][0]["upgraded_consumers"]["jenn_exact_decision"]=c
            self.sync_resolution_consumer(f,"jenn_exact_decision")
            self.record(f"R5-A{n:03d}",f"mixed-null optional consumer mask {mask:02d}",f,"MIXED_NULL_INVALID"); n+=1
        # All-null on required role and optional lookup/resolution tampering.
        f=copy.deepcopy(b); null={k:None for k in fields}; f["merged_H01_derivation_cases"][0]["upgraded_consumers"]["actor_identity"]=null; self.sync_resolution_consumer(f,"actor_identity")
        self.record(f"R5-A{n:03d}","all-null required consumer",f,"expected ALL_NON_NULL"); n+=1
        f=copy.deepcopy(b); r=self.resolution(f,"jenn_exact_decision"); r["owner_lookup_performed"]=True
        self.record(f"R5-A{n:03d}","optional all-null owner lookup forged true",f,"owner resolution inventory not independently derived"); n+=1
        f=copy.deepcopy(b); r=self.resolution(f,"jenn_exact_decision"); r["resolved_commitment_ref"]="synthetic://attacker/commitment"
        self.record(f"R5-A{n:03d}","optional all-null resolved commitment forged",f,"owner resolution inventory not independently derived"); n+=1
        # Boundary occurrence attacks.
        for field in sorted(self.v.BOUNDARY_FIELDS - {"terminal_outcome"}):
            f=copy.deepcopy(b); f["boundary_assertions"][field]=1
            self.record(f"R5-A{n:03d}",f"nonzero boundary {field}",f,"integer zero required"); n+=1
        f=copy.deepcopy(b); f["boundary_assertions"]["terminal_outcome"]="EXECUTED"
        self.record(f"R5-A{n:03d}","forged terminal outcome",f,"NOT_EXECUTED required"); n+=1
        # Fixed input tamper probes through the actual CLI hash gates.
        with tempfile.TemporaryDirectory(prefix="f8-r5-fixed-input-") as td:
            td=Path(td)
            tampered_r2=td/"r2.json"; obj=copy.deepcopy(self.r2); obj["contract_id"]="ATTACKER"; tampered_r2.write_text(json.dumps(obj),encoding="utf-8")
            cmd=["python3",str(self.package/"validator/validate-f8-r5-witness.py"),str(self.package/"fixture/F8-R5-synthetic-witness.json"),"--r2-fixture",str(tampered_r2),"--r2-validator",str(self.package/"validator/validate-f8-r2-witness.py")]
            p=subprocess.run(cmd,text=True,capture_output=True)
            self.records.append({"attack_id":f"R5-A{n:03d}","category":"fixed_input_attack","title":"tampered fixed R2 fixture","fully_resigned":False,"invalid_graph":True,"legal_input":False,"accepted":p.returncode==0,"observed_result":None,"expected_error_substring":"R2 fixture hash mismatch","target_error_observed":"R2 fixture hash mismatch" in p.stdout,"errors":[p.stdout.strip(),p.stderr.strip()],"stale_hash_errors":[],"rejection_class":"fixed_input_hash","favorable_invalid_path":p.returncode==0,"legal_input_over_rejection":False,"passed":p.returncode!=0 and "R2 fixture hash mismatch" in p.stdout,"notes":None}); n+=1
            tampered_v2=td/"v2.py"; tampered_v2.write_bytes((self.package/"validator/validate-f8-r2-witness.py").read_bytes()+b"\n# tamper\n")
            cmd=["python3",str(self.package/"validator/validate-f8-r5-witness.py"),str(self.package/"fixture/F8-R5-synthetic-witness.json"),"--r2-fixture",str(self.package/"fixture/F8-R2-synthetic-witness.json"),"--r2-validator",str(tampered_v2)]
            p=subprocess.run(cmd,text=True,capture_output=True)
            self.records.append({"attack_id":f"R5-A{n:03d}","category":"fixed_input_attack","title":"tampered fixed R2 validator","fully_resigned":False,"invalid_graph":True,"legal_input":False,"accepted":p.returncode==0,"observed_result":None,"expected_error_substring":"R2 validator hash mismatch","target_error_observed":"R2 validator hash mismatch" in p.stdout,"errors":[p.stdout.strip(),p.stderr.strip()],"stale_hash_errors":[],"rejection_class":"fixed_input_hash","favorable_invalid_path":p.returncode==0,"legal_input_over_rejection":False,"passed":p.returncode!=0 and "R2 validator hash mismatch" in p.stdout,"notes":None}); n+=1
        # Parser probes.
        parser_samples=[("duplicate-key",'{"a":1,"a":2}'),("NaN",'{"a":NaN}'),("Infinity",'{"a":Infinity}'),("float",'{"a":1.5}')]
        for name,text in parser_samples:
            rejected=False; err=None
            try:
                value=json.loads(text,object_pairs_hook=self.v.strict_object,parse_constant=self.v.reject_constant)
                local=[]; self.v.validate_json_value(value,"$",local); rejected=bool(local); err=local[0] if local else None
            except Exception as exc:
                rejected=True; err=f"{type(exc).__name__}: {exc}"
            self.records.append({"attack_id":f"P-{name}","category":"parser_probe","title":name,"fully_resigned":False,"invalid_graph":True,"legal_input":False,"accepted":not rejected,"observed_result":None,"expected_error_substring":None,"target_error_observed":rejected,"errors":[err] if err else [],"stale_hash_errors":[],"rejection_class":"parser_or_primitive_schema","favorable_invalid_path":not rejected,"legal_input_over_rejection":False,"passed":rejected,"notes":None})


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("package",type=Path); ap.add_argument("--output",type=Path)
    args=ap.parse_args(); p=Probe(args.package); p.run()
    records=p.records
    summary={
        "coordinated_probe_count":len(records)+len(p.direct_controls),
        "independent_fully_resigned_attack_count":sum(r["fully_resigned"] for r in records),
        "fixed_input_attack_count":sum(r["category"]=="fixed_input_attack" for r in records),
        "parser_probe_count":sum(r["category"]=="parser_probe" for r in records),
        "positive_control_count":1+len(p.direct_controls),
        "favorable_invalid_path_count":sum(r["favorable_invalid_path"] for r in records),
        "legal_input_over_rejection_count":sum(r["legal_input_over_rejection"] for r in records)+sum(not x["passed"] and x["expected"] for x in p.direct_controls),
        "unexpected_probe_failure_count":sum(not r["passed"] for r in records)+sum(not x["passed"] for x in p.direct_controls),
        "stale_hash_rejection_count":sum(bool(r["stale_hash_errors"]) for r in records),
        "uncaught_exception_count":sum(any(str(e).startswith("stable BLOCK") for e in r["errors"]) for r in records),
    }
    out={"schema_version":"agents-os.f8-r5-independent-attack-results.v0.1","review_unit":"F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R5_ATOMIC_BUNDLE","summary":summary,"direct_stable_ref_controls":p.direct_controls,"attacks":records}
    text=json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    if args.output: args.output.write_text(text,encoding="utf-8")
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0 if summary["favorable_invalid_path_count"]==0 and summary["legal_input_over_rejection_count"]==0 and summary["unexpected_probe_failure_count"]==0 else 1

if __name__=="__main__": raise SystemExit(main())
