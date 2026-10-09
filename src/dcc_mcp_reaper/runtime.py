"""Host discovery and readiness reporting.

Every function here is transport-aware and side-effect free with respect to the
host: they report what the adapter can see, never mutate the REAPER project.
REAPER has no headless mode, so on a machine without REAPER these return
``available: False`` and CI never calls them against a real host.
"""

import os
import platform
import sys

from .compat import TARGET_VERSION, is_supported, parse_app_version
from .transport import (
    ENV_VAR,
    IN_PROCESS,
    external_client,
    in_process_module,
    resolve_transport,
)


def _host_version_in_process():
    """Read REAPER's own version string through the in-process API."""
    module = in_process_module()
    raw = module.RPR_GetAppVersion()
    return parse_app_version(raw)[0]


def _host_version_external():
    """Read REAPER's own version string through the external client."""
    reapy = external_client()
    version, _ = parse_app_version(reapy.get_reaper_version())
    return version


def detect_host_version(transport=None):
    """Return the running REAPER version, or ``None`` when unreachable."""
    chosen = resolve_transport(transport)
    try:
        if chosen == IN_PROCESS:
            return _host_version_in_process()
        return _host_version_external()
    except Exception:
        return None


def bitness_matches_host(transport=None):
    """Whether the current interpreter bitness can drive REAPER.

    ReaScript Python requires the interpreter bitness to match REAPER's: a
    64-bit REAPER needs a 64-bit Python. Only meaningful on the in-process
    transport, which is the one that loads Python into REAPER.
    """
    if resolve_transport(transport) != IN_PROCESS:
        return True
    arch = platform.architecture()[0]
    return arch == "64bit" and sys.maxsize > 2**32


def environment_report(transport=None, environ=None):
    """A JSON-serialisable readiness report for ``doctor`` and the CLI."""
    chosen = resolve_transport(transport, environ=environ)
    version = detect_host_version(chosen)
    report = {
        "adapter": "dcc-mcp-reaper",
        "transport": chosen,
        "transport_env_var": ENV_VAR,
        "target_reaper_version": TARGET_VERSION,
        "host_version": version,
        "host_available": version is not None,
        "host_version_supported": is_supported(version) if version else None,
        "python_version": platform.python_version(),
        "python_bitness_ok": bitness_matches_host(chosen),
        "headless_host": False,
        "notes": [],
    }
    if not report["host_available"]:
        report["notes"].append("REAPER is not reachable; the adapter starts as a standalone service.")
    if not report["python_bitness_ok"]:
        report["notes"].append(
            "Interpreter bitness does not match REAPER; ReaScript Python needs a matching 64-bit interpreter."
        )
    report["notes"].append(
        "REAPER has no headless mode; host-side behaviour is verified on a real host and is not covered by CI."
    )
    return report


def reaper_resource_path():
    """REAPER's resource directory, or ``None`` when it is not configured.

    Honours ``DCC_MCP_REAPER_RESOURCE_PATH`` so operator installs and tests can
    point at a portable or network install.
    """
    return os.environ.get("DCC_MCP_REAPER_RESOURCE_PATH") or None
