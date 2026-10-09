"""Report path, dirty state, length and tempo of the active REAPER project."""

import sys

from dcc_mcp_core.skill import skill_entry

from dcc_mcp_reaper.runtime import environment_report
from dcc_mcp_reaper.skill_support import inspection_result, print_cli_result
from dcc_mcp_reaper.transport import IN_PROCESS, external_client, in_process_module, resolve_transport


def _read_in_process():
    module = in_process_module()
    project, _, path, _ = module.RPR_EnumProjects(-1, "", 4096)
    return {
        "path": path or None,
        "name": module.RPR_GetProjectName(project, "", 4096)[1] or None,
        "dirty": bool(module.RPR_IsProjectDirty(project)),
        "length": module.RPR_GetProjectLength(project),
        "tempo": module.RPR_Master_GetTempo(),
    }


@skill_entry
def main() -> dict:
    report = environment_report()
    if not report["host_available"]:
        result = {"host_available": False, "project": None}
        if report["transport_error"]:
            result["transport_error"] = report["transport_error"]
        else:
            result["note"] = "REAPER is not reachable; start REAPER and retry."
        return inspection_result("REAPER is not reachable", result)
    transport = resolve_transport()
    if transport == IN_PROCESS:
        project = _read_in_process()
    else:
        reapy = external_client()

        proj = reapy.Project()
        project = {
            "path": reapy.reascript_api.EnumProjects(-1, "", 4096)[2] or None,
            "name": proj.name,
            "dirty": bool(reapy.reascript_api.IsProjectDirty(proj.id)),
            "length": proj.length,
            "tempo": proj.bpm,
        }
    return inspection_result(
        "Active REAPER project", {"host_available": True, "transport": transport, "project": project}
    )


def cli_main():
    return print_cli_result(main())


if __name__ == "__main__":
    sys.exit(cli_main())
