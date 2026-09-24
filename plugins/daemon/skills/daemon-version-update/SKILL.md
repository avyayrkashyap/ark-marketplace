---
name: daemon-version-update
description: Bumps a plugin's version following semver, based on what changed since the last version bump. Use when the user asks to bump, update, or release a plugin version, or before publishing plugin changes.
---

# Daemon version update

Bump the version of Claude Code / Codex plugins using these rules:

| Change since the last version bump | Bump |
| --- | --- |
| Edits to existing skills, commands, agents, scripts, assets or manifests | patch (`1.2.3` → `1.2.4`) |
| A new skill, command or agent added to the plugin | minor (`1.2.3` → `1.3.0`) |
| Anything bigger: a skill, command or agent removed or renamed, the plugin renamed, or a breaking change to how an existing skill is used | major (`1.2.3` → `2.0.0`) |

If several rules apply, use the highest one.

## Steps

1. **Preview.** Run the bundled script with `--dry-run` from anywhere inside the
   repository. It lives in `scripts/version_bump.py` next to this file (in
   Claude Code: `${CLAUDE_SKILL_DIR}/scripts/version_bump.py`).

   ```bash
   python3 <skill-dir>/scripts/version_bump.py --dry-run [PLUGIN_DIR ...]
   ```

   With no plugin directories it checks every plugin in the repo. For each
   plugin it compares against the last commit that changed the version and lists
   what was added, removed and changed, plus the bump it detected.

2. **Look for breaking changes the script can't see.** For every plugin whose
   detected level is patch or minor, read the diff of its changed skills
   (`git diff <base> -- <plugin-dir>`; the script prints `<base>`). Escalate to
   major if an existing skill's use changes incompatibly, for example: its
   `name` in the frontmatter changes, arguments it expects are removed or change
   meaning, or it now does something users relying on it wouldn't expect.

3. **Apply.** Run the script again without `--dry-run`. Pass `--level major`
   only when step 2 found a breaking change, and only for that plugin's
   directory. Never pass a level lower than the one detected.

   The script updates the version in every manifest the plugin has
   (`.claude-plugin/plugin.json`, `plugin.json`, `.codex-plugin/plugin.json`)
   and in marketplace entries that carry a `version`, so they stay in sync.

4. **Report.** Tell the user each plugin's old → new version and the reason for
   the level in one line. Don't commit unless the user asks.

## When the script can't decide

- **Not a git repository, or no committed version yet:** nothing to compare
  against. Show the user the current version and ask which level they want,
  then run the script with `--level`.
- **Version already changed but not committed:** the plugin was bumped since
  the last commit. Don't bump it again; tell the user.
- **Manifests disagree on the version:** stop and show the user the values.
  Don't guess which one is right.
