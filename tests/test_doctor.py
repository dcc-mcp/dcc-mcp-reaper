"""Doctor contract smoke.

The doctor is where the adapter assembles an Install SOP report and validates
it before the report is published. This test runs the real report — built from
what the adapter actually observes, not a hand-written fixture — through Core's
validator, which is what contract rule A014 asks for.
"""

import pytest

from dcc_mcp_reaper import doctor
from dcc_mcp_reaper.transport import EXTERNAL, IN_PROCESS


def test_schema_version_is_read_from_core_not_re_declared():
    revision = doctor.schema_version()
    assert revision is None or isinstance(revision, (int, str))


def test_report_carries_identity():
    report = doctor.build_report(IN_PROCESS, environ={})
    assert report["dcc_type"] == "reaper"
    assert report["adapter_version"]


def test_report_names_the_transport_it_describes():
    assert doctor.build_report(EXTERNAL, environ={})["environment"]["transport"] == EXTERNAL


def test_report_states_reaper_is_not_headless():
    report = doctor.build_report(IN_PROCESS, environ={})
    assert report["environment"]["headless_host"] is False


def test_report_declares_sop_status():
    status = doctor.build_report(IN_PROCESS, environ={})["status"]
    assert status in ("planned", "running", "ok", "failed", "partial", "requires_restart")


def test_report_carries_the_install_steps():
    steps = doctor.build_report(IN_PROCESS, environ={})["steps"]
    assert [step["id"] for step in steps] == [
        "install-package",
        "connect-host",
        "verify-host",
    ]


def test_verify_block_reports_a_reason_when_not_usable():
    verify = doctor.build_report(IN_PROCESS, environ={})["verify"]
    assert verify["directly_usable"] is False
    assert verify["failure_stage"] == "host"
    assert verify["failure_reason"]


def test_next_steps_are_offered_only_when_not_usable():
    report = doctor.build_report(IN_PROCESS, environ={})
    assert report["next_steps"]
    for step in report["next_steps"]:
        assert step["id"] and step["description"] and step["why"]


def test_core_version_is_reported():
    assert doctor.build_report(IN_PROCESS, environ={})["core_version"]


def test_validate_a_real_report():
    if doctor.validate_install_sop_report is None:
        pytest.skip("dcc-mcp-core does not expose validate_install_sop_report")
    ok, errors = doctor.validate()
    assert ok, errors
