"""Report REAPER play state, edit cursor position, and time selection."""

import sys

from dcc_mcp_core.skill import skill_entry

from dcc_mcp_reaper.runtime import environment_report
from dcc_mcp_reaper.skill_support import inspection_result, print_cli_result
from dcc_mcp_reaper.transport import IN_PROCESS, external_client, in_process_module, resolve_transport


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


@skill_entry
def main() -> dict:
    report = environment_report()
    if not report["host_available"]:
        result = {"host_available": False, "transport_state": None}
        if report["transport_error"]:
            result["transport_error"] = report["transport_error"]
        return inspection_result("REAPER is not reachable", result)
    transport = resolve_transport()
    if transport == IN_PROCESS:
        state = _read_in_process()
    else:
        reapy = external_client()

        proj = reapy.Project()
        state = {
            "play_state": int(proj.is_playing),
            "edit_cursor": proj.cursor_position,
            "time_selection_start": proj.time_selection.start,
            "time_selection_end": proj.time_selection.end,
        }
    return inspection_result(
        "REAPER transport state", {"host_available": True, "transport": transport, "transport_state": state}
    )


def cli_main():
    return print_cli_result(main())


if __name__ == "__main__":
    sys.exit(cli_main())
