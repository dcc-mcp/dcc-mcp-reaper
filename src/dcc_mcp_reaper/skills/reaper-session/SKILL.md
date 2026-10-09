---
name: reaper-session
description: "Inspect the running REAPER instance: version, transport, project count."
license: MIT
metadata:
  dcc-mcp:
    dcc: reaper
    layer: host
    version: "0.1.0"
---

# REAPER Session

Read-only inspection of the REAPER instance the adapter is attached to.

## When to use

Use this skill first when you need to know *which* REAPER you are talking to
before doing work: the transport in use decides what is possible, and the host
version decides which ReaScript API functions exist.

## Tools

- `session_info` — host version, transport, and adapter identity.
- `list_projects` — the project tabs currently open in this instance.

## Constraints

- REAPER has **no headless mode**. Every host-facing call in this skill needs a
  running REAPER with a GUI session; on a machine with no REAPER the tools
  report `host_available: false` rather than failing the MCP call.
- On the `in_process` transport the interpreter bitness must match REAPER's
  (64-bit REAPER requires 64-bit Python).
