"""Tests for the multi-phase workflow (plan-<phase> / tasks-<phase>).

Covers the phase-aware path resolution added to common.sh / setup-plan.sh /
setup-tasks.sh / check-prerequisites.sh (and their PowerShell mirrors):

- ``setup-plan --phase <name>`` writes ``plan-<phase>.md`` and records the
  active phase in ``<feature>/.current-phase``.
- The base phase keeps the historical ``plan.md`` / ``tasks.md`` names and
  clears the marker.
- ``setup-tasks`` and ``check-prerequisites`` pick up the active phase from the
  marker (no extra flags) and resolve / report the phase-suffixed files.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import requires_bash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASH_DIR = PROJECT_ROOT / "scripts" / "bash"
PS_DIR = PROJECT_ROOT / "scripts" / "powershell"
PLAN_TEMPLATE = PROJECT_ROOT / "templates" / "plan-template.md"
TASKS_TEMPLATE = PROJECT_ROOT / "templates" / "tasks-template.md"

_SCRIPTS = ("common", "setup-plan", "setup-tasks", "check-prerequisites")

HAS_PWSH = shutil.which("pwsh") is not None
_POWERSHELL = shutil.which("powershell.exe") or shutil.which("powershell")
PS_EXE = "pwsh" if HAS_PWSH else _POWERSHELL
requires_pwsh = pytest.mark.skipif(
    not (HAS_PWSH or _POWERSHELL), reason="no PowerShell available"
)

FEATURE = "001-my-feature"


def _install_scripts(repo: Path) -> None:
    bd = repo / ".specify" / "scripts" / "bash"
    pd = repo / ".specify" / "scripts" / "powershell"
    bd.mkdir(parents=True, exist_ok=True)
    pd.mkdir(parents=True, exist_ok=True)
    for name in _SCRIPTS:
        shutil.copy(BASH_DIR / f"{name}.sh", bd / f"{name}.sh")
        shutil.copy(PS_DIR / f"{name}.ps1", pd / f"{name}.ps1")


def _install_templates(repo: Path) -> None:
    tdir = repo / ".specify" / "templates"
    tdir.mkdir(parents=True, exist_ok=True)
    shutil.copy(PLAN_TEMPLATE, tdir / "plan-template.md")
    shutil.copy(TASKS_TEMPLATE, tdir / "tasks-template.md")


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("SPECIFY_"):
            env.pop(key)
    return env


def _git_init(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init", "-q"], cwd=repo, check=True
    )


@pytest.fixture
def phase_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir()
    _git_init(repo)
    subprocess.run(["git", "checkout", "-q", "-b", FEATURE], cwd=repo, check=True)
    (repo / ".specify").mkdir()
    _install_templates(repo)
    _install_scripts(repo)
    # A spec is required by setup-tasks.
    feat = repo / "specs" / FEATURE
    feat.mkdir(parents=True)
    (feat / "spec.md").write_text("# Spec\n", encoding="utf-8")
    return repo


def _run_sh(repo: Path, script: str, *args: str) -> subprocess.CompletedProcess:
    path = repo / ".specify" / "scripts" / "bash" / f"{script}.sh"
    return subprocess.run(
        ["bash", str(path), *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )


def _run_ps(repo: Path, script: str, *args: str) -> subprocess.CompletedProcess:
    path = repo / ".specify" / "scripts" / "powershell" / f"{script}.ps1"
    return subprocess.run(
        [PS_EXE, "-NoProfile", "-File", str(path), *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )


def _marker(repo: Path) -> Path:
    return repo / "specs" / FEATURE / ".current-phase"


def _feat(repo: Path) -> Path:
    return repo / "specs" / FEATURE


# ── Bash: setup-plan phase handling ─────────────────────────────────────────


@requires_bash
def test_phase_plan_creates_suffixed_plan_and_marker(phase_repo: Path) -> None:
    """``--phase review`` writes plan-review.md and records the phase."""
    result = _run_sh(phase_repo, "setup-plan", "--json", "--phase", "review")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert Path(data["IMPL_PLAN"]).name == "plan-review.md"
    assert Path(data["IMPL_PLAN"]).is_file()
    assert _marker(phase_repo).read_text(encoding="utf-8").strip() == "review"
    # The base plan must NOT have been created by a phase run.
    assert not (_feat(phase_repo) / "plan.md").exists()


@requires_bash
def test_base_plan_has_no_suffix_and_clears_marker(phase_repo: Path) -> None:
    """The base ``--phase base`` run uses plan.md and clears a prior marker."""
    # Establish a phase marker first.
    _run_sh(phase_repo, "setup-plan", "--json", "--phase", "review")
    assert _marker(phase_repo).exists()

    result = _run_sh(phase_repo, "setup-plan", "--json", "--phase", "base")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert Path(data["IMPL_PLAN"]).name == "plan.md"
    assert not _marker(phase_repo).exists()


@requires_bash
def test_plan_without_phase_flag_defaults_to_base(phase_repo: Path) -> None:
    """Omitting --phase behaves like the base phase (backward compatible)."""
    result = _run_sh(phase_repo, "setup-plan", "--json")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert Path(data["IMPL_PLAN"]).name == "plan.md"
    assert not _marker(phase_repo).exists()


@requires_bash
def test_phase_requires_value(phase_repo: Path) -> None:
    """A trailing --phase with no value is an error."""
    result = _run_sh(phase_repo, "setup-plan", "--json", "--phase")
    assert result.returncode != 0
    assert "--phase requires a value" in result.stderr


# ── Bash: ambient phase flows into the other scripts ────────────────────────


@requires_bash
def test_ambient_phase_flows_to_setup_tasks(phase_repo: Path) -> None:
    """setup-tasks (no flags) targets the active phase's plan/tasks files."""
    _run_sh(phase_repo, "setup-plan", "--json", "--phase", "release")
    result = _run_sh(phase_repo, "setup-tasks", "--json")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["PHASE"] == "release"
    assert Path(data["IMPL_PLAN"]).name == "plan-release.md"
    assert Path(data["TASKS"]).name == "tasks-release.md"


