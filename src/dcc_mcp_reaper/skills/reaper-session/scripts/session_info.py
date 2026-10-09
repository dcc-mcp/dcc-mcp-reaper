"""Report the REAPER host version, active transport, and adapter identity."""

import sys

from dcc_mcp_core.skill import skill_entry

from dcc_mcp_reaper.runtime import environment_report
from dcc_mcp_reaper.skill_support import inspection_result, print_cli_result


@skill_entry
def main() -> dict:
    return inspection_result("REAPER session readiness", environment_report())


def cli_main():
    return print_cli_result(main())


if __name__ == "__main__":
    sys.exit(cli_main())
