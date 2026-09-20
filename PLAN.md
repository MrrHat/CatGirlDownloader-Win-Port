# Crafty+ (working title)

A fork of Crafty Controller 4 with extended features. Single owner, AI assistance via chat.

## Principles

- Free technologies and APIs only. No paid services required for core functionality.
- Secrets (IPs, API keys, passwords) live only in the panel's database/config. Never committed to the repository.
- Every change is a commit. If something breaks, roll back.
- Cross-platform: development on Windows 11, production on Ubuntu 24.04. No hardcoded paths.
- Custom features live in separate modules/pages; core Crafty code is touched minimally (keeps future upstream merges easy).
- Each stage ends with a working, runnable panel.

## Environment

- **Dev:** Windows 11, Python 3.11, Git, VS Code. Run from source, test on localhost.
- **Prod:** Ubuntu 24.04, update = `git pull` + restart.
- Panel data (DB, servers, backups) stays outside git (`.gitignore` — Crafty already ships one that covers this).
- Entry point confirmed: `python main.py` (run from repo root, inside the venv). Do NOT run as Administrator/root — Crafty refuses to start with elevated permissions by design.
- Stack (confirmed): Python, Tornado (web framework), Peewee (ORM), SQLite (database).

## Stage 0 — Scaffolding (DONE)

- Cloned from GitLab (`gitlab.com/crafty-controller/crafty-4`) — this is the actual live repo (GitHub mirror is outdated).
- Remote setup: `upstream` = GitLab (source of future updates), `origin` = own GitHub repo.
- Pushed initial unmodified copy to own GitHub as the zero point.
- Verified `python main.py` runs successfully from source on Windows (non-elevated terminal).
- Confirmed panel version: 4.11.0.
- `.gitignore` already provided by upstream Crafty — data files (DB, configs, logs) are not tracked.

## Stage 1 — Quick wins

- Themes: dark/light + accent colors, selection persists per user.
- CPU/RAM display: visual polish on existing widgets.
- Logs: search, filter, error highlighting, "jump to last crash" button.

## Stage 2 — Management

- Gamerules: read/change on the fly and at server startup.
- Whitelist / OP / ban list managed via buttons (check what Crafty already supports before building from scratch).
- Restart with an in-game chat countdown; countdown duration configurable.
- Port reachability check button (target address comes from server settings, not hardcoded).

## Stage 3 — Mods (main focus)

- Mods page: icons, versions, enable/disable toggle, delete, source badge (Modrinth/CurseForge/manual).
- Search and install mods from Modrinth (free public API).
- Update checker via Modrinth API + one-click update.
- Duplicate handling: installing a new .jar with the same modid automatically replaces the old one; the old version moves to `.trash` (this doubles as "rollback a single mod" — restore from `.trash`).
- Modpack import: `.mrpack` (file upload + URL), CurseForge `.zip` (only if a CurseForge API key is configured in settings — tab hidden otherwise).
- Create a new server directly from a Modrinth modpack by name/search (true one-click, not just file import).
- Install a single mod via direct URL to a `.jar`.
- Mod cache: downloaded `.jar` files are stored locally (keyed by hash, `.mrpack` provides hashes); reinstalling a 250+ mod pack pulls from cache instead of re-downloading everything.
- Bulk actions: filters (outdated / disabled / duplicates / client-side-only) + checkboxes + "update all" button.
- Compatibility check on install: warn if mod's target MC version or loader (Fabric/Forge/NeoForge) doesn't match the server.
- Java auto-select based on MC version (8/16/17/21), auto-download via Temurin, manual override available.
- Server version lists: live-fetched, going as far back as possible (Vanilla/Forge to 1.7.10 where feasible; Fabric ~1.14+; NeoForge 1.20.1+).
- Preflight dependency check before starting the server (offline, no API calls — catches missing required dependencies between installed mods).
- Client-side mod detector: reads `environment: client` from `fabric.mod.json`, flags such mods as "client-only, remove from server" (offline, free).
- `.trash` system for removed mods with one-click restore (this is the "rollback a single mod" feature).
- Confirmation dialog before bulk mod updates: "Create a backup first?" checkbox (manual, just convenient).
- CurseForge API key field in settings; CurseForge-dependent features hidden entirely when no key is set.

## Stage 4 — Crashes

- Offline pattern-based crash diagnosis: a local knowledge base of known crash signatures (built from real troubleshooting patterns, e.g. `Unknown registry key` → orphaned dimension from a removed mod, `NullPointerException ... JsonElement` → broken recipe/registry data, `ClassNotFoundException porting_lib...` → mod/loader version mismatch). No paid API involved.
- "Server failed to start" banner + crash report archive + basic stats (e.g. "3 crashes this week, top cause: X").
- No Anthropic/paid AI analysis in this build — deliberately excluded to keep the project fully free.

## Stage 5 — Dashboard & monitoring

- Configurable widgets: console preview, CPU/RAM, online players + quick actions, uptime.
- Historical graphs: dedicated monitoring page. Default view: last 1 day. Range selector: 1h / 6h / 1d / 7d. Data retention: 7 days max, with downsampling (fresh points every 5s, older points collapsed to per-minute) to keep storage small.
- Hang watchdog: process alive but server unresponsive → banner + force-stop button.
- Server uptime history.

## Stage 6 — Optional / lower priority

- MOTD editor with live preview.
- World manager: download/upload world as zip, list worlds, delete a specific world (without a full server backup).
- Player stats (read from world save files, offline): playtime, deaths, distance traveled.
- Player head avatars in online list and whitelist (free API, no key, purely cosmetic).
- Server cloning (for testing mods without risking the main world).
- Mod changelog ("what changed since the last known-working version").
- Server notes field ("what is this server for / what I'm testing here").
- Ctrl+K quick search across servers/mods/settings.
- Notification when a new version of the fork itself is available (checks own GitHub releases).
- Search across old (rotated) log files, not just the current one — lowest priority overall.

## Explicitly NOT doing (frozen decision)

- Discord bridge / webhooks
- Public status page (no-login friend-facing page)
- Disk/RAM warning banners
- Mod "profiles" (saved sets to switch between)
- Modpack export feature
- Paid AI crash analysis (Anthropic API) — replaced by the offline pattern-based system in Stage 4
- Electricity cost tracker
- Russian localization
- Inline help/tooltips for server.properties fields

## Process

- One feature at a time: spec → code → visual test in browser → commit.
- On error: paste the text/screenshot into chat → get a fix → retry.
- Merging upstream Crafty updates is handled as its own careful, separate step — never mixed with feature work.
