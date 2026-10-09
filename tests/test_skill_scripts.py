"""Run bundled inspection entry points against hermetic REAPER client doubles."""

import json
import runpy
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from uuid import UUID

import pytest

from dcc_mcp_reaper.transport import ENV_VAR, EXTERNAL, IN_PROCESS

SKILLS_DIR = Path(__file__).resolve().parents[1] / "src" / "dcc_mcp_reaper" / "skills"
SCRIPTS = {
    "project_info": "reaper-project",
    "transport_state": "reaper-transport",
    "list_tracks": "reaper-tracks",
    "list_projects": "reaper-session",
    "session_info": "reaper-session",
}
TRACK_GUIDS = ["{11111111-1111-4111-8111-111111111111}", "{22222222-2222-4222-8222-222222222222}"]
EXPECTED = {
    "project_info": {
        "project": {
            "path": "/session/session.rpp",
            "name": "session.rpp",
            "dirty": False,
            "length": 12.5,
            "tempo": 120.0,
        },
    },
    "transport_state": {
        "transport_state": {
            "play_state": 1,
            "edit_cursor": 2.5,
            "time_selection_start": 1.0,
            "time_selection_end": 4.0,
        },
    },
    "list_tracks": {
        "tracks": [
            {"index": 0, "name": "Music", "guid": TRACK_GUIDS[0], "muted": False, "soloed": True, "fx_count": 2},
            {"index": 1, "name": "Voice", "guid": TRACK_GUIDS[1], "muted": True, "soloed": False, "fx_count": 0},
        ],
    },
}


@pytest.fixture(params=sorted(EXPECTED))
def script_name(request):
    return request.param


@pytest.fixture
def client(monkeypatch):
    """Block installed host modules so these tests cannot contact REAPER."""
    monkeypatch.setenv(ENV_VAR, EXTERNAL)
    for name in ("reapy_boost", "reapy", "reaper_python"):
        monkeypatch.setitem(sys.modules, name, None)
    module = ModuleType("reapy_boost")
    module.get_reaper_version = lambda: "7.82"
    project = SimpleNamespace(
        id="project",
        path="/session",
        name="session.rpp",
        length=12.5,
        bpm=120.0,
        is_playing=True,
        cursor_position=2.5,
        time_selection=SimpleNamespace(start=1.0, end=4.0),
        tracks=[
            SimpleNamespace(
                id=0, name="Music", GUID="(GUID*)0x0000000000000001", is_muted=False, is_solo=True, n_fxs=2
            ),
            SimpleNamespace(
                id=1, name="Voice", GUID="(GUID*)0x0000000000000002", is_muted=True, is_solo=False, n_fxs=0
            ),
        ],
    )
    module.Project = lambda: project

    def get_track_string(track_id, key, value, set_value):
        assert key == "GUID"
        assert set_value is False
        return True, track_id, key, TRACK_GUIDS[track_id], False

    module.reascript_api = SimpleNamespace(
        GetSetMediaTrackInfo_String=get_track_string,
        EnumProjects=lambda index, value, size: (
            ("project" if index in (-1, 0) else None),
            index,
            "/session/session.rpp",
            size,
        ),
        GetProjectName=lambda project, value, size: (project, "session.rpp", size),
        IsProjectDirty=lambda project: 0,
    )
    return module


def _run_script(script_name, monkeypatch, capsys, *args):
    path = SKILLS_DIR / SCRIPTS[script_name] / "scripts" / (script_name + ".py")
    monkeypatch.setattr(sys, "argv", [str(path)] + list(args))
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(str(path), run_name="__main__")
    captured = capsys.readouterr()
    assert captured.err == ""
    return excinfo.value.code, json.loads(captured.out)


@pytest.mark.parametrize("legacy_present", [False, True])
def test_scripts_use_maintained_client(script_name, client, legacy_present, monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "reapy_boost", client)
    if legacy_present:
        # An empty legacy package must not shadow the installed maintained fork.
        monkeypatch.setitem(sys.modules, "reapy", ModuleType("reapy"))
    code, result = _run_script(script_name, monkeypatch, capsys)
    assert code == 0
    assert result == dict(EXPECTED[script_name], host_available=True, transport=EXTERNAL)


def test_scripts_use_validated_legacy_fallback(script_name, client, monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "reapy", client)
    code, result = _run_script(script_name, monkeypatch, capsys)
    assert code == 0
    assert result == dict(EXPECTED[script_name], host_available=True, transport=EXTERNAL)


@pytest.mark.parametrize("legacy_present", [False, True])
def test_scripts_report_misconfigured_client(script_name, client, legacy_present, monkeypatch, capsys):
    if legacy_present:
        monkeypatch.setitem(sys.modules, "reapy", ModuleType("reapy"))
    code, result = _run_script(script_name, monkeypatch, capsys)
    assert code == 1
    assert result["host_available"] is False
    assert "dcc-mcp-reaper[external]" in result["transport_error"]
    assert ("get_reaper_version" if legacy_present else "reapy_boost") in result["transport_error"]
    assert "start REAPER" not in result.get("note", "")
    for key in EXPECTED[script_name]:
        assert result[key] == ([] if key == "tracks" else None)


