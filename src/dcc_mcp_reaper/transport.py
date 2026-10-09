"""Transport selection for the REAPER adapter.

REAPER is reachable over two materially different channels, and which one is in
use decides what the adapter can do:

``in_process``
    The adapter runs *inside* REAPER as a ReaScript Python script. It calls the
    ``RPR_*`` API directly through the ``reaper_python`` module REAPER injects.
    Full API surface, no network hop, but it requires the user to have installed
    a Python whose bitness matches REAPER, and ReaScript Python deliberately has
    no UI, no graphics, and no ``get_action_context`` support.

``external``
    The adapter runs in its own process and drives REAPER through ``reapy_boost``
    (the maintained fork shipped by the ``external`` extra), which needs REAPER's
    Web Browser Interface enabled and a one-time ``configure_reaper`` plus
    restart. Zero Python installation inside REAPER, at the cost of a narrower
    API surface and a network round trip per call. ``reapy_boost`` requires
    Python >= 3.7, which matches this package's floor.

The choice is data-driven from ``DCC_MCP_REAPER_TRANSPORT`` so tests and CI can
exercise both paths without a live host. See ``docs/adr/0001-transport.md``.
"""

IN_PROCESS = "in_process"
EXTERNAL = "external"

TRANSPORTS = (IN_PROCESS, EXTERNAL)

DEFAULT_TRANSPORT = IN_PROCESS

ENV_VAR = "DCC_MCP_REAPER_TRANSPORT"


class TransportError(RuntimeError):
    """Raised when a transport is requested but cannot be honoured."""


class TransportConfigError(TransportError):
    """The selected transport is installed or configured incorrectly.

    Distinct from the host merely being unreachable: REAPER not running is an
    expected state that readiness reporting should describe, whereas a missing
    optional dependency or an unusable client is a fault the user must fix.
    """


def resolve_transport(value=None, environ=None):
    """Return the transport name to use.

    ``value`` wins when given; otherwise ``DCC_MCP_REAPER_TRANSPORT`` is read
    from ``environ`` (defaulting to ``os.environ``). An empty or unset value
    falls back to :data:`DEFAULT_TRANSPORT`. Unknown values are rejected rather
    than silently downgraded, because a typo should not look like a working
    in-process setup.
    """
    import os

    chosen = value
    if chosen is None:
        chosen = (environ if environ is not None else os.environ).get(ENV_VAR)
    if chosen is None or not str(chosen).strip():
        return DEFAULT_TRANSPORT
    chosen = str(chosen).strip().lower()
    if chosen not in TRANSPORTS:
        raise TransportError("unknown REAPER transport %r; expected one of %s" % (chosen, ", ".join(TRANSPORTS)))
    return chosen


def in_process_module():
    """Return the ``reaper_python`` module REAPER injects into ReaScript Python.

    Raises :class:`TransportError` when the adapter is not running inside a
    REAPER process, so callers get one explicit failure instead of an obscure
    ``ImportError``.
    """
    try:
        import reaper_python  # type: ignore[import-not-found]
    except ImportError as exc:
        raise TransportError(
            "in_process transport requires REAPER's injected reaper_python module; "
            "run this adapter as a ReaScript, or set %s=%s" % (ENV_VAR, EXTERNAL)
        ) from exc
    return reaper_python


def external_client():
    """Return the ``reapy_boost`` client module for out-of-process control.

    The ``external`` extra installs ``reapy-boost``, whose top-level package is
    ``reapy_boost``; the ``python-reapy`` distribution that provides a top-level
    ``reapy`` is a different package. Importing only ``reapy`` here would make
    the transport fail even on a correctly-installed ``.[external]``.

    A top-level ``reapy`` is still accepted, but only when it actually exposes
    :func:`get_reaper_version`: the bare ``reapy`` distribution on PyPI is an
    empty placeholder, so falling back to it unconditionally would turn a clear
    install error into an ``AttributeError`` further down the call stack.

    Raises :class:`TransportConfigError` when no usable client is installed. It
    is an optional dependency: the in-process path must remain installable
    without it.
    """
    try:
        import reapy_boost  # type: ignore[import-not-found]

        return reapy_boost
    except ImportError:
        pass

    try:
        import reapy  # type: ignore[import-not-found]
    except ImportError as exc:
        raise TransportConfigError(
            "external transport requires the 'reapy_boost' module; "
            "install it with 'pip install dcc-mcp-reaper[external]'"
        ) from exc

    if not hasattr(reapy, "get_reaper_version"):
        raise TransportConfigError(
            "the installed 'reapy' module does not expose get_reaper_version; "
            "install the maintained fork with 'pip install dcc-mcp-reaper[external]'"
        )
    return reapy
