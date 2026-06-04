---
description: Finalize the feature — verify the work is fully integrated (branches & submodules merged, worktree closeable), then generate resolution.md.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). Treat any
notes the user provides here (known caveats, follow-ups, intentional scope cuts)
as authoritative context for the report.

## Purpose

This is the **final step** of the workflow — run it after `__SPECKIT_COMMAND_IMPLEMENT__`
has completed (and, in a multi-phase workflow, after the last phase you intend to
ship). It does two things, in order:

1. **Verifies the work is fully integrated and the worktree can be closed** (the
   "Integration & worktree gate" below). This is a **hard gate**: if it fails,
   the command STOPS and does **not** write the report.
2. Only when the gate passes, produces the hand-off artifact `resolution.md`
   summarizing the work actually done: what was delivered, what was deferred, how
   it was verified, and the final state of the feature.

This project develops each feature in its own **`git worktree`** (e.g.
`../<project>-<feature>` on the feature branch). "Done" means that worktree is
ready to be **closed** (`git worktree remove`). The single most common reason a
worktree fails to close is **uncommitted changes** — in the worktree itself **or
in a submodule** — so the gate checks exactly that, plus that every task branch
(superproject and each submodule) has been merged into its base.

Except for writing `resolution.md` (and committing it / removing the worktree in
the closing step), this command does **not** modify code, plans, or tasks.

## Pre-Execution Checks

**Check for extension hooks (before resolution)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_done` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse FEATURE_DIR, IMPL_PLAN, TASKS, PHASE, and AVAILABLE_DOCS. All paths must be absolute. `IMPL_PLAN` and `TASKS` are the **active plan and tasks files** — when PHASE is not `base`/empty they are phase-suffixed (e.g. `plan-final.md` / `tasks-final.md`); otherwise they are `plan.md` / `tasks.md`. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Determine the resolution file path** (`RESOLUTION`):
   - If PHASE is `base` or empty: `FEATURE_DIR/resolution.md`
   - Otherwise: `FEATURE_DIR/resolution-<PHASE>.md` (mirrors `plan-<phase>.md` / `tasks-<phase>.md`)

3. **Load context** (read everything that exists; never fail if an optional doc is missing):
   - **REQUIRED**: The feature spec (`spec.md` in FEATURE_DIR) — the original requirements and user stories.
   - **REQUIRED**: The active plan at IMPL_PLAN — the intended tech stack, architecture, and work items.
   - **REQUIRED**: The active tasks file at TASKS — the task breakdown and each task's checked/unchecked state (`[X]` vs `[ ]`).
   - **IN A PHASE** (PHASE not `base`/empty): also read the base `plan.md` and any earlier-phase `resolution-*.md` for overall context.
   - **IF EXISTS**: `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, and any `checklists/`.
   - **IF EXISTS**: `/memory/constitution.md` for governance constraints to confirm adherence.

