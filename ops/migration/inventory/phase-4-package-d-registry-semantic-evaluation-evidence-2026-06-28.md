# Phase 4 Package D Registry Semantic Evaluation Evidence - 2026-06-28

Status: Package D evaluation evidence collection completed with an exact
structured read of `control-plane/registry/WORKSPACE_REGISTRY.yaml`.

Notice: This evidence is not registry acceptance, not validator execution, not a
consumer integration proof, not schema validation, and not authorization to edit
registry data, parse registry examples, change executable bits, or perform
remote, branch, release, deploy, sync, secret, private-state, runtime, or
project-repository actions.

## Authorization

User authorization:

```text
授权 Package D evaluation evidence collection，允许 exact structured read of WORKSPACE_REGISTRY.yaml，只产出 rule result evidence/receipt，不改 registry。
```

Authorized scope:

- perform an exact structured read of
  `control-plane/registry/WORKSPACE_REGISTRY.yaml`
- evaluate Package B registry semantic rules against the scoped authority
  registry and supporting README/path evidence
- create this evidence file
- create a matching receipt
- do not edit `control-plane/registry/WORKSPACE_REGISTRY.yaml`
- do not execute validators
- do not parse registry examples

## Inputs Rechecked

| Input | SHA-256 | Mode | Use |
| --- | --- | --- | --- |
| `ops/migration/plans/phase-4-package-d-registry-semantic-evaluation-authorization-plan-2026-06-28.md` | `5d1c1ba567a4c90ef999f1de3496fd69e836954310b2979dcb0f5c52794bebf5` | `644` | Package D authorization shape. |
| `ops/migration/plans/phase-4-package-b-registry-semantic-rules-plan-2026-06-28.md` | `d14e95efd4fe69042aaa5fb186c3229cfe4f1695961c67f9d50734ae7f2c9ab7` | `644` | Rule plan authority. |
| `ops/migration/receipts/rules-assets-phase-4-package-b-registry-semantic-rules-review-closeout-receipt-2026-06-28.md` | `7d095bc46910c37eb2f6bcdab2b02da51761154be866f87e831395024b9b2001` | `644` | Package B closeout authority. |
| `ops/migration/inventory/phase-4-package-c-registry-yaml-parse-evidence-2026-06-28.md` | `8530a4645b0aeeca3eed7bde7d706e7383df8c634b875f904dd5ebea6393c6e7` | `644` | Parse-only evidence. |
| `ops/migration/receipts/rules-assets-phase-4-package-c-registry-yaml-parse-review-closeout-receipt-2026-06-28.md` | `a2e8c7af0a2d77ebfd8e206801b39f43539c95eb28a89aa7bbc6b203219b75de` | `644` | Package C closeout authority. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | `644` | Exact structured-read target. |
| `control-plane/registry/README.md` | `2a14a146acc36f6dbd1bc3f64f80d3193b554017612924d5a404a4f32d5fe753` | `644` | Registry boundary wording. |
| Evidence target before creation | n/a | n/a | Target was absent before creation. |
| Receipt target before creation | n/a | n/a | Target was absent before creation. |
| Workspace Git state | n/a | n/a | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Evaluation Method

| Item | Result |
| --- | --- |
| Structured read target | `control-plane/registry/WORKSPACE_REGISTRY.yaml` only. |
| Parser | Python `3.12.3`, PyYAML `6.0.1`, `yaml.safe_load`. |
| Top-level type | `dict`. |
| Top-level keys | `workspace`, `layers`, `repositories`, `security`. |
| Supporting reads | `control-plane/registry/README.md` and fixed path existence checks. |
| Registry examples parsed | No. |
| Validator executed | No. |
| Registry edited | No. |
| Result labels | `PASS`, `FAIL`, `WARNING`, `DEFERRED`, `NOT_EVALUATED`. |

## Result Counts

| Result | Count |
| --- | ---: |
| `PASS` | 28 |
| `FAIL` | 0 |
| `WARNING` | 4 |
| `DEFERRED` | 3 |
| `NOT_EVALUATED` | 1 |
| Total rule rows | 36 |

