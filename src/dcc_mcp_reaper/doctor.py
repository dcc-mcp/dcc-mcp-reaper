"""Install SOP self-check and report assembly.

The doctor is where the adapter turns what :mod:`dcc_mcp_reaper.runtime` can see
into an Install SOP report, then validates that report against the schema Core
publishes. Reading the schema revision from Core rather than re-declaring it
locally is what keeps the report from drifting when Core republishes the
artifact (contract rule A002).
"""

from . import __version__
from .runtime import environment_report

try:  # Core >= 0.20.40, which is this package's declared floor.
    from dcc_mcp_core import install_sop_report_schema_version, validate_install_sop_report
except ImportError:  # pragma: no cover - defensive; the floor guarantees it
    install_sop_report_schema_version = None
    validate_install_sop_report = None

DCC_TYPE = "reaper"

INSTALL_STEPS = (
    ("package", "install the dcc-mcp-reaper package"),
    ("host", "make REAPER reachable over the selected transport"),
    ("verify", "confirm the host version and interpreter bitness"),
)


def schema_version():
    """The report schema revision, read from Core when Core exposes it."""
    if install_sop_report_schema_version is not None:
        return install_sop_report_schema_version()
    return None


def core_version():
    """The installed dcc-mcp-core version, or ``None`` when unavailable."""
    try:
        import dcc_mcp_core
    except ImportError:  # pragma: no cover - defensive; the floor guarantees it
        return None
    return getattr(dcc_mcp_core, "__version__", None)


def _steps(env):
    """Map the readiness checks onto the Install SOP step list."""
    checks = {
        "host_reachable": env["host_available"],
        "host_version_supported": bool(env["host_version_supported"]),
        "python_bitness_matches_host": env["python_bitness_ok"],
    }
    return [
        {"id": "install-package", "status": "ok", "description": INSTALL_STEPS[0][1]},
        {
            "id": "connect-host",
            "status": "ok" if checks["host_reachable"] else "planned",
            "description": INSTALL_STEPS[1][1],
        },
        {
            "id": "verify-host",
            "status": "ok" if checks["host_version_supported"] and checks["python_bitness_matches_host"] else "planned",
            "description": INSTALL_STEPS[2][1],
        },
    ]


def _verify_block(env):
    usable = bool(env["host_available"] and env["host_version_supported"] and env["python_bitness_ok"])
    reason = None
    stage = None
    if env.get("transport_error"):
        stage, reason = "transport", env["transport_error"]
    elif not env["host_available"]:
        stage, reason = "host", "REAPER is not reachable over the selected transport"
    elif not env["host_version_supported"]:
        stage, reason = "host", "the running REAPER version is on an unsupported line"
    elif not env["python_bitness_ok"]:
        stage, reason = "verify", "interpreter bitness does not match REAPER"
    return {"directly_usable": usable, "failure_stage": stage, "failure_reason": reason}


def _next_steps(env):
    """Concrete remediation steps, empty when the install is already usable."""
    if env["host_available"] and env["host_version_supported"] and env["python_bitness_ok"]:
        return []
    steps = []
    if env.get("transport_error"):
        steps.append(
            {
                "id": "fix-transport",
                "description": "Fix the selected transport's configuration",
                "why": env["transport_error"],
                "command": ["pip", "install", "dcc-mcp-reaper[external]"],
            }
        )
    if not env["host_available"] and not env.get("transport_error"):
        steps.append(
            {
                "id": "start-reaper",
                "description": "Start REAPER and enable the selected transport",
                "why": "REAPER has no headless mode; the host must be running to be driven.",
                "command": ["dcc-mcp-reaper", "doctor"],
            }
        )
    if env["host_available"] and not env["host_version_supported"]:
        steps.append(
            {
                "id": "upgrade-reaper",
                "description": "Move to a supported REAPER 6.x or 7.x release",
                "why": "Older or newer major lines are not covered by the compatibility matrix.",
                "command": ["dcc-mcp-reaper", "doctor"],
            }
        )
    if not env["python_bitness_ok"]:
        steps.append(
            {
                "id": "match-bitness",
                "description": "Install a Python whose bitness matches REAPER",
                "why": "ReaScript Python requires a 64-bit interpreter for a 64-bit REAPER.",
                "command": ["dcc-mcp-reaper", "doctor"],
            }
        )
    return steps


def build_report(transport=None, environ=None):
    """Assemble an Install SOP report for this installation."""
    env = environment_report(transport=transport, environ=environ)
    report = {
        "schema_version": schema_version(),
        "status": "ok" if env["host_available"] else "planned",
        "dcc_type": DCC_TYPE,
        "adapter_version": __version__,
        "core_version": core_version(),
        "steps": _steps(env),
        "next_steps": _next_steps(env),
        "receipt_path": None,
        "verify": _verify_block(env),
    }
    report["notes"] = env["notes"]
    report["environment"] = env
    return report


def validate(report=None):
    """Validate a report against Core's schema.

    Returns ``(ok, errors)``. When Core does not expose the validator the check
    reports that instead of passing silently, so a missing Core feature never
    looks like a validated install.
    """
    if report is None:
        report = build_report()
    if validate_install_sop_report is None:
        return False, ["dcc-mcp-core does not expose validate_install_sop_report"]
    try:
        validate_install_sop_report(report)
    except Exception as exc:
        return False, [str(exc)]
    return True, []
