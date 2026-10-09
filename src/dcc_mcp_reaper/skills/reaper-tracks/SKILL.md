---
name: reaper-tracks
description: "Inspect REAPER tracks: count, names, mute/solo state, FX count."
license: MIT
metadata:
  dcc-mcp:
    dcc: reaper
    layer: host
    version: "0.1.0"
---

# REAPER Tracks

Read-only inspection of the tracks in the active project.

## When to use

Use it to enumerate what is in the session before targeting a specific track by
index or GUID.

## Tools

- `list_tracks` — one row per track with name, mute/solo state, and FX count.

## Constraints

- REAPER has **no headless mode**; a live GUI session is required.
- Track indices are positional and shift when tracks are added or removed, so
  prefer the GUID when a later call has to address the same track.