No `FAIL` result was found inside this authorized rule-evaluation subset. This
does not equal registry acceptance.

## Rule Results

| Rule | Family | Result | Summary | Evidence |
| --- | --- | --- | --- | --- |
| `AUTH-001` | Authority Location And Copy Policy | `PASS` | Active authority path remains `control-plane/registry/WORKSPACE_REGISTRY.yaml`. | `workspace.authority_path` equals the active registry path. |
| `AUTH-002` | Authority Location And Copy Policy | `PASS` | Root-level `WORKSPACE_REGISTRY.yaml` remains absent. | Fixed-path existence check. |
| `AUTH-003` | Authority Location And Copy Policy | `PASS` | `governance/WORKSPACE_REGISTRY.yaml` remains absent. | Fixed-path existence check. |
| `AUTH-004` | Authority Location And Copy Policy | `PASS` | Registry example files remain under `examples/` and README marks them example-only. | `extensions.example.yaml` and `protected-paths.example.yaml` are under `control-plane/registry/examples/`. |
| `AUTH-005` | Authority Location And Copy Policy | `WARNING` | Windows root value is present as reference metadata; no active execution use was evaluated. | `workspace.windows_reference_root` is present. |
| `STRUCT-001` | Required Top-Level Structure | `PASS` | Registry defines `workspace`, `layers`, `repositories`, and `security`. | Structured top-level keys checked. |
| `STRUCT-002` | Required Top-Level Structure | `PASS` | `workspace` includes required identity, root, authority, policy, and note fields. | Checked `name`, `owner`, `canonical_root`, `authority_path`, `purpose`, `default_branch_policy`, `remote_action_authorization`, and `registry_notes`. |
| `STRUCT-003` | Required Top-Level Structure | `PASS` | `layers` is a list whose entries include `id` and `path`. | `layer_count=11`. |
| `STRUCT-004` | Required Top-Level Structure | `PASS` | `repositories` is a list whose entries include names, layers, policies, and URL metadata roles. | `repository_count=6`. |
| `STRUCT-005` | Required Top-Level Structure | `PASS` | `security` defines `default_forbidden` and `registry_authorizes`. | Structured security keys checked. |
| `LAYER-001` | Layer Semantics | `PASS` | Layer IDs are unique. | `ids=11`, `unique=11`. |
| `LAYER-002` | Layer Semantics | `PASS` | Layer paths are relative and do not escape the workspace. | `checked_paths=11`, `bad_paths=0`. |
| `LAYER-003` | Layer Semantics | `PASS` | `state_private` remains private and not public-pushable. | `private: true`; `must_not_push_publicly: true`. |
| `LAYER-004` | Layer Semantics | `PASS` | `archive` remains read-only by default. | `read_only_by_default: true`. |
| `LAYER-005` | Layer Semantics | `PASS` | `execution` remains disabled by default. | `default_enabled: false`. |
| `LAYER-006` | Layer Semantics | `PASS` | `extensions` continues to require manifests. | `requires_manifest: true`. |
| `LAYER-007` | Layer Semantics | `NOT_EVALUATED` | `must_not_contain` contradiction review was intentionally not evaluated. | Requires subjective policy review beyond the exact structured-value gate. |
| `REPO-001` | Repository Declaration Semantics | `PASS` | Every repository entry references an existing layer ID. | Repository layers are within declared layer IDs. |
| `REPO-002` | Repository Declaration Semantics | `PASS` | Repository URLs remain metadata only and do not imply remote authorization. | `url_role: metadata_only` and registry notes checked. |
| `REPO-003` | Repository Declaration Semantics | `PASS` | Repository policy is bounded by registry notes that deny remote side effects. | Registry notes deny fetch, pull, clone, push, release, and deploy authorization. |
| `REPO-004` | Repository Declaration Semantics | `WARNING` | Optional repository descriptions are absent for all six entries; warning only. | `missing_description_count=6`. |
| `SEC-001` | Security And Permission Defaults | `PASS` | `default_forbidden` includes required high-risk capabilities. | No required item missing. |
| `SEC-002` | Security And Permission Defaults | `PASS` | `registry_authorizes.remote_actions` is false. | Structured flag checked. |
| `SEC-003` | Security And Permission Defaults | `PASS` | `registry_authorizes.validation_execution` is false. | Structured flag checked. |
| `SEC-004` | Security And Permission Defaults | `PASS` | `registry_authorizes.executable_bit_changes` is false. | Structured flag checked. |
| `SEC-005` | Security And Permission Defaults | `PASS` | `registry_authorizes.permission_expansion` is false. | Structured flag checked. |
| `SEC-006` | Security And Permission Defaults | `WARNING` | URL metadata boundary is in registry notes; path metadata boundary is in README, not `registry_notes`. | Clarity warning; no authority expansion observed. |
| `CONS-001` | Consumer Declaration Semantics | `PASS` | Registry and README wording do not claim runtime consumer integration from static data alone. | README boundary wording checked. |
| `CONS-002` | Consumer Declaration Semantics | `WARNING` | `validate-workspace.sh` remains implemented/unexecuted for this package; runtime verification is not claimed. | Static README wording only. |
| `CONS-003` | Consumer Declaration Semantics | `DEFERRED` | Prompt catalog behavior remains outside this structured registry evaluation. | Requires prompt catalog evidence. |
| `CONS-004` | Consumer Declaration Semantics | `DEFERRED` | Extension loader behavior remains outside this structured registry evaluation. | Requires loader inspection. |
| `CONS-005` | Consumer Declaration Semantics | `DEFERRED` | Governance runtime enforcement remains outside this structured registry evaluation. | Requires runtime/governance inspection. |
| `EX-001` | Example Boundary And Secret Hygiene | `PASS` | Example registry files stay under `control-plane/registry/examples/`. | Fixed-path example directory review. |
| `EX-002` | Example Boundary And Secret Hygiene | `PASS` | Example files are not active authority. | README examples-versus-authority wording checked. |
| `EX-003` | Example Boundary And Secret Hygiene | `PASS` | Authority registry contains no live secret-like matches in scoped scan. | Redacted match count: `0`. |
| `EX-004` | Example Boundary And Secret Hygiene | `PASS` | Registry may contain paths, identifiers, policy names, variable names, and metadata-style URL roles. | README allowed-name boundary and registry `url_role` checked. |

