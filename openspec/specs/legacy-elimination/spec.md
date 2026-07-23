# Legacy Elimination Specification

## Purpose

Define the removal of the legacy codebases (`backend/`, `ui/`, `ui_flet/`,
root `main.py`, `verification_test.py`) and migration of their persisted
state into the canonical `audio2text/` package. The elimination SHALL be
delivered as chained PRs each ≤400 changed lines, each independently
revertible, with the test suite green after every slice.

## Requirements

### Requirement: Deletion Scope

The system MUST remove from the repository root: `backend/`, `ui/`,
`ui_flet/`, root `main.py`, and `verification_test.py`. No file in
`audio2text/` MAY contain `from backend`, `from ui`, or `from ui_flet`
after elimination.

#### Scenario: All legacy directories gone

- GIVEN the chained PR series has merged
- WHEN `git ls-files backend ui ui_flet main.py verification_test.py` runs
- THEN zero files are listed
- AND `rg "from (backend|ui|ui_flet)\." audio2text/` returns no matches

#### Scenario: Legacy preserved in git history

- GIVEN the deletion PRs have merged
- WHEN `git log --oneline -- backend/config_manager.py` runs
- THEN the historical commits are still reachable

### Requirement: Config Migration XOR to SecretManager

The system SHALL provide a one-shot migration
(`audio2text/config/migration.py`) that decodes legacy XOR-obfuscated keys
and stores them through core-cenf `SecretManager`. The migrated config MUST
contain no secret values.

#### Scenario: Migration round-trips a real key

- GIVEN a legacy `config.json` with `groq_api_key` as a XOR+Base64 value
- WHEN `ConfigMigrator(secret_manager).run(old, new)` is invoked
- THEN `SecretManager.get("groq_api_key")` returns a plaintext `gsk_` key
- AND the new config.json holds no key value
- AND a `.v015.bak` backup of the old file exists

#### Scenario: Idempotent re-run

- GIVEN migration has already succeeded on a config file
- WHEN `detect_old_config` is called on the migrated file
- THEN it returns `False` (no `groq_api_key` at root)
- AND no second backup is created

### Requirement: CI/CD Path Update

`.github/workflows/ci.yml` MUST target `audio2text/` and `tests/` paths.
The legacy `backend/`, `ui/`, `ui_flet/` path triggers MUST be removed.

#### Scenario: CI runs on audio2text changes only

- GIVEN the updated workflow file
- WHEN a PR modifies `audio2text/providers/groq_provider.py`
- THEN the CI matrix runs against the `audio2text/` and `tests/` paths
- AND no CI step references the deleted directories

### Requirement: pyproject.toml and setup.py Cleanup

`pyproject.toml` and `setup.py` MUST declare `audio2text` as the sole
package. Legacy entry points, console scripts, and package discovery
referencing `backend.` or `ui.` MUST be removed.

#### Scenario: Package discovery is canonical

- GIVEN the updated `pyproject.toml`
- WHEN `[tool.setuptools.packages.find]` is inspected
- THEN `include = ["audio2text*"]` is the only entry

### Requirement: Build Script Cleanup

Scripts under `scripts/` MUST target the `audio2text/` package and the
`audio2text.main:main` entry point. Legacy PyInstaller spec references to
`backend/`, `ui/` MUST be removed.

#### Scenario: Build launches canonical entry point

- GIVEN the cleaned build script
- WHEN `python scripts/build.py --variant GENERAL` runs
- THEN the executable launches via `audio2text.main:main`
- AND no `ModuleNotFoundError: backend` appears in the log

### Requirement: Chained PR Size Budget

Each deletion PR SHALL have ≤400 changed lines (additions + deletions).
Slices that would exceed the budget MUST split along directory boundaries
(`backend/`, then `ui/`, then `ui_flet/`).

#### Scenario: Each slice within budget

- GIVEN the chained PR plan exists
- WHEN `gh pr view <n> --json additions,deletions` runs for each PR
- THEN `additions + deletions ≤ 400` for every PR
- AND each PR has a clear start, finish, and standalone verification step

#### Scenario: Independently revertible slices

- GIVEN a merged slice (e.g., `backend/` deletion) is reverted
- WHEN `git revert <merge-sha>` runs on `main`
- THEN the rest of the series still compiles and tests pass

### Requirement: Green Test Suite Per Slice

Every slice PR SHALL leave the full test suite green. The pipeline SHALL
block merge if `pytest tests/` fails. Coverage MUST be ≥50% after the final
slice.

#### Scenario: Slice blocks on failing test

- GIVEN a slice PR drops a test fixture referenced by an unrelated test
- WHEN CI runs `pytest tests/`
- THEN the pipeline blocks merge
- AND the failing test names are surfaced in the CI log
