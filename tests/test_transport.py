"""Transport resolution is data-driven and rejects typos loudly."""

import pytest

from dcc_mcp_reaper.transport import (
    DEFAULT_TRANSPORT,
    ENV_VAR,
    EXTERNAL,
    IN_PROCESS,
    TransportError,
    resolve_transport,
)


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
