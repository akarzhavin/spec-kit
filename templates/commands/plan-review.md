---
description: Plan the REVIEW phase — turn review/refactor findings on the implemented feature into a focused, phase-scoped plan.
handoffs:
  - label: Create Review Tasks
    agent: speckit.tasks
    prompt: Break the review plan into tasks
    send: true
scripts:
  sh: scripts/bash/setup-plan.sh --json --phase review
  ps: scripts/powershell/setup-plan.ps1 -Json -Phase review
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

This is the **review** phase of a multi-phase workflow. The base feature has
already been implemented (`plan.md` / `tasks.md`). This command produces a
**separate, phase-scoped plan** at `plan-review.md` that captures the work needed
to review and harden the implementation: code-review findings, refactors,
edge cases, error handling, test gaps, and adherence to the constitution.

It does **NOT** regenerate the design artifacts (`research.md`, `data-model.md`,
`quickstart.md`, `contracts/`) — those are shared across phases. Reference them.

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC,
   IMPL_PLAN (this resolves to `plan-review.md`), SPECS_DIR, BRANCH. The script
   also records the active phase so the subsequent `tasks` / `analyze` /
   `implement` commands automatically target `plan-review.md` / `tasks-review.md`.
   For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot'.

2. **Load context**: Read FEATURE_SPEC, the base `plan.md`, the base `tasks.md`,
   `/memory/constitution.md`, and any existing implementation in the repo. If the
   user provided review findings in the input above, treat them as the primary
   scope.

3. **Author the review plan** at IMPL_PLAN (`plan-review.md`):
   - Summarize what is being reviewed and the review criteria (correctness,
     simplicity, performance, security, test coverage, constitution compliance).
   - List concrete review/refactor items with rationale and affected files.
   - Note risks and ordering. Keep it focused on review work, not new features.

## Completion Report

Report branch, the `plan-review.md` path, and the review items captured. Hand off
to `speckit.tasks` to generate `tasks-review.md`.

## Key rules

- Use absolute paths for filesystem operations; project-relative paths in docs.
- Do not overwrite the base `plan.md` or any shared design artifacts.
- ERROR if the base `plan.md` does not exist (run the base planning flow first).

## Done When

- [ ] `plan-review.md` written with concrete, scoped review/refactor items
- [ ] Shared design artifacts referenced, not regenerated
- [ ] Completion reported with branch and plan path
