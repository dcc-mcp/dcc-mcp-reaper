---
name: reaper-transport
description: "Read REAPER transport state: play state, edit cursor, time selection."
license: MIT
metadata:
  dcc-mcp:
    dcc: reaper
    layer: host
    tools: tools.yaml
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

- Playback state requires a running REAPER host; this tool reports
  `host_available: false` rather than a fabricated position when REAPER is not
  reachable. Linux can run headlessly with a custom `libSwell` built using
  `NOGDK=1`.
- On the `external` transport each read is a network round trip through the Web
  Browser Interface, so do not poll this tool in a tight loop.
