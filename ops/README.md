# ops

Purpose:
- validation, reports, receipts, dry-runs, and maintenance.

Allowed:
- validation scripts
- reports
- receipts
- dry-run outputs
- maintenance scripts

Denied:
- secrets
- private state
- source code that belongs to a specific repo

Agent policy:
- read allowed by default
- write only for explicit report, receipt, dry-run, or maintenance tasks
