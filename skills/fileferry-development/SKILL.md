---
name: fileferry-development
description: Use when implementing or updating FileFerry features. Enforces project standards for branch-first development, V1.2/V1.3 protocol compatibility, Chinese GUI conventions, packaging alignment, and required validation/document updates.
---

# FileFerry Development Standards

Use this skill for any feature work, bugfix, refactor, or packaging update in the FileFerry repository.

## Mandatory Workflow

1. Start from `main` and create a new feature branch before coding.
2. Read impacted docs first:
   - `docs/requirements_v1.2.md`
   - `docs/requirements_v1.3.md` (if GUI or packaging is touched)
   - `docs/architecture_design.md`
3. Implement minimal coherent changes across affected layers (protocol/core/CLI/GUI/packaging).
4. Run validation commands (below).
5. Update docs and version fields when behavior or deliverables change.
6. Commit on the feature branch and hand off for user merge to `main`.

## Project Constraints

- Keep protocol/path safety checks intact (`sanitize_relative_path`, output-dir escape prevention).
- Keep V1.2 compatibility:
  - `--src` multi-source mode
  - legacy `--file` mode
  - conflict policy: `overwrite|skip|rename` (default `overwrite`)
  - continue-on-error supported
- Keep V1.3 GUI conventions:
  - Chinese UI text
  - manual connect/disconnect controls for sender and receiver
  - receiver can start/stop listening explicitly
- Preserve CLI + GUI coexistence in packaging outputs.
- Do not break `send_file` / `receive_once` compatibility wrappers unless explicitly requested.

## Required Validation Commands

Run all that apply after changes:

```bash
python3 -m compileall fileferry fileferry_gui tests scripts
python3 -m unittest discover -s tests -v
bash -n packaging/linux/build_deb.sh packaging/linux/build_rpm.sh packaging/macos/build_pkg.sh
python3 -m fileferry send --help
python3 -m fileferry recv --help
```

If GUI code changed, also run:

```bash
python3 -m fileferry_gui.app
```

If it fails due missing `PySide6`, record that clearly and keep the dependency/install guidance updated.

## Files Usually Requiring Sync Updates

- `README.md`
- `docs/user_manual.md`
- `docs/test_report.md`
- `docs/architecture_design.md`
- `docs/packaging_test_report.md` (if packaging touched)
- `pyproject.toml` + `fileferry/__init__.py` (version bumps when releasing a new iteration)

## Completion Checklist

- New branch was used.
- Behavior matches current requirements docs.
- Tests passed (or failures documented with root cause).
- Docs and packaging instructions are updated.
- Final handoff includes branch name, commit hash, and validation summary.
