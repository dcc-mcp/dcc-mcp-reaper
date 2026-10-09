"""Readiness reporting never raises when REAPER is absent."""

from dcc_mcp_reaper.runtime import environment_report
from dcc_mcp_reaper.transport import EXTERNAL, IN_PROCESS


def test_report_is_json_serialisable():
    import json

    report = environment_report(IN_PROCESS, environ={})
    assert json.loads(json.dumps(report)) == report


def test_report_names_the_transport():
    assert environment_report(EXTERNAL, environ={})["transport"] == EXTERNAL
    assert environment_report(IN_PROCESS, environ={})["transport"] == IN_PROCESS


def test_reaper_is_reported_as_not_headless():
    assert environment_report(IN_PROCESS, environ={})["headless_host"] is False


def test_absent_host_is_reported_not_raised():
    report = environment_report(IN_PROCESS, environ={})
    assert report["host_available"] is False
    assert report["host_version"] is None


def test_absent_host_produces_a_note():
    notes = environment_report(IN_PROCESS, environ={})["notes"]
    assert any("not reachable" in note for note in notes)


def test_report_always_states_ci_does_not_cover_the_host():
    notes = environment_report(EXTERNAL, environ={})["notes"]
    assert any("no headless mode" in note for note in notes)
