"""Transport resolution is data-driven and rejects typos loudly."""

import importlib
import sys
import types

import pytest

from dcc_mcp_reaper.transport import (
    DEFAULT_TRANSPORT,
    ENV_VAR,
    EXTERNAL,
    IN_PROCESS,
    TransportConfigError,
    TransportError,
    external_client,
    in_process_module,
    resolve_transport,
)


def _stub_module(monkeypatch, name, **attrs):
    """Put a fake module on ``sys.modules`` and drop it after the test."""
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    monkeypatch.setitem(sys.modules, name, module)
    return module


def test_defaults_to_in_process_without_env():
    assert resolve_transport(environ={}) == DEFAULT_TRANSPORT == IN_PROCESS


def test_reads_transport_from_environ():
    assert resolve_transport(environ={ENV_VAR: EXTERNAL}) == EXTERNAL


def test_explicit_value_wins_over_environ():
    assert resolve_transport(EXTERNAL, environ={ENV_VAR: IN_PROCESS}) == EXTERNAL


def test_value_is_case_and_space_insensitive():
    assert resolve_transport(" External ", environ={}) == EXTERNAL


def test_empty_env_value_falls_back_to_default():
    assert resolve_transport(environ={ENV_VAR: "   "}) == DEFAULT_TRANSPORT


def test_unknown_transport_is_rejected():
    with pytest.raises(TransportError, match="unknown REAPER transport"):
        resolve_transport("websockets", environ={})


def test_error_message_lists_valid_choices():
    with pytest.raises(TransportError) as excinfo:
        resolve_transport("nope", environ={})
    message = str(excinfo.value)
    assert IN_PROCESS in message and EXTERNAL in message


def test_in_process_module_returns_reaper_python(monkeypatch):
    sentinel = _stub_module(monkeypatch, "reaper_python", RPR_GetAppVersion=lambda: "7.82")
    assert in_process_module() is sentinel


def test_in_process_module_raises_outside_reaper(monkeypatch):
    monkeypatch.setitem(sys.modules, "reaper_python", None)
    with pytest.raises(TransportError, match="reaper_python"):
        in_process_module()


def test_external_client_returns_installed_reapy_boost(monkeypatch):
    """The ``.[external]`` install must be importable under its real name.

    The extra ships ``reapy-boost``, whose top-level package is ``reapy_boost``.
    Without a test pinning that name, a future drift in either direction fails
    silently -- the old code asked for a package the extra never installed.
    """
    sentinel = _stub_module(monkeypatch, "reapy_boost", get_reaper_version=lambda: "7.82")
    assert external_client() is sentinel


def test_external_client_exposes_get_reaper_version(monkeypatch):
    """The symbol ``runtime`` actually calls must be on the returned module."""
    _stub_module(monkeypatch, "reapy_boost", get_reaper_version=lambda: "7.82")
    assert callable(external_client().get_reaper_version)


def test_external_client_falls_back_to_reapy_with_the_expected_api(monkeypatch):
    monkeypatch.setitem(sys.modules, "reapy_boost", None)
    sentinel = _stub_module(monkeypatch, "reapy", get_reaper_version=lambda: "7.82")
    assert external_client() is sentinel


def test_external_client_rejects_reapy_without_get_reaper_version(monkeypatch):
    """The bare PyPI ``reapy`` is an empty placeholder; do not return it.

    Returning it would push an ``AttributeError`` into the caller's broad
    ``except Exception`` instead of surfacing the install problem here.
    """
    monkeypatch.setitem(sys.modules, "reapy_boost", None)
    _stub_module(monkeypatch, "reapy")
    with pytest.raises(TransportConfigError, match="get_reaper_version"):
        external_client()


def test_external_client_error_names_the_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "reapy_boost", None)
    monkeypatch.setitem(sys.modules, "reapy", None)
    with pytest.raises(TransportConfigError, match=r"dcc-mcp-reaper\[external\]"):
        external_client()


def test_external_client_error_does_not_repeat_the_failed_command(monkeypatch):
    """The message must name the module, not just re-prescribe the install."""
    monkeypatch.setitem(sys.modules, "reapy_boost", None)
    monkeypatch.setitem(sys.modules, "reapy", None)
    with pytest.raises(TransportConfigError) as excinfo:
        external_client()
    assert "reapy_boost" in str(excinfo.value)


def test_missing_client_is_a_config_error_not_a_plain_transport_error(monkeypatch):
    """A missing dependency must be distinguishable from an absent host."""
    monkeypatch.setitem(sys.modules, "reapy_boost", None)
    monkeypatch.setitem(sys.modules, "reapy", None)
    with pytest.raises(TransportConfigError) as excinfo:
        external_client()
    assert isinstance(excinfo.value, TransportError)


def test_absent_host_is_a_plain_transport_error(monkeypatch):
    """REAPER not running is unreachable, not misconfigured."""
    monkeypatch.setitem(sys.modules, "reaper_python", None)
    with pytest.raises(TransportError) as excinfo:
        in_process_module()
    assert not isinstance(excinfo.value, TransportConfigError)


def test_transport_module_has_no_stale_reapy_only_import():
    """Guard the regression directly: the source must reference reapy_boost."""
    source = importlib.import_module("dcc_mcp_reaper.transport")
    import inspect

    assert "reapy_boost" in inspect.getsource(source)
