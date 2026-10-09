"""Server construction: the two transports have different binding rules."""

import pytest

from dcc_mcp_reaper.server import ReaperServer
from dcc_mcp_reaper.transport import EXTERNAL, IN_PROCESS


def test_in_process_requires_a_host_pid():
    with pytest.raises(ValueError, match="requires the REAPER host PID"):
        ReaperServer(port=0, dcc_pid=None, transport=IN_PROCESS)


def test_external_rejects_a_host_pid():
    with pytest.raises(ValueError, match="only valid for the in_process"):
        ReaperServer(port=0, dcc_pid=1234, transport=EXTERNAL)


def test_external_transport_constructs():
    server = ReaperServer(port=0, dcc_pid=None, transport=EXTERNAL)
    assert server.transport == EXTERNAL
