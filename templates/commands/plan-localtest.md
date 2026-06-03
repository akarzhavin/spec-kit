---
description: Plan the LOCALTEST phase — plan running the feature locally and fixing what the local run surfaces.
handoffs:
  - label: Create Localtest Tasks
    agent: speckit.tasks
    prompt: Break the localtest plan into tasks
    send: true
scripts:
  sh: scripts/bash/setup-plan.sh --json --phase localtest
  ps: scripts/powershell/setup-plan.ps1 -Json -Phase localtest
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

This is the **localtest** phase of a multi-phase workflow. The base feature and
any prior review work are done. This command produces a **separate, phase-scoped
plan** at `plan-localtest.md` covering how to run the feature locally
(build/run steps, env/config, fixtures/seed data, smoke and manual test
scenarios) and the fixes required for issues the local run uncovers.

It does **NOT** regenerate the design artifacts (`research.md`, `data-model.md`,
`quickstart.md`, `contracts/`) — reference them, especially `quickstart.md`.

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC,
   IMPL_PLAN (resolves to `plan-localtest.md`), SPECS_DIR, BRANCH. The script
   records the active phase so `tasks` / `analyze` / `implement` target
   `plan-localtest.md` / `tasks-localtest.md`. For single quotes in args like
   "I'm Groot", use escape syntax: e.g 'I'\''m Groot'.

2. **Load context**: Read FEATURE_SPEC, base `plan.md`, `quickstart.md` (if
   present), `/memory/constitution.md`, and the current implementation. Treat any
   user-provided run results/errors in the input above as the primary scope.

3. **Author the localtest plan** at IMPL_PLAN (`plan-localtest.md`):
   - Exact steps to build and run the feature locally and the expected behavior.
   - Smoke/manual test scenarios mapped to the user stories.
   - A list of fixes for issues the local run reveals, with affected files.

## Completion Report

Report branch, the `plan-localtest.md` path, and the local-run scenarios and
fixes captured. Hand off to `speckit.tasks` to generate `tasks-localtest.md`.

## Key rules

- Use absolute paths for filesystem operations; project-relative paths in docs.
- Do not overwrite the base `plan.md` or any shared design artifacts.
- ERROR if the base `plan.md` does not exist (run the base planning flow first).

## Done When

- [ ] `plan-localtest.md` written with run steps, scenarios, and concrete fixes
- [ ] Shared design artifacts referenced, not regenerated
- [ ] Completion reported with branch and plan path
