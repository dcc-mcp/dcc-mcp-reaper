"""REAPER version parsing and the supported-line matrix."""

from dcc_mcp_reaper.compat import (
    SUPPORTED_MAJOR_LINES,
    is_supported,
    major_line,
    parse_app_version,
)


def test_parse_app_version_splits_arch_suffix():
    assert parse_app_version("7.82/x64") == ("7.82", "x64")


def test_parse_app_version_without_suffix():
    assert parse_app_version("7.82") == ("7.82", None)


def test_parse_app_version_handles_empty():
    assert parse_app_version("") == ("", None)
    assert parse_app_version(None) == ("", None)


def test_major_line():
    assert major_line("7.82/x64") == "7"
    assert major_line("6.81") == "6"


def test_current_release_is_supported():
    assert is_supported("7.82/x64") is True


def test_supported_lines_cover_6_and_7():
    assert SUPPORTED_MAJOR_LINES == ("6", "7")


def test_unsupported_major_line():
    assert is_supported("5.99") is False


def test_unknown_version_is_not_supported():
    assert is_supported("") is False
