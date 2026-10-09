# ADR 0001: REAPER transport — in-process ReaScript Python as the default

- **Status:** Accepted
- **Date:** 2026-10-09
- **Host:** REAPER 7.82 (Cockos), Windows / macOS / Linux

## Context

The adapter needs one channel over which to drive REAPER. Two candidates were
measured against the official documentation rather than chosen by default.

### Candidate A — In-process ReaScript Python

REAPER embeds a Python interpreter and injects a `reaper_python` module exposing
the `RPR_*` extension API. From the official
[ReaScript page](https://www.reaper.fm/sdk/reascript/reascript.php):

- "ReaScript should work with any version of Python between 2.7 and the current
  3.x release." — so Python 3.7 sits inside the supported range and satisfies
  the PIP-2519 3.7 red line.
- "For 32-bit REAPER, you need 32-bit Python... For 64-bit REAPER, you need
  64-bit Python." — the interpreter bitness must match the host.
- "Python must be downloaded and installed separately... and as such, will never
  be as portable between users as EEL or Lua."
- Python "does not offer any UI or graphic features" — unlike EEL2 and Lua,
  which both support script windows, docking and drawing primitives.
- `get_action_context()` is documented as "(sorry, no Python support)", so
  MIDI/OSC/mouse-wheel binding context is unavailable to Python scripts.
- Performance is called out as "not as good as EEL or Lua".

### Candidate B — External control via reapy / Web Browser Interface

`reapy` (and its maintained fork `reapy-boost`, the fork this adapter
recognises) drives REAPER from a separate Python process. From PyPI metadata:

- `reapy-boost` 0.10.201 declares `requires_python >=3.7`, matching this
  package's floor exactly.
- `python-reapy` 0.10.0 declares `requires_python >=3.0`.
- The `reapy` name on PyPI resolves to a `0.0` placeholder with no metadata,
  which is why the adapter treats `reapy` as an optional extra and does not pin
  the bare name.

Costs of the external path: it requires REAPER's Web Browser Interface to be
enabled, a matching Python shared library for the server ReaScript, a one-time
`configure_reaper` step, and a REAPER restart. `configure_reaper()` enables
ReaScript Python and registers `activate_reapy_server.py`; only the adapter
process runs outside REAPER. Every call
becomes a network round trip (the upstream project quotes roughly 30–60 calls
per second), and the wrapper exposes a narrower surface than the raw `RPR_*`
API.

## Decision

**Default to the in-process ReaScript Python transport (`in_process`), and keep
the external transport (`external`) selectable through
`DCC_MCP_REAPER_TRANSPORT`.**

Reasons, in order of weight:

1. **API surface.** The typed-tools contract this adapter ships is built on
   `RPR_*` functions. The in-process path reaches all of them; the external path
   reaches only what the wrapper has modelled. Choosing the narrower surface as
   the default would cap the skill set before it is written.
2. **Structural fit.** Every other embedded-Python adapter in the org (Blender,
   Houdini, Nuke, FreeCAD) runs inside the host and dispatches onto the host
   thread through `HostExecutionBridge`. The in-process path reuses that shape
   instead of introducing a second remote-call convention.
3. **The costs are known and bounded.** The three documented in-process costs —
   user-installed matching-bitness Python, no UI/graphics, no
   `get_action_context` — are all acceptable here: bitness is checked at runtime
   and reported by `doctor`; this adapter ships no UI or drawing tools; and no
   skill depends on action-binding context.
4. **The external path stays available as an opt-in** for users who want the
   adapter to run in a separate process. The reapy bridge still requires
   embedded Python inside REAPER.

The selection is data-driven from an environment variable rather than hard-coded
so both paths are testable without a live host.

## Consequences

- `DccServerOptions.from_env("reaper", ...)` is constructed with
  `instance_type="gui"` and a bound `dcc_pid` on the in-process transport, and
  `instance_type="standalone"` with no bound PID on the external one. The two
  shapes have different liveness semantics and are validated separately.
- `reapy-boost` is an optional dependency under the `external` extra, so the
  in-process install stays lean. The extra installs the maintained fork, whose
  importable top-level package is **`reapy_boost`**; the code imports that name,
  not `reapy`. The bare `reapy` name on PyPI is an empty placeholder, so it is
  not used as a fallback unless it exposes `get_reaper_version`.
- Current CI does not launch a real REAPER host. Linux REAPER supports
  headless operation with a custom `libSwell.so` built using `NOGDK=1`, as
  documented in the official Linux tarball's `readme-linux.txt`; this still
  requires a running host and a configured transport. Host validation is
  recorded under `docs/validation/`; a passing host-free suite alone is not
  evidence that either transport works against REAPER.
