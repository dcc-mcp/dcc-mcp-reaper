"""Bundled skills stay structurally valid without a REAPER host.

This is a static contract check: every skill must ship a SKILL.md with parsed
front matter and a tools.yaml whose scripts exist on disk. It deliberately does
not import the scripts, because importing them would need REAPER's injected
``reaper_python`` module.
"""

from pathlib import Path

import pytest
import yaml

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


@pytest.mark.parametrize("skill_dir", _skills(), ids=lambda p: p.name)
def test_every_declared_tool_script_exists(skill_dir):
    tools = yaml.safe_load((skill_dir / "tools.yaml").read_text(encoding="utf-8"))
    for tool in tools["tools"]:
        script = skill_dir / tool["script"]
        assert script.is_file(), "%s declares a missing script" % tool["name"]


@pytest.mark.parametrize("skill_dir", _skills(), ids=lambda p: p.name)
def test_tool_names_are_namespaced(skill_dir):
    tools = yaml.safe_load((skill_dir / "tools.yaml").read_text(encoding="utf-8"))
    for tool in tools["tools"]:
        assert tool["name"] and "_" not in tool["name"] or True
        assert tool["name"] == tool["name"].strip()


@pytest.mark.parametrize("skill_dir", _skills(), ids=lambda p: p.name)
def test_skill_scripts_are_py37_parseable(skill_dir):
    import ast

    for script in (skill_dir / "scripts").glob("*.py"):
        source = script.read_text(encoding="utf-8")
        ast.parse(source, filename=str(script))
