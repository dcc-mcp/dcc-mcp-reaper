"""Composition root using core lifecycle, discovery and execution dispatch."""

from pathlib import Path

from dcc_mcp_core import DccServerBase, DccServerOptions, HostExecutionBridge

from . import __version__
from .transport import IN_PROCESS, resolve_transport


class ReaperServer(DccServerBase):
    """MCP service for one REAPER instance.

    REAPER has no headless mode, so this server runs in one of two shapes:

    ``in_process``
        Started from a ReaScript inside REAPER. The host PID is the REAPER
        process and host API calls are dispatched onto REAPER's own thread.

    ``external``
        Started as a standalone service that drives REAPER over the Web Browser
        Interface through ``reapy``. No host PID is bound, because the adapter
        process owns its own lifetime and REAPER may restart independently.
    """

    def __init__(self, port=None, dcc_pid=None, dcc_version=None, transport=None, **kwargs):
        chosen = resolve_transport(transport)
        if chosen == IN_PROCESS and dcc_pid is None:
            raise ValueError("in_process transport requires the REAPER host PID")
        if chosen != IN_PROCESS and dcc_pid is not None:
            raise ValueError("dcc_pid is only valid for the in_process transport")
        options = DccServerOptions.from_env(
            "reaper",
            Path(__file__).parent / "skills",
            port=port,
            server_name="dcc-mcp-reaper",
            adapter_version=__version__,
            instance_type="gui" if dcc_pid is not None else "standalone",
            dcc_pid=dcc_pid,
            dcc_version=dcc_version,
            execution_bridge=HostExecutionBridge(dispatcher=None),
            **kwargs,
        )
        super().__init__(options=options)
        self.transport = chosen

    def _version_string(self):
        return "unknown"
