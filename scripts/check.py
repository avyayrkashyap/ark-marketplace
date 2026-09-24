#!/usr/bin/env python3
"""Check that the Claude and Codex marketplace catalogs list the same plugins
and that every plugin has matching manifests for both agents."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []


def load(path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        errors.append(f"missing {path.relative_to(ROOT)}")
    except json.JSONDecodeError as e:
        errors.append(f"invalid JSON in {path.relative_to(ROOT)}: {e}")
    return None


claude = load(ROOT / ".claude-plugin/marketplace.json") or {}
codex = load(ROOT / ".agents/plugins/marketplace.json") or {}

claude_plugins = {p["name"]: p["source"] for p in claude.get("plugins", [])}
codex_plugins = {p["name"]: p["source"]["path"] for p in codex.get("plugins", [])}

for name in sorted(claude_plugins.keys() ^ codex_plugins.keys()):
    where = "Claude" if name in claude_plugins else "Codex"
    errors.append(f"{name}: listed only in the {where} marketplace")

for p in codex.get("plugins", []):
    for field in ("policy", "category"):
        if field not in p:
            errors.append(f"{p['name']}: Codex entry is missing '{field}'")

for name in sorted(claude_plugins.keys() & codex_plugins.keys()):
    if Path(claude_plugins[name]) != Path(codex_plugins[name]):
        errors.append(f"{name}: source paths differ between marketplaces")
    plugin_dir = ROOT / claude_plugins[name]
    c = load(plugin_dir / ".claude-plugin/plugin.json")
    x = load(plugin_dir / "plugin.json")
    if c and x:
        for field in ("name", "version", "description"):
            if c.get(field) != x.get(field):
                errors.append(f"{name}: '{field}' differs between manifests")
        if c.get("name") != name:
            errors.append(f"{name}: manifest name is '{c.get('name')}'")
    for skill in (plugin_dir / "skills").glob("*/"):
        if not (skill / "SKILL.md").exists():
            errors.append(f"{name}: {skill.relative_to(ROOT)} has no SKILL.md")

if errors:
    print("\n".join(f"✘ {e}" for e in errors))
    sys.exit(1)
print(f"✔ {len(claude_plugins)} plugin(s) in sync across Claude and Codex")
