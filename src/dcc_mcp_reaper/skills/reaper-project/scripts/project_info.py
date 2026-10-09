"""Report path, dirty state, length and tempo of the active REAPER project."""

import json
import sys

from dcc_mcp_reaper.runtime import environment_report
from dcc_mcp_reaper.transport import IN_PROCESS, in_process_module, resolve_transport


def _read_in_process():
    module = in_process_module()
    project = module.RPR_EnumProjects(-1, "", 0)[0]
    return {
        "path": module.RPR_GetProjectPathEx(project, "", 0)[1] or None,
        "name": module.RPR_GetProjectName(project, "", 0)[1] or None,
        "dirty": bool(module.RPR_IsProjectDirty(project)),
        "length": module.RPR_GetProjectLength(project),
        "tempo": module.RPR_Master_GetTempo(),
    }


def main():
    report = environment_report()
    if not report["host_available"]:
        print(
            json.dumps(
                {
                    "host_available": False,
                    "project": None,
                    "note": "REAPER is not reachable; start REAPER and retry.",
                },
                indent=2,
            )
        )
        return 0
    transport = resolve_transport()
    if transport == IN_PROCESS:
        project = _read_in_process()
    else:
        import reapy

        proj = reapy.Project()
        project = {
            "path": proj.path,
            "name": proj.name,
            "dirty": None,
            "length": proj.length,
            "tempo": proj.bpm,
        }
    print(
        json.dumps(
            {"host_available": True, "transport": transport, "project": project},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
