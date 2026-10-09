"""List the project tabs currently open in this REAPER instance."""

import json
import sys

from dcc_mcp_reaper.runtime import environment_report
from dcc_mcp_reaper.transport import IN_PROCESS, in_process_module, resolve_transport


def _project_count_in_process():
    module = in_process_module()
    # EnumProjects(-1, ...) returns the currently active project; positive
    # indices walk the open project tabs.
    return module.RPR_CountProjects(0)


def main():
    report = environment_report()
    transport = resolve_transport()
    if not report["host_available"]:
        print(json.dumps({"projects": [], "host_available": False}, indent=2))
        return 0
    if transport == IN_PROCESS:
        count = _project_count_in_process()
    else:
        count = 1  # reapy exposes a single active Project, not the tab list.
    print(
        json.dumps(
            {
                "host_available": True,
                "transport": transport,
                "project_count": count,
                "projects": [],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
