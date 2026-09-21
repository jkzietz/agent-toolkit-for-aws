"""Tests that every hook command's ${CLAUDE_PLUGIN_ROOT} target actually exists.

This guards a failure mode that has already shipped once. Upstream, the SessionStart
hook and the file it cats were added in the same commit, and a later "re-sync skill
trees" commit deleted the file while leaving hooks.json pointing at it. `cat` on a
missing path exits non-zero, so the hook failed for every user on every session start,
and nothing caught it — the manifest was still valid JSON and the spec validator does
not read hook payloads.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]

# Matches ${CLAUDE_PLUGIN_ROOT}/some/path, stopping at whitespace, quotes or shell
# metacharacters so a command with arguments or a pipeline still yields a clean path.
PLUGIN_ROOT_REF = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"'|;&>)]+)")


def hooks_files() -> list[Path]:
    """Every hooks.json the plugin manifest actually points at."""
    manifest = json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))
    found = []
    for namespace in manifest.get("extensions", {}).values():
        rel = namespace.get("hooks")
        if rel:
            found.append((PLUGIN_ROOT / rel).resolve())
    return found


def hook_commands() -> list[tuple[Path, str]]:
    """(hooks_file, command) for every command-type hook declared."""
    commands = []
    for path in hooks_files():
        payload = json.loads(path.read_text(encoding="utf-8"))
        for matchers in payload.get("hooks", {}).values():
            for matcher in matchers:
                for hook in matcher.get("hooks", []):
                    if hook.get("type") == "command" and hook.get("command"):
                        commands.append((path, hook["command"]))
    return commands


def test_manifest_declares_a_hooks_file() -> None:
    """A silently-dropped hooks path would make the rest of this file vacuous."""
    declared = hooks_files()
    assert declared, "plugin.json declares no hooks file under any extension namespace"
    for path in declared:
        assert path.is_file(), f"plugin.json points at a missing hooks file: {path}"


def test_hooks_are_declared() -> None:
    assert hook_commands(), "no command hooks found; this test would pass vacuously"


@pytest.mark.parametrize(
    ("hooks_file", "command"),
    hook_commands(),
    ids=lambda v: v.name if isinstance(v, Path) else v[:60],
)
def test_hook_command_targets_exist(hooks_file: Path, command: str) -> None:
    referenced = PLUGIN_ROOT_REF.findall(command)
    assert referenced, (
        f"{hooks_file.name}: command does not reference ${{CLAUDE_PLUGIN_ROOT}}, so its "
        f"target cannot be verified and it will not resolve on an installed plugin: {command!r}"
    )
    for rel in referenced:
        target = (PLUGIN_ROOT / rel).resolve()
        assert target.is_file(), (
            f"{hooks_file.name}: hook command references "
            f"${{CLAUDE_PLUGIN_ROOT}}/{rel}, which does not exist. The hook will fail "
            f"for every user on every session. Command: {command!r}"
        )
        # Containment: a hook must not reach outside the plugin directory.
        assert target.is_relative_to(PLUGIN_ROOT), (
            f"{hooks_file.name}: hook command escapes the plugin directory: {rel}"
        )
