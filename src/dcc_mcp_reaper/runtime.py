"""Host discovery and readiness reporting.

Every function here is transport-aware and side-effect free with respect to the
host: they report what the adapter can see, never mutate the REAPER project.
When no running REAPER is reachable, readiness reports ``host_available: False``.
Host display mode is not detected; Linux can run headlessly with a custom
libSwell build.
"""

import os
import platform
import sys

from .compat import TARGET_VERSION, is_supported, parse_app_version
from .transport import (
    ENV_VAR,
    IN_PROCESS,
    TransportConfigError,
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
    """Return the running REAPER version, or ``None`` when unreachable.

    A :class:`TransportConfigError` means the selected transport is
    misconfigured -- a missing optional dependency, or a client that cannot
    satisfy the contract. That is not the same thing as REAPER being
    unreachable, so it propagates instead of being reported as ``None``.

    A plain :class:`TransportError` covers the ordinary "host not there" case
    (REAPER is not running, so ``reaper_python`` was never injected) and still
    resolves to ``None``.
    """
    chosen = resolve_transport(transport)
    try:
        if chosen == IN_PROCESS:
            return _host_version_in_process()
        return _host_version_external()
    except TransportConfigError:
        raise
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
    """A JSON-serialisable readiness report for ``doctor`` and the CLI.

    A transport that cannot be honoured is reported as ``transport_error``
    rather than raised: the doctor's job is to explain a broken install, so it
    must stay runnable on one. An unreachable host is not an error, so it keeps
    the ordinary ``host_available: false`` path. ``headless_host`` is ``None``
    (unknown) because neither transport currently detects the host display mode.
    """
    chosen = resolve_transport(transport, environ=environ)
    try:
        version = detect_host_version(chosen)
        transport_error = None
    except TransportConfigError as exc:
        version = None
        transport_error = str(exc)
    report = {
        "adapter": "dcc-mcp-reaper",
        "transport": chosen,
        "transport_env_var": ENV_VAR,
        "target_reaper_version": TARGET_VERSION,
        "host_version": version,
        "host_available": version is not None,
        "transport_error": transport_error,
        "host_version_supported": is_supported(version) if version else None,
        "python_version": platform.python_version(),
        "python_bitness_ok": bitness_matches_host(chosen),
        "headless_host": None,
        "notes": [],
    }
    if transport_error:
        report["notes"].append("Transport misconfigured: %s" % transport_error)
    elif not report["host_available"]:
        report["notes"].append("REAPER is not reachable; the adapter starts as a standalone service.")
    if not report["python_bitness_ok"]:
        report["notes"].append(
            "Interpreter bitness does not match REAPER; ReaScript Python needs a matching 64-bit interpreter."
        )
    report["notes"].append(
        "Host display mode is unknown; Linux REAPER supports headless operation with a custom libSwell (NOGDK=1)."
    )
    report["notes"].append(
        "The current CI suite is host-free; host-side behaviour requires separate validation against running REAPER."
    )
    return report


def reaper_resource_path():
    """REAPER's resource directory, or ``None`` when it is not configured.

    Honours ``DCC_MCP_REAPER_RESOURCE_PATH`` so operator installs and tests can
    point at a portable or network install.
    """
    return os.environ.get("DCC_MCP_REAPER_RESOURCE_PATH") or None