4. **Integration & worktree gate** — ⛔ **HARD GATE. Run this BEFORE writing anything.** If any check below fails, **STOP**: print a blocking report (see "If the gate fails") and do **NOT** create `resolution.md`. Skip this entire step only if the project is not a git repo (`git rev-parse --git-dir` fails).

   Resolve the relevant git locations first:
   - **Superproject root**: `git rev-parse --show-toplevel`.
   - **Feature branch**: the current branch (`git rev-parse --abbrev-ref HEAD`), typically a `NNN-<feature>` branch owned by this feature's worktree.
   - **Base branch**: the integration target the feature merges into. Use, in order of preference: an explicit base in the user input above → a base recorded in `plan.md`/constitution → otherwise the repo's default branch (`git symbolic-ref --quiet refs/remotes/origin/HEAD` stripped to its name, else `main`, else `master`). State which base you used.
   - **Submodules**: `git submodule status --recursive` (empty output ⇒ no submodules; skip submodule-specific checks).

   **Check A — Clean working tree (the #1 reason a worktree won't close).** Run `git status --porcelain` in the superproject; it MUST be empty (no staged, unstaged, or untracked changes). Untracked files count — they block `git worktree remove` too. **Note:** `resolution.md` does not exist yet at this point, so it cannot be the cause; any dirt here is leftover implementation work that must be committed or discarded first.

   **Check B — Submodules clean & pointers committed.** For every submodule: `git submodule foreach --recursive 'git status --porcelain'` MUST be empty in each. Additionally, the superproject MUST NOT show modified submodule gitlinks (a submodule advanced to a new commit but the superproject's pointer not committed shows as dirty in Check A) — this is a frequent silent blocker.

   **Check C — All task branches merged.** The feature branch MUST be fully merged into BASE in the superproject: verify BASE contains the feature tip (e.g. `git branch --merged <base>` lists the feature branch, or `git merge-base --is-ancestor <feature> <base>` succeeds), AND there are no feature commits absent from BASE (`git log --oneline <base>..<feature>` is empty). For EACH submodule, perform the same check against that submodule's own base branch — a submodule with un-merged commits means the task is not actually integrated.

   **Check D — Worktree is closeable.** List worktrees with `git worktree list --porcelain`. The feature worktree must be in a removable state: clean (Checks A/B) and not locked. If you are currently executing **inside** the feature worktree, note it — `git worktree remove` cannot remove the worktree you are standing in; closing it happens from the superproject's primary checkout in step 8.

   **If the gate fails**, STOP and report, per failing check:
   - Exactly what is blocking (file list from `git status --porcelain`, the dirty submodule, the un-merged branch + its missing commits, or the locked/dirty worktree).
   - Concrete remediation, e.g. *"commit or stash the N uncommitted files in submodule `libs/foo`, then merge `libs/foo`'s `NNN-…` branch into its base"*, or *"the feature branch has 2 commits not in `main` — merge them before finalizing"*.
   - Do **not** write `resolution.md` and do **not** remove any worktree. The user fixes the blockers and re-runs `/done`.

5. **Gather the real state of the work** (this is the heart of the report — describe what *actually happened*, not what the plan intended):
   - From TASKS: count total / completed (`[X]`) / incomplete (`[ ]`) tasks; list any incomplete ones explicitly.
   - From the repository: feature branch, base branch, merge status (from step 4), and a short commit summary (`git log --oneline`). Summarize changed files by area (`git diff --stat <base>...<feature>`); do not paste full diffs.
   - Submodule integration status (which submodules were touched, and that each is merged & clean).
   - From `checklists/` (if present): the pass/fail status of each checklist.
   - From verification evidence available in context (test runs, build output, the user input above): how the work was validated and the results.

6. **Author the report** at RESOLUTION. If `.specify/templates/resolution-template.md` exists, use it as the structure; otherwise produce the following sections:

   ```markdown
   # Resolution: [FEATURE NAME]

   **Feature**: [branch / feature dir]
   **Phase**: [base | review | localtest | release | final]
   **Status**: [✅ Done | ⚠️ Done with caveats | ⛔ Incomplete]
   **Date**: [today]

   ## Summary

   2–4 sentences: what the task was and what was delivered, in plain language.

   ## What was done

   - Bullet per delivered capability, mapped to the user story / requirement it satisfies.
   - Reference key files or modules (project-relative paths).

   ## Requirements coverage

   | Requirement / User story | Status | Notes |
   |--------------------------|--------|-------|
   | US1 …                    | ✅ Done | … |
   | FR-003 …                 | ⚠️ Partial | … |

   ## Task completion

   - Total: N · Completed: N · Incomplete: N
   - List any incomplete tasks and why they were deferred.

   ## Changes

   - Branch, commit summary, and changed-file summary (by area). No full diffs.

   ## Integration & worktree

   - **Feature branch**: [name] → merged into **[base]**: ✅
   - **Submodules**: [each touched submodule → merged & clean: ✅], or "none"
   - **Working tree**: clean ✅
   - **Worktree**: [path] — closed (`git worktree remove`) ✅ / pending close

   ## Verification

   - How it was tested/validated (tests, build, manual checks) and the results.
   - Checklist results, if any.

   ## Deviations from the plan

   - Anything implemented differently from IMPL_PLAN, and why.

   ## Known limitations & follow-ups

   - Open issues, deferred work, tech debt, and suggested next steps / phases.
   ```

   Rules for the report:
   - Be honest and evidence-based. If tasks are incomplete or tests failed, say so and set Status accordingly — do **not** report success that the evidence does not support.
   - Use project-relative paths in the document; use absolute paths for filesystem operations.
   - Keep it a report: summarize, do not dump raw command output or full diffs.

7. **Mark the workflow complete**: The gate in step 4 already passed, so integration is sound. If all tasks are `[X]`, all checklists pass, and verification succeeded, set Status to ✅ Done. If shipped with caveats, ⚠️. If required work is incomplete, ⛔ and clearly list what remains.

8. **Close the worktree** (the final act of finishing the task):
   - Commit `resolution.md` (and any other spec artifacts created here) so the working tree is clean again — generating the report just re-dirtied it. If your process requires the report on the integration branch, merge that commit into BASE as well.
   - Confirm `git status --porcelain` is empty (superproject + submodules) — re-run Checks A/B from step 4.
   - Remove the feature worktree so it is **closed**: from the superproject's primary checkout run `git worktree remove <feature-worktree-path>` (use `git worktree list` to find it). If you are currently inside that worktree, git will refuse to remove it — switch to the primary checkout first, or instruct the user to run the removal there. Then `git worktree prune`.
   - Verify the worktree is gone (`git worktree list` no longer shows it). If removal could not be completed automatically (e.g. you cannot leave the current worktree), record it as **pending close** in the report and give the exact command for the user to run.

## Mandatory Post-Execution Hooks

**You MUST complete this section before reporting completion to the user.**

Check if `.specify/extensions.yml` exists in the project root.
- If it does not exist, or no hooks are registered under `hooks.after_done`, skip to the Completion Report.
- If it exists, read it and look for entries under the `hooks.after_done` key.
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue to the Completion Report.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Mandatory hook** (`optional: false`) — **You MUST emit `EXECUTE_COMMAND:` for each mandatory hook**:
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

## Completion Report

Report the RESOLUTION file path, the final Status, and a one-line summary. If
Status is ⛔ Incomplete or ⚠️ Done with caveats, list what remains or the caveats.

## Done When

- [ ] Integration & worktree gate passed: working tree clean (superproject + submodules), all task branches (incl. submodules) merged into base, worktree closeable — OR the command STOPPED with a blocking report and no `resolution.md` was written
- [ ] `resolution.md` (or `resolution-<phase>.md`) written to FEATURE_DIR (only after the gate passed)
- [ ] Report reflects the **actual** state of the work (task completion, integration & worktree status, changes, verification) — not just the plan's intent
- [ ] Status set honestly (✅ / ⚠️ / ⛔) based on evidence
- [ ] `resolution.md` committed and the feature worktree closed (`git worktree remove`) — or recorded as pending close with the exact command for the user
- [ ] Extension hooks dispatched or skipped according to the rules above
- [ ] Resolution file path and Status reported to the user
