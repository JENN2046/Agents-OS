# AGENTS OS Stale Local PR Workspace Cleanup Plan

Date: 2026-07-09
Status: planned
Scope: local-only cleanup command gate for merged PR worktrees and branches

## Evidence

All listed local PR branches are already merged into `main`:

- `pr/colameta-pr12-retrospective`
- `pr/pr-risk-review-helper`
- `pr/docctl-readonly-index-cache`
- `pr/codex-appserver-active-loop-import`
- `pr/workbench-next-step-fast-validation`

All listed local PR worktrees are still present:

- `/tmp/agents-os-pr-worktrees/01-docctl`
- `/tmp/agents-os-pr-worktrees/02-active-loop`
- `/tmp/agents-os-pr-worktrees/03-workbench`
- `/tmp/agents-os-pr-worktrees/04-colameta-retrospective`
- `/tmp/agents-os-pr-worktrees/05-pr-risk-review`

## Exact Local Command Plan

```bash
git worktree remove /tmp/agents-os-pr-worktrees/01-docctl
git worktree remove /tmp/agents-os-pr-worktrees/02-active-loop
git worktree remove /tmp/agents-os-pr-worktrees/03-workbench
git worktree remove /tmp/agents-os-pr-worktrees/04-colameta-retrospective
git worktree remove /tmp/agents-os-pr-worktrees/05-pr-risk-review
git branch -d pr/docctl-readonly-index-cache
git branch -d pr/codex-appserver-active-loop-import
git branch -d pr/workbench-next-step-fast-validation
git branch -d pr/colameta-pr12-retrospective
git branch -d pr/pr-risk-review-helper
```

## Boundary

This plan is local-only. It does not authorize command execution yet, remote
branch deletion, push, release, deploy, tag, force push, history rewrite,
provider calls, service starts, Memory writes, state-private reads, or secret
output.
