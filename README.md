# dcc-mcp-reaper

REAPER adapter for [DCC-MCP](https://github.com/dcc-mcp): session, project,
transport and track inspection for AI agents driving Cockos REAPER.

REAPER is the first digital audio workstation in the DCC-MCP ecosystem, filling
the general-purpose DAW gap alongside `dcc-mcp-wwise` (game audio middleware),
`dcc-mcp-premiere` and `dcc-mcp-kdenlive` (video timelines).

## Status

**Alpha.** The adapter ships read-only inspection tools. Host-side behaviour is
verified on a real REAPER installation and is **not** covered by CI, because
REAPER has no headless mode — see [Unverified in CI](#unverified-in-ci).

| | |
|---|---|
| Host | REAPER 7.82 (Cockos), Windows / macOS / Linux |
| Supported lines | REAPER 6.x and 7.x |
| Python | `>=3.7` (PIP-2519 red line) |
| Core | `dcc-mcp-core>=0.20.40,<1.0.0` |

## Install

```bash
pip install dcc-mcp-reaper
# optional, only for the out-of-process transport:
pip install "dcc-mcp-reaper[external]"
```

See [install.md](install.md) for the host-side setup for each transport.

## Transports

REAPER is reachable two ways, and the one you pick decides what is possible.
The choice is recorded in [ADR 0001](docs/adr/0001-transport.md).

### `in_process` (default)

The adapter runs *inside* REAPER as a ReaScript Python script and calls the
`RPR_*` API directly.

- Full ReaScript API surface; no network hop.
- Requires a Python installed on the machine whose bitness matches REAPER
  (64-bit REAPER needs 64-bit Python), enabled under
  `Options > Preferences > Plug-Ins > ReaScript`.
- ReaScript Python has **no UI or graphics support** and **no
  `get_action_context()` support**. This adapter ships neither, so the limit
  does not bind here.

```bash
dcc-mcp-reaper serve --pid <reaper-pid>
```

### `external`

The adapter runs in its own process and drives REAPER over REAPER's Web Browser
Interface through `reapy_boost` (installed by the `external` extra).

- No Python installation needed inside REAPER.
- Needs the Web Browser Interface enabled, plus a one-time `configure_reaper`
  and a REAPER restart.
- Narrower API surface, and each call is a network round trip — avoid polling in
  a tight loop.

```bash
export DCC_MCP_REAPER_TRANSPORT=external
dcc-mcp-reaper serve
```

## Usage

```bash
dcc-mcp-reaper doctor          # readiness report as JSON
dcc-mcp-reaper --version
```

Agents reach the adapter through the shared gateway rather than importing the
package:

```bash
dcc-mcp-cli search --query "list reaper tracks" --dcc-type reaper
dcc-mcp-cli describe <tool-slug>
dcc-mcp-cli call <tool-slug> --json '{}'
```

## Bundled skills

| Skill | Tools |
|---|---|
| `reaper-session` | `session_info`, `list_projects` |
| `reaper-project` | `project_info` |
| `reaper-transport` | `transport_state` |
| `reaper-tracks` | `list_tracks` |

## Unverified in CI

CI runs contract checks, lint, packaging and a host-free pytest suite. It does
**not** run REAPER, because REAPER has no headless mode and cannot be driven on
a runner.

The following are therefore **not verified by CI** and rely on manual host
validation:

- Any call that reaches the ReaScript API (`RPR_*`) or `reapy`.
- Bitness matching against a real 64-bit REAPER.
- Web Browser Interface setup and the `configure_reaper` one-time step.
- Real playback, render, and project-mutation behaviour.

When a host-side check is run manually, record it under `docs/validation/`. Do
not mark an item verified on the strength of a green CI run.

## Development

```bash
python -m pip install -e ".[test]"
python -m pytest -q
python -m ruff check src tests
python -m ruff format --check src tests
python -m build
```

## License

MIT — see [LICENSE](LICENSE).
