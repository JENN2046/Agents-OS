# AGENTS OS Workbench Validation Maturity

Date: 2026-07-08

## Decision

Workbench validation is split into three operating levels:

- `fast`: ordinary progress. Run lightweight checks, selector checks, affected local fixtures, queue sanity, and import boundary checks.
- `targeted`: boundary-adjacent work. Run `fast` plus relevant registry validators or focused probes for the touched boundary.
- `full`: external-write, release, publish, or final audit boundary. Run the full fixture suite, full docctl-backed validation surface, and completion audit.

## Rule

Normal machine movement should not repeat full `docctl` or full registry validation on every step. Full validation remains mandatory before external writes, publication, release, deploy, history mutation, or any gate that crosses Jenn/provider/Memory/external-write boundaries.

## Implementation Notes

- `test-workbench.py` now defaults to fast fixture validation.
- `test-workbench.py --full` runs full validation and completion audit.
- `build_completion_audit()` can reuse a supplied full validation result so one full test does not run the full suite twice.
- Validation results now expose level, required level, actual level, duration, input hash, command evidence, and eligibility flags.

## Safety Boundary

This improves speed only for ordinary progress. It does not relax P3 boundaries, Jenn gate, provider gate, Memory gate, or external-write gate.