def test_scripts_report_unreachable_host(script_name, client, monkeypatch, capsys):
    def unreachable():
        raise ConnectionError("REAPER is not running")

    client.get_reaper_version = unreachable
    monkeypatch.setitem(sys.modules, "reapy_boost", client)
    code, result = _run_script(script_name, monkeypatch, capsys)
    assert code == 0
    assert result["host_available"] is False
    assert not result.get("transport_error")
    for key in EXPECTED[script_name]:
        assert result[key] == ([] if key == "tracks" else None)


def test_list_tracks_preserves_limit_with_maintained_client(client, monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "reapy_boost", client)
    code, result = _run_script("list_tracks", monkeypatch, capsys, "--limit", "1")
    assert code == 0
    assert result == {"host_available": True, "transport": EXTERNAL, "tracks": EXPECTED["list_tracks"]["tracks"][:1]}


@pytest.mark.parametrize("null_pointer", [None, 0, "(ReaProject*)0x0000000000000000"])
@pytest.mark.parametrize("tab_count", [0, 2])
def test_list_projects_enumerates_real_python_pointer_format(tab_count, null_pointer, client, monkeypatch, capsys):
    tabs = [
        ("(ReaProject*)0x0000000000000001", "/session/first.rpp", "first.rpp"),
        ("(ReaProject*)0x0000000000000002", "", ""),
    ][:tab_count]
    active = tabs[-1][0] if tabs else null_pointer
    indices = []

    def enum_projects(index, buffer, size):
        assert size > 0
        indices.append(index)
        if index == -1:
            return active, index, "", size
        if index == len(tabs):
            return null_pointer, index, "", size
        pointer, path, _ = tabs[index]
        return pointer, index, path, size

    def get_project_name(pointer, buffer, size):
        assert size > 0
        return pointer, next(tab[2] for tab in tabs if tab[0] == pointer), size

    # Deliberately omit the nonexistent RPR_CountProjects API.
    module = ModuleType("reaper_python")
    module.RPR_GetAppVersion = lambda: "7.82/linux-x86_64"
    module.RPR_EnumProjects = enum_projects
    module.RPR_GetProjectName = get_project_name
    monkeypatch.setenv(ENV_VAR, IN_PROCESS)
    monkeypatch.setitem(sys.modules, "reaper_python", module)
    code, result = _run_script("list_projects", monkeypatch, capsys)
    assert code == 0
    assert result == {
        "host_available": True,
        "transport": IN_PROCESS,
        "project_count": tab_count,
        "projects": [
            {"index": index, "path": path or None, "name": name or None, "active": pointer == active}
            for index, (pointer, path, name) in enumerate(tabs)
        ],
    }
    assert indices == [-1] + list(range(tab_count + 1))


def test_list_projects_fails_instead_of_looping_or_truncating(client, monkeypatch):
    indices = []

    def enum_projects(index, buffer, size):
        indices.append(index)
        return "(ReaProject*)0x0000000000000001", index, "", size

    module = ModuleType("reaper_python")
    module.RPR_GetAppVersion = lambda: "7.82"
    module.RPR_EnumProjects = enum_projects
    module.RPR_GetProjectName = lambda pointer, buffer, size: (pointer, "Untitled", size)
    monkeypatch.setitem(sys.modules, "reaper_python", module)
    monkeypatch.setenv(ENV_VAR, IN_PROCESS)
    namespace = runpy.run_path(str(SKILLS_DIR / SCRIPTS["list_projects"] / "scripts" / "list_projects.py"))
    monkeypatch.setitem(namespace["_read_in_process"].__globals__, "MAX_PROJECTS", 2)
    result = namespace["main"]()
    assert result["success"] is False
    assert "safety limit of 2 tabs" in result["message"]
    assert indices == [-1, 0, 1, 2]


