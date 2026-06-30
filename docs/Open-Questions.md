# Open Questions

Decisions to resolve before/early in implementation. Each links to the note where it matters.

## Data source (highest priority)

- [x] **Where do Max-plan usage numbers come from?** ✅ **Resolved:** `GET https://api.anthropic.com/api/oauth/usage` (the undocumented endpoint behind `claude.ai/settings/usage`), as used by `m13v/claude-meter`. See [[Usage-Data-Provider]].
- [x] **Authentication**: ✅ **Resolved:** piggyback on the Claude Code CLI's stored Bearer token (Linux: `~/.claude/.credentials.json` → `claudeAiOauth`; verified present on this machine). We **read-only**, never refresh — Claude Code rotates it. No KWallet token of our own. See [[Usage-Data-Provider#Authentication — piggyback on Claude Code]].
- [x] What **unit** does the endpoint report and the exact **JSON field names**? ✅ **Resolved** (live captures 2026-06-30): a `utilization` float **already in percent (0–100)** per window; **no** token/message counts. Full schema in [[API-Reference-Usage-Endpoint]].
- [x] How is the reset expressed? ✅ **Resolved:** `resets_at` ISO-8601 tz-aware datetime per window (may be `null` when a window is inactive). We store the concrete timestamp — see [[Usage-Limits-and-Windows]].
- [x] Does the endpoint split the **weekly** limit (all-models vs. Sonnet-only)? ✅ **Resolved:** yes — `seven_day` (all) and per-model scoped buckets (`seven_day_sonnet`, `seven_day_opus`). ✅ **Decided:** surface **all** model-scoped windows via dynamic discovery (`windows.mode = auto`), each with independent thresholds + alerts. See [[Usage-Limits-and-Windows#Windows are discovered dynamically]].
- [ ] Per-model coverage is bounded by the API: **no per-model 5-hour** window exists, and the all-models `weekly` bucket can't be decomposed. Confirm the full set of model-scoped `kind`s the endpoint can emit (only Sonnet seen populated; Opus null). Capture when other models are used.
- [ ] Do we surface the **extra-usage / overage** block (`extra_usage`) as a third indicator? (Disabled on this account; revisit if enabled.) See [[API-Reference-Usage-Endpoint]].
- [x] ⚠️ **`limits[].percent` scale** ✅ **Resolved** (2026-06-30, `utilization=3.0`/`percent=3`): both `utilization` and `percent` are **0–100**, and agree. We use `utilization` (the float) directly as the percentage. Earlier `× 100` assumption was a bug, now fixed in code.
- [ ] Confirm `limits[].severity` value set (only `normal` observed). We compute our own thresholds regardless.

## Behaviour

- [ ] Should `AlertState.lastNotified` be **persisted across restarts** so we don't re-warn after a relaunch within the same window? See [[Data-Model#What gets persisted vs. in-memory]].
- [ ] Default for `reArmOnDecrease` — keep `false`? See [[Notifications-and-Alerts#Falling usage]].
- [ ] Should `100%`/critical alerts **break through quiet hours** by default? See [[Configuration-Reference#Quiet hours]].
- [ ] Minimum safe `pollIntervalSeconds` given the chosen data source (rate limits?).

## Technology

- [x] **C++/KF6 vs Python/PySide6?** ✅ **Decided: Python + PySide6** (PySide6 6.11.1 already installed; Plasma 6.6.5 / Qt6 host). Tray via `QSystemTrayIcon`, notifications via D-Bus / Qt; no C++ toolchain needed. See [[Technology-Stack]].
- [ ] Config serialization: with Python chosen, lean to **TOML** (stdlib `tomllib` read) for hand-editing; KConfig `.ini` optional later. Confirm during impl.
- [x] **Packaging/deploy target?** ✅ **Decided: local venv + autostart** (`.desktop` autostart entry or user systemd unit). Full read access to `~/.claude/.credentials.json`, no sandbox. Flatpak deferred (would need `--filesystem=~/.claude:ro`). See [[Technology-Stack#Packaging & distribution]].

## Scope (v1 defaults — non-blocking)

- [x] Graphical **Settings UI** in v1? ✅ **No** — config file is the interface for v1; tray menu "Settings…" opens the file. GUI later.
- [x] **Multi-account** support? ✅ **Out of scope** — single linked Claude account (the one Claude Code is logged into).
- [x] **Alert state persistence** across restarts? ✅ v1 default: **in-memory** (`lastNotified` resets on restart; worst case is one duplicate warning after a relaunch). Revisit if annoying.

## Resolution log

> Record decisions here as they're made, with date and rationale, so the rest of the docs can be updated.

| Date | Question | Decision | Rationale |
|---|---|---|---|
| 2026-06-30 | Where does usage data come from? | OAuth usage endpoint (`/api/oauth/usage`) via `oauth-http` provider | Same source proven by `m13v/claude-meter`; identical numbers to the Settings page |
| 2026-06-30 | How do we authenticate? | Read Claude Code's stored Bearer token (`~/.claude/.credentials.json`), read-only | Avoids implementing our own OAuth login/refresh; Claude Code owns the lifecycle |
| 2026-06-30 | Language / framework? | **Python + PySide6** | PySide6 6.11.1 already installed; Plasma 6.6.5/Qt6 host; no C++ toolchain present — fastest path to a working tray app |
| 2026-06-30 | Deploy / packaging? | **Local venv + autostart** (`.desktop`/user systemd) | Personal single-user tool; needs unsandboxed read of `~/.claude/.credentials.json`; Flatpak deferred |
| 2026-06-30 | v1 scope | No GUI settings, single account, in-memory alert state | Keep v1 small; config file + tray menu suffice |
| 2026-06-30 | `utilization` / `percent` scale | Both are **0–100** (percent), used directly | Live capture `utilization=3.0`/`percent=3`; a session can't be 300%, so 3.0 = 3%. Fixed a `×100` bug that showed 300% |
