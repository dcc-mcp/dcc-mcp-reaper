"""List the project tabs currently open in this REAPER instance."""

import sys

from dcc_mcp_core.skill import skill_entry

from dcc_mcp_reaper.runtime import environment_report
from dcc_mcp_reaper.skill_support import inspection_result, print_cli_result
from dcc_mcp_reaper.transport import IN_PROCESS, external_client, in_process_module, resolve_transport

MAX_PROJECTS = 1024


def _enumerate_projects(enum_projects, get_name):
    active = enum_projects(-1, "", 4096)[0]
    projects = []
    # There is no CountProjects API. Enumerate zero-based tabs until REAPER
    # returns a null pointer (a nonempty string in its Python bindings).
    for index in range(MAX_PROJECTS + 1):
        project, _, path, _ = enum_projects(index, "", 4096)
        if not project or project == "(ReaProject*)0x0000000000000000":
            return projects
        if index == MAX_PROJECTS:
            raise RuntimeError("REAPER project enumeration exceeded the safety limit of %s tabs" % MAX_PROJECTS)
        projects.append(
            {
                "index": index,
                "path": path or None,
                "name": get_name(project, "", 4096)[1] or None,
                "active": project == active,
            }
        )


def _read_in_process():
    module = in_process_module()
    return _enumerate_projects(module.RPR_EnumProjects, module.RPR_GetProjectName)


@skill_entry
def main() -> dict:
    report = environment_report()
    transport = resolve_transport()
    if not report["host_available"]:
        result = {"projects": [], "host_available": False}
        if report["transport_error"]:
            result["transport_error"] = report["transport_error"]
        return inspection_result("REAPER is not reachable", result)
    if transport == IN_PROCESS:
        projects = _read_in_process()
        count = len(projects)
    else:
        api = external_client().reascript_api
        projects = _enumerate_projects(api.EnumProjects, api.GetProjectName)
        count = len(projects)
    return inspection_result(
        "Open REAPER project tabs",
        {"host_available": True, "transport": transport, "project_count": count, "projects": projects},
    )


def cli_main():
    return print_cli_result(main())


if __name__ == "__main__":
    sys.exit(cli_main())
