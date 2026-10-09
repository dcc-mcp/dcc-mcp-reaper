"""Bundled skills stay structurally valid without a REAPER host.

Static declarations and core's real discovery/registration path are checked
without importing host modules or contacting REAPER.
"""

from pathlib import Path

import pytest
import yaml
from dcc_mcp_core import SkillCatalog, ToolRegistry, validate_skill

SKILLS_DIR = Path(__file__).resolve().parents[1] / "src" / "dcc_mcp_reaper" / "skills"


def _skills():
    return sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())


def test_at_least_one_skill_ships():
    assert _skills()


@pytest.mark.parametrize("skill_dir", _skills(), ids=lambda p: p.name)
def test_skill_has_a_readme(skill_dir):
    assert (skill_dir / "SKILL.md").is_file()


@pytest.mark.parametrize("skill_dir", _skills(), ids=lambda p: p.name)
def test_skill_front_matter_declares_name_and_dcc(skill_dir):
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    front_matter = yaml.safe_load(text.split("---")[1])
    assert front_matter["name"] == skill_dir.name
    assert front_matter["metadata"]["dcc-mcp"]["dcc"] == "reaper"
    assert front_matter["metadata"]["dcc-mcp"]["tools"] == "tools.yaml"


@pytest.mark.parametrize("skill_dir", _skills(), ids=lambda p: p.name)
def test_every_declared_tool_script_exists(skill_dir):
    tools = yaml.safe_load((skill_dir / "tools.yaml").read_text(encoding="utf-8"))
    for tool in tools["tools"]:
        assert "script" not in tool
        assert "parameters" not in tool
        script = skill_dir / tool["source_file"]
        assert script.is_file(), "%s declares a missing script" % tool["name"]
        assert tool["input_schema"]["type"] == "object"
        assert isinstance(tool["input_schema"]["properties"], dict)
        assert tool["input_schema"]["additionalProperties"] is False
        assert tool["output_schema"]["type"] == "object"
        assert tool["read_only"] is True


@pytest.mark.parametrize("skill_dir", _skills(), ids=lambda p: p.name)
def test_tool_names_are_valid_identifiers(skill_dir):
    tools = yaml.safe_load((skill_dir / "tools.yaml").read_text(encoding="utf-8"))
    for tool in tools["tools"]:
        assert tool["name"].isidentifier()


@pytest.mark.parametrize("skill_dir", _skills(), ids=lambda p: p.name)
def test_skill_scripts_are_py37_parseable(skill_dir):
    import ast

    for script in (skill_dir / "scripts").glob("*.py"):
        source = script.read_text(encoding="utf-8")
        ast.parse(source, filename=str(script))


@pytest.mark.parametrize("skill_dir", _skills(), ids=lambda p: p.name)
def test_core_validates_bundled_skill(skill_dir):
    report = validate_skill(str(skill_dir))
    assert not [issue.message for issue in report.issues if issue.severity == "error"]


@pytest.mark.parametrize("skill_dir", _skills(), ids=lambda p: p.name)
def test_core_registers_declared_schema_and_source(skill_dir):
    registry = ToolRegistry()
    catalog = SkillCatalog(registry)
    catalog.discover([str(SKILLS_DIR)], "reaper")
    loaded = catalog.load_skill(skill_dir.name)
    declarations = yaml.safe_load((skill_dir / "tools.yaml").read_text(encoding="utf-8"))["tools"]
    assert set(loaded) == {skill_dir.name.replace("-", "_") + "__" + tool["name"] for tool in declarations}
    for tool in declarations:
        action = registry.get_action(skill_dir.name.replace("-", "_") + "__" + tool["name"])
        assert action["input_schema"] == tool["input_schema"]
        assert action["output_schema"] == tool["output_schema"]
        assert Path(action["source_file"]) == skill_dir / tool["source_file"]
        assert action["description"] == tool["description"]


def test_list_tracks_declares_positive_integer_limit():
    tools = yaml.safe_load((SKILLS_DIR / "reaper-tracks" / "tools.yaml").read_text(encoding="utf-8"))["tools"]
    limit = next(tool for tool in tools if tool["name"] == "list_tracks")["input_schema"]["properties"]["limit"]
    assert limit["type"] == "integer"
    assert limit["minimum"] == 1
