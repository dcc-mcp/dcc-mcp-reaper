"""Shared structured-result and standalone CLI helpers for inspection skills."""

import json

from dcc_mcp_core.skill import skill_error, skill_success


def inspection_result(message, data):
    """Keep transport configuration failures distinct from an absent host."""
    if data.get("transport_error"):
        return skill_error(data["transport_error"], "transport_configuration", **data)
    return skill_success(message, **data)


def print_cli_result(result):
    """Preserve the standalone JSON payload without printing during MCP calls."""
    print(json.dumps(result.get("context") or result, indent=2))
    return 0 if result["success"] else 1
