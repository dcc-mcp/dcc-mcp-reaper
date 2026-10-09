"""Report REAPER play state, edit cursor position, and time selection."""

import json
import sys

from dcc_mcp_reaper.runtime import environment_report
from dcc_mcp_reaper.transport import IN_PROCESS, in_process_module, resolve_transport


def _read_in_process():
    module = in_process_module()
    project = module.RPR_EnumProjects(-1, "", 0)[0]
    start, end = module.RPR_GetSet_LoopTimeRange2(project, False, False, 0.0, 0.0, False)[3:5]
    return {
        "play_state": module.RPR_GetPlayState(),
        "edit_cursor": module.RPR_GetCursorPositionEx(project),
        "time_selection_start": start,
        "time_selection_end": end,
    }


def main():
    report = environment_report()
    if not report["host_available"]:
        print(json.dumps({"host_available": False, "transport_state": None}, indent=2))
        return 0
    transport = resolve_transport()
    if transport == IN_PROCESS:
        state = _read_in_process()
    else:
        import reapy

        proj = reapy.Project()
        state = {
            "play_state": int(reapy.Project().is_playing),
            "edit_cursor": proj.cursor_position,
            "time_selection_start": proj.time_selection.start,
            "time_selection_end": proj.time_selection.end,
        }
    print(
        json.dumps(
            {"host_available": True, "transport": transport, "transport_state": state},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
