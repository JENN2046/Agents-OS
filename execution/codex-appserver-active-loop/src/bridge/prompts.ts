export const workerNeedReviewerPrompt =
  [
    "Protocol smoke only.",
    "Do not inspect files, call tools, run commands, use network, or request approvals.",
    "Return NEED_REVIEWER using the provided output schema.",
    "Use problem_type policy.",
    "Ask the reviewer to confirm the read-only synthetic-workspace boundary and continue.",
    "Evidence must mention read-only sandbox, synthetic workspace root, and no forbidden App Server method requested.",
    "Recommended next action must be continue.",
  ].join(" ");

export const reviewerDecisionPrompt =
  [
    "Protocol smoke only.",
    "Do not inspect files, call tools, run commands, use network, or request approvals.",
    "Return REVIEWER_DECISION using the provided output schema.",
    "Use decision continue.",
    "Confirm the Worker stayed inside the read-only synthetic-workspace boundary.",
    "Keep the response concise.",
  ].join(" ");

export const workerDonePrompt =
  [
    "Protocol smoke only.",
    "Do not inspect files, call tools, run commands, use network, or request approvals.",
    "Use the reviewer decision to finish and return DONE using the provided output schema.",
    "Summarize that the real App Server Worker/Reviewer resume loop completed.",
  ].join(" ");
