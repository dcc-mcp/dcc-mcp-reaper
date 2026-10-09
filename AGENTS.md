# AGENTS.md — dcc-mcp-reaper

> Navigation map for AI agents, not a reference manual. Detailed API lives in
> `README.md`; install and lifecycle in `install.md`; the transport decision in
> `docs/adr/0001-transport.md`. **This file is the only agent contract file at
> the repository root** — `CLAUDE.md` / `GEMINI.md` / `COPILOT.md` and friends
> are deliberately absent; agents looking for a vendor-named entry point should
> read this file.

## Build & test

```bash
python -m pip install -e ".[test]"       # editable install with the test extra
python -m pytest -q                      # host-free suite (the default local run)
python -m pytest -m reaper -q            # host lane: needs a running REAPER
python -m ruff check src tests           # lint
python -m ruff format --check src tests  # format check
python -m build                          # wheel + sdist
python -m twine check dist/*             # distribution metadata check
```

Use the `dev` extra for the lint, build and distribution gates.

- **Python:** `>=3.7`. The CI matrix covers 3.7–3.12, so keep syntax and
  dependencies importable on 3.7 unless a job explicitly excludes it.
- **Core pin:** `dcc-mcp-core>=0.20.40,<1.0.0`. Do not lower it without running
  `tests/test_doctor.py`: Core only serves `install_sop_report_schema_version()`
  and `validate_install_sop_report()` from 0.20.40 onward.

## The one thing to know before editing

**REAPER has no headless mode.** CI therefore cannot exercise a real host: it
runs contract checks, lint, packaging and a host-free pytest suite. Tests that
need a live REAPER are marked `reaper` and are skipped by default.

Do not write a test that silently passes without a host. Assert on
`host_available: false` explicitly, or mark the test `reaper` so its skip is
visible. Never mark an item verified on the strength of a green CI run.

## Repo layout

| Path | Role |
|---|---|
| `src/dcc_mcp_reaper/` | Adapter package |
| `src/dcc_mcp_reaper/transport.py` | Transport selection (`in_process` / `external`) |
| `src/dcc_mcp_reaper/runtime.py` | Host discovery and readiness reporting |
| `src/dcc_mcp_reaper/doctor.py` | Install SOP report assembly and validation |
| `src/dcc_mcp_reaper/server.py` | `DccServerBase` composition root |
| `src/dcc_mcp_reaper/cli.py` | `serve` / `doctor` entry points |
| `src/dcc_mcp_reaper/compat.py` | Supported REAPER version lines |
| `src/dcc_mcp_reaper/skills/` | Shipped `reaper-*` skills |
| `tests/` | pytest suite; host-free by default |
| `docs/adr/` | Architecture decision records |
| `docs/validation/` | Manual host-validation records |
| `install.md` | Host-side install for both transports |

## Transport rules

Two transports, selected by `DCC_MCP_REAPER_TRANSPORT`:

- `in_process` (default) — runs inside REAPER as a ReaScript, calls `RPR_*`
  directly. **Requires `--pid`.** Full API surface; needs a matching-bitness
  Python; no UI/graphics and no `get_action_context`.
- `external` — standalone process driving REAPER through `reapy_boost` over the
  Web Browser Interface. **Must not receive `--pid`.** No Python inside REAPER;
  narrower API surface and a network hop per call. The `external` extra installs
  `reapy-boost`, whose importable top-level package is `reapy_boost` — not
  `reapy`, which is a different (unmaintained) distribution.

The server constructor enforces the pairing, so a mismatch fails loudly rather
than half-binding the instance.

## Skill authoring

A skill is `SKILL.md` (YAML front matter with `name` and
`metadata.dcc-mcp.dcc: reaper`) plus `tools.yaml` plus `scripts/`.
`tests/test_skills.py` checks that structure statically — it never imports the
scripts, because importing them would need REAPER's injected `reaper_python`.

Keep tools typed. Do not expose raw ReaScript execution as the primary
workflow when a typed tool can cover the task.

## Release

- release-please drives versioning from Conventional Commits on `main`.
- `chore:` / `ci:` / `style:` / `refactor:` / `test:` / `build:` are hidden;
  `docs:` is a visible `Documentation` section. If every commit in a batch is
  hidden, release-please skips the batch entirely.

## Agent control path

Agents reach this adapter through the shared gateway, not by importing the
package:

```bash
dcc-mcp-cli search --query "<task>" --dcc-type reaper
dcc-mcp-cli describe <tool-slug>
dcc-mcp-cli call <tool-slug> --json '{}'
```
