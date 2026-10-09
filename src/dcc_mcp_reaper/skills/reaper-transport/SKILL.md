---
name: reaper-transport
description: "Read REAPER transport state: play state, edit cursor, time selection."
license: MIT
metadata:
  dcc-mcp:
    dcc: reaper
    layer: host
    version: "0.1.0"
---

# REAPER Transport

Read-only view of the REAPER transport.

## When to use

Use it to find out where the playhead is and whether REAPER is playing, before
scheduling edits or a render.

## Tools

- `transport_state` — play state, edit cursor position, and time selection.

## Constraints

- REAPER has **no headless mode**; playback state only exists in a live GUI
  session, so this tool reports `host_available: false` rather than a
  fabricated position when REAPER is not running.
- On the `external` transport each read is a network round trip through the Web
  Browser Interface, so do not poll this tool in a tight loop.
