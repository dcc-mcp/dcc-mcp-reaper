# Linux external transport validation — 2026-10-09

## Environment and boundaries

- Debian GNU/Linux 13, x86_64; REAPER 7.82 evaluation from the official Linux archive.
- Vendor-documented custom headless libSwell built with `NOGDK=1` from Cockos WDL commit `d30c30b356b2b7fb1654def8dbda90066f43061a`.
- Embedded and external Python 3.12.14, reapy-boost 0.10.201, dcc-mcp-core 0.20.41, CLI/server 0.20.42.
- Adapter base: `cc84efbe516016c97ef7298b0e8c6b3d71c071db`, with the fixes accompanying this record.
- Source and configuration kept local. No REAPER installer, binary, license key, account data or software documentation is redistributed.
- REAPER is a paid product with a 60-day evaluation. Noncommercial/open-source use is not an indefinite free license. See https://www.reaper.fm/download.php .

## Actual execution

The real host was started, then the official `dcc-mcp-reaper serve --transport external` CLI was started as a separate Python process. Its bundled skills were discovered automatically after the lifecycle fix. A local-only gateway was started with the remote listener disabled. Commands used the official CLI with `--require-gateway` and a stable agent-session identifier.

The validation executed inventory, scoped search, skill load, describe, and calls. The companion JSON retains the final successful call results with execution paths replaced by `WORKSPACE`; endpoint addresses are replaced by `LOOPBACK_ENDPOINT`. This is deliberate sanitization, not a byte-identical raw log.

All five bundled read-only tools returned structured context over MCP:

- session_info: real version 7.82, external transport, reachable host.
- list_projects: enumerated the real tab and full native RPP path.
- project_info: full RPP path, clean dirty-state, 38.4 seconds, 100 BPM.
- list_tracks: five tracks, stable braced GUID values, mute=false, solo=false; `limit=2` returned two tracks.
- transport_state: stopped, cursor and time selection read from the host.

A separate, explicitly added `reaper-stem-session` production skill imported five original synthesized WAV stems, saved/reopened a native RPP, and rendered through REAPER's native offline renderer. Those mutation/render capabilities are **not** capabilities of the bundled read-only inspection package. The saved project retained five tracks, five media items and matching GUIDs after reopen, using relative media paths. Subsequent gateway renders matched the original PCM sample bytes. The master is stereo 48 kHz/24-bit, 1,843,200 frames (38.4 s), with peak −3.2264 dBFS and no clipped samples. Subjective listening remains pending.

## Defects fixed by this change

1. Bundled tools bypassed external_client and imported obsolete `reapy`.
2. Tool mains printed JSON but returned integer 0 to MCP.
3. SKILL.md omitted the tools.yaml linkage and declarations used the wrong schema/source keys.
4. CLI serve did not register bundled skills.
5. In-process project enumeration called nonexistent CountProjects; external enumeration assumed one tab.
6. GetTrackGUID/reapy GUID returned pointer strings, not stable GUID values.
7. `bool(track.solo)` evaluated a bound method as true; use `is_solo`.
8. Project.path/GetProjectPathEx exposed a recording-media directory instead of the project filename.
9. Documentation incorrectly denied Linux headless support and incorrectly said external reapy did not require embedded Python.

## Limits and failed paths

- No hardware audio playback, subjective listening or GUI screenshot is claimed.
- The standard graphical launch was unavailable in this cloud execution environment. The headless build still executes the real host.
- Embedded core/in-process MCP execution hit a Python `os.stat_result` type-identity error here; it remains unverified in this environment. The successful production and final verification used the official external reapy route instead.
- Host-free unit tests are not host evidence. The actual invocation record is separate.
- Wwise Authoring was not installed or tested: official authoring requirements list Windows/macOS, while Linux deployment SDK support does not establish native Linux authoring support.
