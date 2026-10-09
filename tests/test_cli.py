"""CLI surface: doctor prints JSON, serve validates its transport arguments."""

import json

import pytest

from dcc_mcp_reaper.cli import main


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert capsys.readouterr().out.strip()


def test_doctor_prints_json(capsys):
    assert main(["doctor"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["adapter"] == "dcc-mcp-reaper"
    assert report["headless_host"] is False


def test_serve_requires_a_pid_for_in_process(capsys):
    with pytest.raises(SystemExit):
        main(["serve", "--transport", "in_process"])
    assert "--pid is required" in capsys.readouterr().err


def test_serve_rejects_a_pid_for_external(capsys):
    with pytest.raises(SystemExit):
        main(["serve", "--transport", "external", "--pid", "1234"])
    assert "only valid for the in_process" in capsys.readouterr().err


def test_no_command_prints_help(capsys):
    assert main([]) == 1
    assert "usage" in capsys.readouterr().out.lower()