@pytest.mark.parametrize("name", sorted(SCRIPTS))
def test_mcp_entry_returns_structured_data_without_stdout(name, client, monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "reapy_boost", client)
    # MCP host process arguments must never be parsed by a tool's main().
    monkeypatch.setattr(sys, "argv", ["reaper", "--unrelated-host-argument"])
    namespace = runpy.run_path(str(SKILLS_DIR / SCRIPTS[name] / "scripts" / (name + ".py")))
    result = namespace["main"]()
    assert result["success"] is True
    assert result["context"]["host_available"] is True
    assert result["context"]["transport"] == EXTERNAL
    if name in EXPECTED:
        for key, value in EXPECTED[name].items():
            assert result["context"][key] == value
    elif name == "session_info":
        assert result["context"]["host_version"] == "7.82"
    else:
        assert result["context"]["project_count"] == 1
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("name", sorted(SCRIPTS))
def test_mcp_entry_returns_configuration_error_without_stdout(name, client, monkeypatch, capsys):
    namespace = runpy.run_path(str(SKILLS_DIR / SCRIPTS[name] / "scripts" / (name + ".py")))
    result = namespace["main"]()
    assert result["success"] is False
    assert result["error"] == "transport_configuration"
    assert result["context"]["host_available"] is False
    assert "dcc-mcp-reaper[external]" in result["context"]["transport_error"]
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("limit", [None, 1, 2, 10])
def test_list_tracks_accepts_typed_mcp_limit(limit, client, monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "reapy_boost", client)
    namespace = runpy.run_path(str(SKILLS_DIR / SCRIPTS["list_tracks"] / "scripts" / "list_tracks.py"))
    result = namespace["main"](limit=limit)
    assert result["success"] is True
    assert result["context"]["tracks"] == EXPECTED["list_tracks"]["tracks"][:limit]
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("limit", [0, -1, True, "1", 1.5])
def test_list_tracks_rejects_invalid_mcp_limit(limit, client, monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "reapy_boost", client)
    namespace = runpy.run_path(str(SKILLS_DIR / SCRIPTS["list_tracks"] / "scripts" / "list_tracks.py"))
    result = namespace["main"](limit=limit)
    assert result["success"] is False
    assert "positive integer" in result["message"]
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("transport", [IN_PROCESS, EXTERNAL])
def test_list_tracks_returns_guid_values_instead_of_pointers(transport, client, monkeypatch, capsys):
    module = ModuleType("reaper_python")
    module.RPR_GetAppVersion = lambda: "7.82"
    module.RPR_EnumProjects = lambda index, value, size: ("project", index, value, size)
    module.RPR_CountTracks = lambda project: 2
    module.RPR_GetTrack = lambda project, index: index

    def get_track_string(track, key, value, set_value):
        assert set_value is False
        if key == "GUID":
            value = TRACK_GUIDS[track]
        else:
            assert key == "P_NAME"
            value = EXPECTED["list_tracks"]["tracks"][track]["name"]
        return True, track, key, value, False

    module.RPR_GetSetMediaTrackInfo_String = get_track_string
    module.RPR_GetMediaTrackInfo_Value = lambda track, key: 0
    module.RPR_TrackFX_GetCount = lambda track: 0
    # RPR_GetTrackGUID intentionally does not exist in this double: its Python
    # binding returns a pointer to a GUID, not the serializable identifier.
    monkeypatch.setitem(sys.modules, "reaper_python", module)
    monkeypatch.setitem(sys.modules, "reapy_boost", client)
    monkeypatch.setenv(ENV_VAR, transport)
    namespace = runpy.run_path(str(SKILLS_DIR / SCRIPTS["list_tracks"] / "scripts" / "list_tracks.py"))
    result = namespace["main"]()
    assert result["success"] is True
    guids = [track["guid"] for track in result["context"]["tracks"]]
    assert guids == TRACK_GUIDS
    for value in guids:
        assert value == "{%s}" % UUID(value)
    assert json.loads(json.dumps(result))["context"]["tracks"] == result["context"]["tracks"]
    assert capsys.readouterr() == ("", "")


def test_list_tracks_reads_solo_property_without_calling_mutator(client, monkeypatch, capsys):
    class Track:
        id = 1
        name = "Not soloed"
        is_muted = False
        is_solo = False
        n_fxs = 0

        def solo(self):
            raise AssertionError("Read-only track inspection must not change solo state")

    client.Project().tracks = [Track()]
    monkeypatch.setitem(sys.modules, "reapy_boost", client)
    namespace = runpy.run_path(str(SKILLS_DIR / SCRIPTS["list_tracks"] / "scripts" / "list_tracks.py"))
    result = namespace["main"]()
    assert result["success"] is True
    assert result["context"]["tracks"][0]["soloed"] is False
    assert capsys.readouterr() == ("", "")


def test_external_projects_are_enumerated_and_not_assumed_single(client, monkeypatch):
    monkeypatch.setitem(sys.modules, "reapy_boost", client)
    tabs = [("p1", "/a.rpp"), ("p2", "/b.rpp")]

    def enum(index, value, size):
        if index == -1:
            return "p2", index, "/b.rpp", size
        if index >= len(tabs):
            return "(ReaProject*)0x0000000000000000", index, "", size
        return tabs[index][0], index, tabs[index][1], size

    client.reascript_api.EnumProjects = enum
    client.reascript_api.GetProjectName = lambda pointer, value, size: (pointer, pointer + ".rpp", size)
    path = SKILLS_DIR / SCRIPTS["list_projects"] / "scripts" / "list_projects.py"
    result = runpy.run_path(str(path))["main"]()
    assert result["success"]
    assert result["context"]["project_count"] == 2
    assert [x["active"] for x in result["context"]["projects"]] == [False, True]
    assert [x["path"] for x in result["context"]["projects"]] == ["/a.rpp", "/b.rpp"]


def test_external_project_path_is_rpp_not_media_directory(client, monkeypatch):
    monkeypatch.setitem(sys.modules, "reapy_boost", client)
    client.Project().path = "/recordings/media"
    client.reascript_api.IsProjectDirty = lambda project: 1
    path = SKILLS_DIR / SCRIPTS["project_info"] / "scripts" / "project_info.py"
    result = runpy.run_path(str(path))["main"]()
    assert result["context"]["project"]["path"] == "/session/session.rpp"
    assert result["context"]["project"]["dirty"] is True
