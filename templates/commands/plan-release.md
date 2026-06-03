---
description: Plan the RELEASE phase — plan packaging, versioning, changelog, and CI/release readiness for the feature.
handoffs:
  - label: Create Release Tasks
    agent: speckit.tasks
    prompt: Break the release plan into tasks
    send: true
scripts:
  sh: scripts/bash/setup-plan.sh --json --phase release
  ps: scripts/powershell/setup-plan.ps1 -Json -Phase release
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

This is the **release** phase of a multi-phase workflow. The feature is
implemented, reviewed, and locally tested. This command produces a **separate,
phase-scoped plan** at `plan-release.md` covering release readiness: versioning,
changelog/release notes, packaging/build artifacts, dependency and license
checks, CI/CD pipeline updates, documentation, and rollout/rollback steps.

It does **NOT** regenerate the design artifacts (`research.md`, `data-model.md`,
`quickstart.md`, `contracts/`) — reference them.

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC,
   IMPL_PLAN (resolves to `plan-release.md`), SPECS_DIR, BRANCH. The script
   records the active phase so `tasks` / `analyze` / `implement` target
   `plan-release.md` / `tasks-release.md`. For single quotes in args like
   "I'm Groot", use escape syntax: e.g 'I'\''m Groot'.

2. **Load context**: Read FEATURE_SPEC, base `plan.md`, `/memory/constitution.md`,
   and project release/CI config (e.g. `pyproject.toml`, `CHANGELOG.md`,
   `.github/workflows/`). Treat any user-provided release constraints in the
   input above as the primary scope.

3. **Author the release plan** at IMPL_PLAN (`plan-release.md`):
   - Version bump strategy and target version.
   - Changelog/release-notes entries to add.
   - Packaging/build, dependency/license, and CI/CD steps.
   - Documentation updates, rollout and rollback plan.

## Completion Report

Report branch, the `plan-release.md` path, and the release items captured. Hand
off to `speckit.tasks` to generate `tasks-release.md`.

## Key rules

- Use absolute paths for filesystem operations; project-relative paths in docs.
- Do not overwrite the base `plan.md` or any shared design artifacts.
- ERROR if the base `plan.md` does not exist (run the base planning flow first).

## Done When

- [ ] `plan-release.md` written with version, changelog, packaging, and CI steps
- [ ] Shared design artifacts referenced, not regenerated
- [ ] Completion reported with branch and plan path
