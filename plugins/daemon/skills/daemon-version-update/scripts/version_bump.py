#!/usr/bin/env python3
"""Work out and apply a semver bump for Claude Code / Codex plugins.

The baseline for each plugin is the last commit that changed the version in
its manifest. Every change to the plugin since then (committed, staged,
unstaged or untracked) is classified:

  major  a skill, command or agent was removed, or the plugin was renamed
  minor  a skill, command or agent was added
  patch  anything else changed (edits to existing skills, scripts, assets...)

Usage:
  version_bump.py [PLUGIN_DIR ...] [--level patch|minor|major] [--dry-run]

With no PLUGIN_DIR, every plugin in the repository is checked. --level
overrides the detected level for every plugin that has changes.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

MANIFESTS = (".claude-plugin/plugin.json", "plugin.json", ".codex-plugin/plugin.json")
MARKETPLACES = (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json")
LEVELS = ("patch", "minor", "major")


def git(*args, check=True):
    result = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)
    if check and result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def find_plugins():
    files = git("ls-files", "--cached", "--others", "--exclude-standard").splitlines()
    dirs = set()
    for f in files:
        for m in MANIFESTS:
            if f == m or f.endswith("/" + m):
                d = f[: -len(m)].rstrip("/") or "."
                if Path(d).name not in (".claude-plugin", ".codex-plugin"):
                    dirs.add(d)
    return sorted(dirs)


def components(paths):
    """Map plugin-relative file paths to the components they belong to."""
    found = set()
    for p in paths:
        parts = p.split("/")
        if len(parts) >= 3 and parts[0] == "skills" and parts[2] == "SKILL.md":
            found.add(f"skill:{parts[1]}")
        elif len(parts) == 2 and parts[0] in ("commands", "agents") and p.endswith(".md"):
            found.add(f"{parts[0][:-1]}:{parts[1][:-3]}")
    return found


def owner(path):
    parts = path.split("/")
    if parts[0] == "skills" and len(parts) > 1:
        return f"skill:{parts[1]}"
    if parts[0] in ("commands", "agents") and len(parts) == 2:
        return f"{parts[0][:-1]}:{Path(parts[1]).stem}"
    return path


def bump(version, level):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    if not m:
        sys.exit(f"'{version}' is not a MAJOR.MINOR.PATCH version")
    major, minor, patch = map(int, m.groups())
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def check_plugin(rel):
    pdir = ROOT / rel
    manifests = [pdir / m for m in MANIFESTS if (pdir / m).exists()]
    data = {m: json.loads(m.read_text()) for m in manifests}
    versions = {d.get("version") for d in data.values()}
    names = {d.get("name") for d in data.values()}
    if len(versions) != 1 or None in versions:
        sys.exit(f"{rel}: manifests disagree on version or lack one: {sorted(map(str, versions))}")
    version, name = versions.pop(), names.pop()

    prefix = "" if rel == "." else rel + "/"
    main = str(manifests[0].relative_to(ROOT))
    base = git("log", "-1", "--format=%H", "-G", r'"version"', "--", main).strip()
    if not base:
        return {"plugin": name, "dir": rel, "version": version, "level": None,
                "note": "no committed version yet; nothing to compare against"}

    base_version = json.loads(git("show", f"{base}:{main}")).get("version")
    if base_version != version:
        return {"plugin": name, "dir": rel, "version": version, "level": None,
                "note": f"version already changed from {base_version} (uncommitted)"}

    def strip(p):
        return p[len(prefix):]

    ignore = {str(m.relative_to(ROOT)) for m in manifests}
    before = {strip(p) for p in git("ls-tree", "-r", "--name-only", base, "--", rel).splitlines()
              if p not in ignore}
    now = {strip(p) for p in git("ls-files", "--cached", "--others", "--exclude-standard", "--", rel).splitlines()
           if p not in ignore and (ROOT / p).exists()}

    added_c = sorted(components(now) - components(before))
    removed_c = sorted(components(before) - components(now))
    modified = {strip(p) for p in git("diff", "--name-only", base, "--", rel).splitlines()} & before & now
    changed = sorted({owner(p) for p in modified | (now ^ before)} - set(added_c) - set(removed_c))

    # Manifest edits other than the version count as changes too.
    for m in manifests:
        path = str(m.relative_to(ROOT))
        try:
            old = json.loads(git("show", f"{base}:{path}"))
        except (SystemExit, json.JSONDecodeError):
            changed.append(strip(path))
            continue
        new = json.loads(m.read_text())
        if old.get("name") != new.get("name"):
            removed_c.append(f"plugin renamed {old.get('name')} -> {new.get('name')}")
        old.pop("version", None)
        new.pop("version", None)
        if old != new:
            changed.append(strip(path))

    level = "major" if removed_c else "minor" if added_c else "patch" if changed else None
    return {"plugin": name, "dir": rel, "version": version, "base": base[:7], "level": level,
            "added": added_c, "removed": removed_c, "changed": sorted(set(changed))}


def apply(result, level):
    new = bump(result["version"], level)
    pdir = ROOT / result["dir"]
    for m in MANIFESTS:
        path = pdir / m
        if path.exists():
            text = path.read_text()
            path.write_text(re.sub(r'("version"\s*:\s*)"[^"]*"', rf'\g<1>"{new}"', text, count=1))
    for mp in MARKETPLACES:
        path = ROOT / mp
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        entry = next((p for p in data.get("plugins", []) if p.get("name") == result["plugin"]), None)
        if entry and "version" in entry:
            entry["version"] = new
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return new


def main():
    global ROOT
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plugins", nargs="*")
    ap.add_argument("--level", choices=LEVELS)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if top.returncode != 0:
        sys.exit("not inside a git repository; the bump level can't be worked out automatically")
    ROOT = Path(top.stdout.strip())

    dirs = [str(Path(p).resolve().relative_to(ROOT)) for p in args.plugins] or find_plugins()
    if not dirs:
        sys.exit("no plugins found (looked for .claude-plugin/plugin.json or plugin.json)")

    for rel in dirs:
        r = check_plugin(rel)
        print(f"{r['plugin']} ({r['dir']}) {r['version']}")
        if r.get("note"):
            print(f"  skipped: {r['note']}")
            continue
        print(f"  since {r['base']}:")
        for key in ("added", "removed", "changed"):
            if r[key]:
                print(f"    {key}: {', '.join(r[key])}")
        if not r["level"]:
            print("  no changes; version stays")
            continue
        level = args.level or r["level"]
        if args.level and LEVELS.index(args.level) < LEVELS.index(r["level"]):
            print(f"  warning: --level {args.level} is lower than the detected {r['level']}")
        detected = "" if level == r["level"] else f" (detected {r['level']})"
        if args.dry_run:
            print(f"  would bump {level}{detected}: {r['version']} -> {bump(r['version'], level)}")
        else:
            print(f"  bumped {level}{detected}: {r['version']} -> {apply(r, level)}")


if __name__ == "__main__":
    main()
