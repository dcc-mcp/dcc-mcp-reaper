---
name: reaper-project
description: "Inspect the active REAPER project: path, dirty state, length, tempo."
license: MIT
metadata:
  dcc-mcp:
    dcc: reaper
    layer: host
    tools: tools.yaml
    version: "0.1.0"
---

# REAPER Project

Read-only inspection of the active REAPER project (`.rpp`).

## When to use

Reach for this before mutating anything, so the tool call can name the project
it is about to touch and report the dirty state afterwards.

## Tools

- `project_info` — path, dirty flag, length, and tempo of the active project.

## Constraints

- A real REAPER host must be running and reachable over the selected transport.
  Linux can run headlessly with a custom `libSwell` built using `NOGDK=1`.
- ReaScript Python has no `get_action_context` support, so this skill never
  reports how a script was invoked.
