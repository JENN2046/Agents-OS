# 06｜Event Contract

## 1. Worker NEED_REVIEWER

```json
{
  "type": "NEED_REVIEWER",
  "problem_type": "architecture",
  "question": "What should the Worker do next?",
  "evidence": ["Evidence item"],
  "proposed_options": ["Option A", "Option B"],
  "recommended_next_action": "Ask Reviewer for decision."
}
```

Allowed `problem_type`:

```text
architecture
policy
test_failure
diff_review
unclear_intent
```

## 2. Reviewer REVIEWER_DECISION

```json
{
  "type": "REVIEWER_DECISION",
  "decision": "continue",
  "reason": "The Worker can safely continue in read-only mode.",
  "next_instruction": "Continue the synthetic smoke test and produce DONE.",
  "constraints": ["read-only", "synthetic workspace only"],
  "evidence_used": ["Worker question", "Synthetic workspace contents"]
}
```

Allowed `decision`:

```text
continue
revise
block
request_human_gate
```

## 3. Worker DONE

```json
{
  "type": "DONE",
  "summary": "The synthetic Worker → Reviewer → Worker loop completed.",
  "evidence": ["NEED_REVIEWER emitted", "REVIEWER_DECISION received"]
}
```

## 4. Worker BLOCKED

```json
{
  "type": "BLOCKED",
  "reason": "Cannot continue without forbidden capability.",
  "needs": ["..."]
}
```

## 5. State Transition Event

```json
{
  "ts": "2026-07-07T00:00:00.000Z",
  "job_id": "job_xxx",
  "type": "STATE_TRANSITION",
  "from": "WORKER_RUNNING",
  "to": "NEED_REVIEWER",
  "reason": "Worker emitted valid NEED_REVIEWER",
  "evidence_refs": []
}
```

## 6. Policy Decision Event

```json
{
  "ts": "2026-07-07T00:00:00.000Z",
  "job_id": "job_xxx",
  "type": "POLICY_DECISION",
  "request_type": "item/fileChange/requestApproval",
  "decision": "decline",
  "reason": "MVP is read-only",
  "path": null
}
```

## 7. Receipt Format

Receipt must include:

```text
# Receipt

result: PASS | BLOCK | FAIL
job_id:
started_at:
finished_at:
final_state:

## Boundary Summary
## State Timeline
## Worker Output
## Reviewer Decision
## Policy Decisions
## Artifacts
## Next Step
```

## 8. Parsing Rule

Smoke test must use `outputSchema`.

Malformed JSON is not valid. Do not attempt to “repair” structured output in smoke. Real-job tolerance can be added only after MVP passes.
