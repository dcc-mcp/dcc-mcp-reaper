"""Readiness reporting never raises when REAPER is absent."""

import sys
import types

import pytest

from dcc_mcp_reaper.runtime import detect_host_version, environment_report
from dcc_mcp_reaper.transport import (
    EXTERNAL,
    IN_PROCESS,
    TransportConfigError,
)


def test_report_is_json_serialisable():
    import json

    report = environment_report(IN_PROCESS, environ={})
    assert json.loads(json.dumps(report)) == report


def test_report_names_the_transport():
    assert environment_report(EXTERNAL, environ={})["transport"] == EXTERNAL
    assert environment_report(IN_PROCESS, environ={})["transport"] == IN_PROCESS


@pytest.mark.parametrize("transport", [IN_PROCESS, EXTERNAL])
@pytest.mark.parametrize("version", [None, "7.82"])
def test_host_display_mode_is_unknown_even_when_reachable(monkeypatch, transport, version):
    monkeypatch.setattr("dcc_mcp_reaper.runtime.detect_host_version", lambda chosen: version)
    report = environment_report(transport, environ={})
    assert report["host_available"] is (version is not None)
    assert report["headless_host"] is None


def test_absent_host_is_reported_not_raised():
    report = environment_report(IN_PROCESS, environ={})
    assert report["host_available"] is False
    assert report["host_version"] is None


def test_absent_host_produces_a_note():
    notes = environment_report(IN_PROCESS, environ={})["notes"]
    assert any("not reachable" in note for note in notes)


def test_report_always_states_ci_does_not_cover_the_host():
    notes = environment_report(EXTERNAL, environ={})["notes"]
    assert any("CI suite is host-free" in note for note in notes)


def test_report_explains_headless_support_without_claiming_detection():
    notes = environment_report(IN_PROCESS, environ={})["notes"]
    assert any("Host display mode is unknown" in note and "NOGDK=1" in note for note in notes)


class TestTransportMisconfiguration:
    """A broken transport must not be disguised as an unreachable host.

    The broad ``except Exception`` used to turn a missing optional dependency
    into ``host_available: false``, so the doctor told users to start REAPER
    for a problem that no amount of starting REAPER would fix.
    """

    @pytest.fixture(autouse=True)
    def _no_reapy(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "reapy_boost", None)
        monkeypatch.setitem(sys.modules, "reapy", None)

    def test_detect_host_version_raises_instead_of_returning_none(self):
        with pytest.raises(TransportConfigError):
            detect_host_version(EXTERNAL)

    def test_report_carries_the_transport_error(self):
        report = environment_report(EXTERNAL, environ={})
        assert report["transport_error"]
        assert "reapy_boost" in report["transport_error"]

    def test_report_stays_serialisable(self):
        import json

        report = environment_report(EXTERNAL, environ={})
        assert json.loads(json.dumps(report)) == report

    def test_report_does_not_blame_the_absent_host(self):
        notes = environment_report(EXTERNAL, environ={})["notes"]
        assert not any("not reachable" in note for note in notes)
        assert any("misconfigured" in note.lower() for note in notes)

    def test_report_is_clean_when_the_host_is_simply_absent(self):
        """An unreachable host is not an error -- that path stays as it was."""
        report = environment_report(IN_PROCESS, environ={})
        assert report["transport_error"] is None
        assert report["host_available"] is False


def test_report_is_clean_when_the_client_is_installed(monkeypatch):
    module = types.ModuleType("reapy_boost")
    module.get_reaper_version = lambda: "7.82/x64"
    monkeypatch.setitem(sys.modules, "reapy_boost", module)
    report = environment_report(EXTERNAL, environ={})
    assert report["transport_error"] is None
    assert report["host_version"] == "7.82"