@requires_bash
def test_ambient_phase_flows_to_check_prerequisites(phase_repo: Path) -> None:
    """check-prerequisites reports phase-suffixed plan/tasks and lists them."""
    _run_sh(phase_repo, "setup-plan", "--json", "--phase", "review")
    # Simulate /speckit.tasks having produced the phase tasks file.
    (_feat(phase_repo) / "tasks-review.md").write_text("# tasks\n", encoding="utf-8")

    result = _run_sh(
        phase_repo,
        "check-prerequisites",
        "--json",
        "--require-tasks",
        "--include-tasks",
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["PHASE"] == "review"
    assert Path(data["IMPL_PLAN"]).name == "plan-review.md"
    assert Path(data["TASKS"]).name == "tasks-review.md"
    assert "tasks-review.md" in data["AVAILABLE_DOCS"]


@requires_bash
def test_check_prerequisites_errors_on_missing_phase_tasks(phase_repo: Path) -> None:
    """When the phase tasks file is missing, the error names the phase file."""
    _run_sh(phase_repo, "setup-plan", "--json", "--phase", "final")
    result = _run_sh(
        phase_repo, "check-prerequisites", "--json", "--require-tasks"
    )
    assert result.returncode != 0
    assert "tasks-final.md not found" in result.stderr


@requires_bash
def test_base_flow_unaffected_by_phase_changes(phase_repo: Path) -> None:
    """With no active phase, the base scripts still resolve plan.md / tasks.md."""
    _run_sh(phase_repo, "setup-plan", "--json")  # base
    result = _run_sh(phase_repo, "setup-tasks", "--json")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["PHASE"] in ("", "base")
    assert Path(data["IMPL_PLAN"]).name == "plan.md"
    assert Path(data["TASKS"]).name == "tasks.md"


@requires_bash
def test_phases_do_not_overwrite_each_other(phase_repo: Path) -> None:
    """Each phase keeps its own plan file; phases never clobber one another."""
    for phase in ("review", "localtest", "release", "final"):
        result = _run_sh(phase_repo, "setup-plan", "--json", "--phase", phase)
        assert result.returncode == 0, result.stderr
    feat = _feat(phase_repo)
    for phase in ("review", "localtest", "release", "final"):
        assert (feat / f"plan-{phase}.md").is_file()


# ── PowerShell mirror ───────────────────────────────────────────────────────


@requires_pwsh
def test_ps_phase_plan_creates_suffixed_plan_and_marker(phase_repo: Path) -> None:
    result = _run_ps(phase_repo, "setup-plan", "-Json", "-Phase", "review")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert Path(data["IMPL_PLAN"]).name == "plan-review.md"
    assert Path(data["IMPL_PLAN"]).is_file()
    assert _marker(phase_repo).read_text(encoding="utf-8").strip() == "review"


@requires_pwsh
def test_ps_base_plan_clears_marker(phase_repo: Path) -> None:
    _run_ps(phase_repo, "setup-plan", "-Json", "-Phase", "review")
    assert _marker(phase_repo).exists()
    result = _run_ps(phase_repo, "setup-plan", "-Json", "-Phase", "base")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert Path(data["IMPL_PLAN"]).name == "plan.md"
    assert not _marker(phase_repo).exists()


@requires_pwsh
def test_ps_ambient_phase_flows_to_check_prerequisites(phase_repo: Path) -> None:
    _run_ps(phase_repo, "setup-plan", "-Json", "-Phase", "review")
    (_feat(phase_repo) / "tasks-review.md").write_text("# tasks\n", encoding="utf-8")
    result = _run_ps(
        phase_repo,
        "check-prerequisites",
        "-Json",
        "-RequireTasks",
        "-IncludeTasks",
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["PHASE"] == "review"
    assert Path(data["IMPL_PLAN"]).name == "plan-review.md"
    assert Path(data["TASKS"]).name == "tasks-review.md"
    assert "tasks-review.md" in data["AVAILABLE_DOCS"]
