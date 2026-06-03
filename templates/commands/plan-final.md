---
description: Plan the FINAL TEST phase — plan final acceptance/end-to-end testing and sign-off for the feature.
handoffs:
  - label: Create Final Test Tasks
    agent: speckit.tasks
    prompt: Break the final test plan into tasks
    send: true
scripts:
  sh: scripts/bash/setup-plan.sh --json --phase final
  ps: scripts/powershell/setup-plan.ps1 -Json -Phase final
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

This is the **final test** phase of a multi-phase workflow — the last gate before
the feature is considered done. This command produces a **separate, phase-scoped
plan** at `plan-final.md` covering final acceptance and end-to-end testing:
verification of every user story's acceptance criteria, regression and
integration coverage, non-functional checks (performance/security/accessibility
as applicable), and a sign-off checklist.

It does **NOT** regenerate the design artifacts (`research.md`, `data-model.md`,
`quickstart.md`, `contracts/`) — reference them.

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC,
   IMPL_PLAN (resolves to `plan-final.md`), SPECS_DIR, BRANCH. The script records
   the active phase so `tasks` / `analyze` / `implement` target `plan-final.md` /
   `tasks-final.md`. For single quotes in args like "I'm Groot", use escape
   syntax: e.g 'I'\''m Groot'.

2. **Load context**: Read FEATURE_SPEC (acceptance criteria per user story), base
   `plan.md`, `/memory/constitution.md`, and the results of prior phases
   (review, localtest, release). Treat any user-provided acceptance constraints in
   the input above as the primary scope.

3. **Author the final test plan** at IMPL_PLAN (`plan-final.md`):
   - Acceptance test per user story, mapped to spec criteria, with pass/fail
     conditions.
   - Regression/integration/e2e coverage and any non-functional checks.
   - A sign-off checklist gating "done".

## Completion Report

Report branch, the `plan-final.md` path, and the acceptance/sign-off items
captured. Hand off to `speckit.tasks` to generate `tasks-final.md`.

## Key rules

- Use absolute paths for filesystem operations; project-relative paths in docs.
- Do not overwrite the base `plan.md` or any shared design artifacts.
- ERROR if the base `plan.md` does not exist (run the base planning flow first).

## Done When

- [ ] `plan-final.md` written with acceptance tests and a sign-off checklist
- [ ] Shared design artifacts referenced, not regenerated
- [ ] Completion reported with branch and plan path
