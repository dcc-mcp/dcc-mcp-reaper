---
name: reaper-project
description: "Inspect the active REAPER project: path, dirty state, length, tempo."
license: MIT
metadata:
  dcc-mcp:
    dcc: reaper
    layer: host
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

- REAPER has **no headless mode**; a real GUI session must be running.
- ReaScript Python has no `get_action_context` support, so this skill never
  reports how a script was invoked.
