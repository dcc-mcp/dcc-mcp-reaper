---
name: reaper-session
description: "Inspect the running REAPER instance: version, transport, project count."
license: MIT
metadata:
  dcc-mcp:
    dcc: reaper
    layer: host
    tools: tools.yaml
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

- Every host-facing call in this skill needs a running, reachable REAPER; when
  the host is absent the tools report `host_available: false` rather than
  failing the MCP call. Linux can run headlessly with a custom `libSwell` built
  using `NOGDK=1`.
- On the `in_process` transport the interpreter bitness must match REAPER's
  (64-bit REAPER requires 64-bit Python).
