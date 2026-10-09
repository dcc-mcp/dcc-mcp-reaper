"""Report the REAPER host version, active transport, and adapter identity."""

import json
import sys

from dcc_mcp_reaper.runtime import environment_report


def main():
    print(json.dumps(environment_report(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
