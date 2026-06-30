# Configuration Reference

The full set of configuration keys for Claude Meter. This is a **proposed** schema for the planning phase — see [[Alert-Configuration]] for the conceptual guide and [[Open-Questions]] for unresolved choices (e.g. file format).

> [!note] Format
> Examples below use TOML for readability. The real app will likely use **KConfig** (`.ini`-style groups) for native Plasma integration — see [[Technology-Stack]]. The keys/semantics stay the same regardless of serialization.

## Top-level keys

| Key | Type | Default | Description |
|---|---|---|---|
| `pollIntervalSeconds` | int | `60` | How often to poll the [[Usage-Data-Provider]]. Minimum `15`. |
| `thresholds` | int[] | `[70, 80, 90, 100]` | Global warning percentages. The default for any window with no group/window override. |
| `windows.mode` | enum | `"auto"` | `auto` = track every window the [[API-Reference-Usage-Endpoint\|endpoint]] returns (incl. per-model). `manual` = only the ids in `windows.include`. See [[Usage-Limits-and-Windows]]. |
| `windows.include` | string[] | `[]` | When `mode = manual`, the explicit window ids to track (e.g. `["5h","weekly","weekly:opus"]`). |
| `windows.includeInactive` | bool | `false` | If false, hide scoped windows that are `is_active: false` (e.g. a model you haven't used yet) until they activate. |
| `reArmOnDecrease` | bool | `false` | If true, lower `lastNotified` when usage falls (re-warns on re-cross). See [[Notifications-and-Alerts]]. |
| `startMinimized` | bool | `true` | Start to tray with no window. |
| `autostart` | bool | `true` | Install a login autostart entry. |

## Per-window and per-group thresholds

Thresholds can be set at three levels. For each window, the app resolves them **most-specific-first**:

1. `thresholds.per_window.<windowId>` — exact match (e.g. `"weekly:opus"`)
2. `thresholds.per_group.<group>` — the window's group (`session` or `weekly`)
3. `thresholds` — the global default

```toml
# global default
thresholds = [70, 80, 90, 100]

[thresholds.per_group]
session = [70, 80, 90, 100]
weekly  = [70, 85, 95, 100]

[thresholds.per_window]
"weekly:opus"   = [50, 75, 90, 100]   # I burn through Opus fast — warn me earlier
"weekly:sonnet" = [80, 95, 100]
```

| Key | Type | Description |
|---|---|---|
| `thresholds.per_group.<group>` | int[] | Overrides the global `thresholds` for every window in that group (`session` / `weekly`). |
| `thresholds.per_window.<windowId>` | int[] | Overrides everything for one window — including per-model windows like `weekly:opus`. |

Because windows are discovered dynamically, you can pre-configure thresholds for a `weekly:<model>` window **before** it ever activates; the override applies the moment that model's bucket appears. Each window also alerts independently — see [[Notifications-and-Alerts#Per-window independence]].

## Urgency mapping

```toml
[urgency]
70  = "normal"
80  = "normal"
90  = "high"
100 = "critical"
```

| Value | Meaning |
|---|---|
| `low` | minimal, may be coalesced |
| `normal` | standard popup |
| `high` | prominent, longer-lived |
| `critical` | persistent until dismissed |

See the mapping rationale in [[Notifications-and-Alerts#Threshold → urgency mapping]].

## Quiet hours

```toml
[quiet_hours]
from = "23:00"
to   = "07:00"
```

| Key | Type | Description |
|---|---|---|
| `quiet_hours.from` / `quiet_hours.to` | "HH:MM" | Suppress popups during this daily window. `100%`/critical may still break through (`quiet_hours.allowCritical = true`). |

## Tray "pause" presets

```toml
pauseDurationsMinutes = [15, 60, 240]   # plus an implicit "until next reset"
```

## Notification appearance

| Key | Type | Default | Description |
|---|---|---|---|
| `notify.showResetTime` | bool | `true` | Include the window reset time in the body. |
| `notify.showPercent` | bool | `true` | Include the exact percentage. |
| `notify.actionsEnabled` | bool | `true` | Show inline actions (Open usage / Pause). |

## Data source (provider) settings

```toml
[provider]
kind = "oauth-http"   # "oauth-http" (default) | "mock" | "cookie-http"  — see [[Usage-Data-Provider]]

[provider.oauth_http]
usageUrl      = "https://api.anthropic.com/api/oauth/usage"
profileUrl    = "https://api.anthropic.com/api/oauth/profile"
credentialsPath = "~/.claude/.credentials.json"   # Linux; falls back to system keyring if absent
```

| Key | Type | Description |
|---|---|---|
| `provider.kind` | enum | Which [[Usage-Data-Provider]] implementation to use. Default `oauth-http`. |
| `provider.oauth_http.usageUrl` | string | The usage endpoint (overridable if it moves). |
| `provider.oauth_http.profileUrl` | string | The profile endpoint (account email / org). |
| `provider.oauth_http.credentialsPath` | string | Where to read Claude Code's stored Bearer token. **Read-only.** |
| `provider.*` | varies | Implementation-specific options. **No secrets here** — the token is read from Claude Code's store, never copied into this config. See [[Usage-Data-Provider#Token handling rules]]. |

## Full example

```toml
pollIntervalSeconds = 60
thresholds = [70, 80, 90, 100]
reArmOnDecrease = false
startMinimized = true
autostart = true
pauseDurationsMinutes = [15, 60, 240]

[windows]
mode = "auto"             # track every window the API returns, including per-model
includeInactive = false

[thresholds.per_group]
weekly = [70, 85, 95, 100]

[thresholds.per_window]
"weekly:opus" = [50, 75, 90, 100]   # warn earlier on Opus

[urgency]
90  = "high"
100 = "critical"

[quiet_hours]
from = "23:00"
to   = "07:00"
allowCritical = true

[provider]
kind = "oauth-http"
```

## Validation

See [[Alert-Configuration#Validation rules]]. Invalid values fall back to the defaults in this table and raise a one-time warning notification.
