"""Hermetic test fixtures.

The default suite is deliberately host-free, regardless of GUI/headless support.
``DCC_MCP_DISABLE_DEFAULT_SKILL_PATHS`` keeps core's implicit skill discovery
from pulling in a developer's local or marketplace skills, while the adapter's
own bundled skills stay active.
"""

import os

import pytest

os.environ.setdefault("DCC_MCP_DISABLE_DEFAULT_SKILL_PATHS", "1")
os.environ.setdefault("DCC_MCP_DISABLE_TELEMETRY", "1")


@pytest.fixture(autouse=True)
def _isolated_transport(monkeypatch):
    """Clear the transport env var so tests opt in to a transport explicitly."""
    monkeypatch.delenv("DCC_MCP_REAPER_TRANSPORT", raising=False)
