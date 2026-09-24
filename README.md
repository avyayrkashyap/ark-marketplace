# ARK Marketplace

A plugin marketplace for both **Claude Code** and **Codex**. Each plugin lives
once under `plugins/` and ships a manifest for each agent, so its skills work in
both.

## Install

**Claude Code**

```
/plugin marketplace add avyayrkashyap/ark-marketplace
/plugin install ark-starter@ark-marketplace
```

**Codex**

```
codex plugin marketplace add avyayrkashyap/ark-marketplace
```

Then open `/plugins` in Codex and install `ark-starter`.

## Plugins

| Plugin | Description |
| --- | --- |
| [ark-starter](plugins/ark-starter) | Starter plugin with an example skill. Copy it to make new plugins. |
| [daemon](plugins/daemon) | Maintenance tools for plugin authors. `daemon-version-update` bumps plugin versions following semver. |

## Layout

```
.claude-plugin/marketplace.json     Claude Code catalog
.agents/plugins/marketplace.json    Codex catalog
plugins/<name>/
  .claude-plugin/plugin.json        Claude Code manifest
  plugin.json                       Codex manifest
  skills/<skill>/SKILL.md           Skills, shared by both agents
```

## Add a plugin

1. Copy `plugins/ark-starter` to `plugins/<name>` and rename it in both
   manifests.
2. Add skills under `plugins/<name>/skills/<skill>/SKILL.md`.
3. Add an entry to **both** `.claude-plugin/marketplace.json` and
   `.agents/plugins/marketplace.json`.
4. Run the checks:

   ```
   python3 scripts/check.py
   claude plugin validate .
   ```

To turn a logo into terminal art, run
`python3 scripts/img2blocks.py path/to/logo.png 20` (needs Pillow), then tidy
the result by hand. Small logos (3 rows or so) usually need hand-drawing.

`ark-starter` shows its logo from a `UserPromptExpansion` hook, so it appears
instantly and in color when you type `/hello`, instead of the model typing it
out. The logo lives in `plugins/ark-starter/assets/banner.txt`; after editing
it, run `python3 plugins/ark-starter/assets/build_banner.py` to rebuild the
colored hook output, and update the copy in the skill's SKILL.md.

Bump versions with the `daemon-version-update` skill, or run
`python3 plugins/daemon/skills/daemon-version-update/scripts/version_bump.py`.
It follows semver: edits to existing skills are a patch, new skills are a minor
bump, and removals, renames or breaking changes are major. Claude Code only
updates installed plugins when the version changes.