## Warnings

| Rule | Warning |
| --- | --- |
| `AUTH-005` | Windows reference root exists as metadata; no active execution use was evaluated. |
| `REPO-004` | Optional repository descriptions are absent for six entries. |
| `SEC-006` | URL metadata boundary is directly in registry notes; path metadata boundary is in README rather than `registry_notes`. |
| `CONS-002` | Validator file existence and wording were reviewed, but runtime execution remains unverified. |

## Deferred Or Not Evaluated

| Rule | Status | Reason |
| --- | --- | --- |
| `LAYER-007` | `NOT_EVALUATED` | Subjective `must_not_contain` contradiction review was outside the exact structured-value gate. |
| `CONS-003` | `DEFERRED` | Prompt catalog behavior requires prompt catalog evidence. |
| `CONS-004` | `DEFERRED` | Extension loader behavior requires loader inspection. |
| `CONS-005` | `DEFERRED` | Governance runtime enforcement requires runtime/governance inspection. |

## Not Validated

| Item | Reason |
| --- | --- |
| Registry acceptance | Requires separate closeout decision. |
| Validator runtime behavior | Validator execution was not authorized. |
| Registry example YAML parsing | Registry examples were not parsed by this package. |
| JSON Schema validation | No schema validation was authorized or performed. |
| Consumer runtime integration | Runtime consumer inspection was outside scope. |
| Extension loader behavior | Loader inspection was outside scope. |
| Governance runtime enforcement | Runtime enforcement inspection was outside scope. |
| Remote, branch, release, deploy, sync, or external state | Outside authorization. |

## Package D Evidence Result

```text
PHASE_4_PACKAGE_D_REGISTRY_SEMANTIC_EVALUATION_EVIDENCE_COLLECTED_NO_REGISTRY_EDITS
```

Package D evaluation evidence was collected with exact structured read of the
authority registry. No registry edits, validator execution, registry example
parsing, or remote actions were performed.
