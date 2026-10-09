# Host validation records

This directory holds evidence from runs against a **real REAPER installation**.

## Why this directory exists

REAPER has no headless mode, so CI cannot drive a host: it runs contract checks,
lint, packaging and a host-free pytest suite only. Anything that touches the
ReaScript API or `reapy` must be validated on a real machine, and that evidence
lives here.

A green CI run is **not** evidence that host behaviour works.

## What is not verified by CI

- Any `RPR_*` ReaScript call or `reapy` call.
- Interpreter bitness matching against a real 64-bit REAPER.
- Web Browser Interface setup and the one-time `configure_reaper` step.
- Real playback, render, and project-mutation behaviour.

## How to record a validation

Add a dated Markdown file plus its JSON result, following the shape used by
sibling adapters:

| File | Contents |
|---|---|
| `<topic>.md` | What was run, on which REAPER version and OS, and what was observed |
| `<topic>.json` | Machine-readable result: host version, transport, timestamp, pass/fail per check |

State the REAPER version, the OS, the transport used, and the adapter version.
Record failures as failures — an untested path is not a tested path.
