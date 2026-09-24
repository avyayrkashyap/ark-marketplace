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

Bump `version` in both manifests when you release changes. Claude Code only
updates installed plugins when the version changes.
