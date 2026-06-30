# API Reference — Usage Endpoint

Captured from a **live response** on 2026-06-30 (HTTP 200). This pins down the JSON shape that [[Usage-Data-Provider]]'s `oauth-http` implementation must parse and the [[Data-Model|Usage Model]] mapping. These endpoints are **undocumented** — treat this as observed behaviour, not a contract.

## `GET https://api.anthropic.com/api/oauth/usage`

Headers: `Authorization: Bearer <token>`, `Content-Type: application/json`.

### Sample response (real, no secrets/PII — only numbers & flags)

```json
{
  "five_hour":  { "utilization": 1.0, "resets_at": "2026-06-30T17:20:00.261810+00:00",
                  "limit_dollars": null, "used_dollars": null, "remaining_dollars": null },
  "seven_day":  { "utilization": 0.0, "resets_at": "2026-06-30T13:00:00.261832+00:00",
                  "limit_dollars": null, "used_dollars": null, "remaining_dollars": null },
  "seven_day_oauth_apps": null,
  "seven_day_opus": null,
  "seven_day_sonnet": { "utilization": 0.0, "resets_at": null,
                        "limit_dollars": null, "used_dollars": null, "remaining_dollars": null },
  "seven_day_cowork": null, "seven_day_omelette": null,
  "tangelo": null, "iguana_necktie": null, "omelette_promotional": null,
  "cinder_cove": null, "amber_ladder": null,
  "extra_usage": { "is_enabled": false, "monthly_limit": null, "used_credits": null,
                   "utilization": null, "currency": null, "decimal_places": null,
                   "disabled_reason": null, "daily": null, "weekly": null },
  "limits": [
    { "kind": "session",       "group": "session", "percent": 1, "severity": "normal",
      "resets_at": "2026-06-30T17:20:00.261810+00:00", "scope": null, "is_active": true },
    { "kind": "weekly_all",    "group": "weekly",  "percent": 0, "severity": "normal",
      "resets_at": "2026-06-30T13:00:00.261832+00:00", "scope": null, "is_active": false },
    { "kind": "weekly_scoped", "group": "weekly",  "percent": 0, "severity": "normal",
      "resets_at": null, "scope": { "model": { "id": null, "display_name": "Sonnet" }, "surface": null },
      "is_active": false }
  ],
  "spend": { "used": { "amount_minor": 0, "currency": "USD", "exponent": 2 },
             "limit": null, "percent": 0, "severity": "normal", "enabled": false,
             "disabled_reason": null, "cap": null, "balance": null, "auto_reload": null,
             "can_purchase_credits": false, "can_toggle": false },
  "member_dashboard_available": false
}
```

### The two views of the same data

The payload exposes usage **twice** — pick one to consume:

1. **Typed objects** (`five_hour`, `seven_day`, `seven_day_sonnet`, …) — each has `utilization` + `resets_at`.
2. **Unified `limits[]` array** — one entry per active/known limit with `kind`, `group`, `severity`, `resets_at`, `is_active`.

> [!tip] Recommendation
> Consume the **typed objects** for the numbers (`utilization` is the precise float) and use **`limits[]`** only for `is_active` / `severity` metadata.

> [!important] Units — `utilization` is already a percentage (0–100), NOT a 0–1 fraction
> Confirmed by a second live capture (2026-06-30): `five_hour.utilization = 3.0` with `limits[].percent = 3`. A session limit cannot be at 300%, so `3.0` means **3%**. So `utilization` is a 0–100 **float percentage**, and `limits[].percent` is the same value as an **integer** — they agree.
> **Use `percent = utilization` directly (do NOT multiply by 100).** The earlier `1.0`/`1` snapshot was 1% usage, not 100% — easy to misread when the only data points are 0 and 1.

### Field reference

| Field | Type | Meaning / mapping |
|---|---|---|
| `five_hour.utilization` | float `0–100` | **Percent** of the **5-hour** limit used (already 0–100, e.g. `3.0` = 3%). → our `5h` window. |
| `five_hour.resets_at` | ISO-8601 datetime (tz-aware) | When the 5-hour window resets → `windowResetsAt`. |
| `seven_day.utilization` / `.resets_at` | float `0–100` / datetime | The **weekly (all-models)** limit, as a percent. → our `weekly` window. |
| `seven_day_sonnet` | object \| null | Weekly limit **scoped to Sonnet**. Optional second weekly window. `resets_at` may be `null` when inactive. |
| `seven_day_opus`, `seven_day_oauth_apps`, `seven_day_cowork`, `seven_day_omelette` | object \| null | Other model/surface-scoped weekly buckets. Usually `null`; render only if populated. |
| `tangelo`, `iguana_necktie`, `omelette_promotional`, `cinder_cove`, `amber_ladder` | null (codenames) | Internal/experimental buckets. **Ignore** unless they appear populated. |
| `*.limit_dollars` / `used_dollars` / `remaining_dollars` | null for plan windows | Only meaningful for paid credits, **not** the plan limits. Confirms usage has **no token/message count** — percentage is the only native unit. |
| `extra_usage` | object | Overage/credits block. `is_enabled=false` here. Optional third indicator (see [[Usage-Limits-and-Windows]]). |
| `limits[].kind` | enum | `session` (=5h), `weekly_all`, `weekly_scoped`. |
| `limits[].group` | enum | `session` \| `weekly`. |
| `limits[].percent` | int `0–100` | Integer percent; equals `round(utilization)`. Either field works; we use `utilization` for precision. |
| `limits[].severity` | enum | Observed `normal`. Other values (e.g. `warning`/`critical`?) unconfirmed. We compute our **own** thresholds — don't depend on this. |
| `limits[].resets_at` | datetime \| null | Reset time for that limit. |
| `limits[].scope.model.display_name` | string | e.g. `"Sonnet"` for the scoped weekly limit. |
| `limits[].is_active` | bool | Whether the limit currently applies. |
| `spend` | object | Credit-spend summary (currency, balance). Not a usage window. |

> [!note] Sample values above are small percentages
> In the sample payload, `utilization: 1.0` = **1%** and `0.0` = 0% — both well under the limits. Do not read `1.0` as "100%". A fully-consumed window would show `utilization: 100.0` / `percent: 100`.

## `GET https://api.anthropic.com/api/oauth/profile`

Used for "linked account" identity and to confirm Max entitlement. Structure (values redacted):

```
account.uuid / full_name / display_name / email : str
account.has_claude_max : bool          # confirm Max plan
account.has_claude_pro : bool
account.created_at : str
organization.uuid / name / organization_type / billing_type : str
organization.rate_limit_tier : str
organization.has_extra_usage_enabled : bool
organization.subscription_status / subscription_created_at : str
application.uuid / name / slug : str
enabled_plugins : list
```

We need almost none of this — `account.email` (display) and `account.has_claude_max` (sanity check) are the only useful fields. **Do not log** email/uuids.

## Token store (`~/.claude/.credentials.json`)

Structure (values redacted) — read **read-only**, see [[Usage-Data-Provider#Token handling rules]]:

```
claudeAiOauth.accessToken : str      # Bearer token for the calls above
claudeAiOauth.refreshToken : str     # we never use/rotate this — Claude Code does
claudeAiOauth.expiresAt : int        # epoch ms; if past, attempt anyway then handle 401
claudeAiOauth.scopes : list[5]
claudeAiOauth.subscriptionType : str # e.g. "max"
claudeAiOauth.rateLimitTier : str
```

## Resulting mapping into our model

| Our window | Source | Percent |
|---|---|---|
| `5h` | `five_hour` | `utilization` (already a percent) |
| `weekly` | `seven_day` | `utilization` |
| `weekly_sonnet` *(optional)* | `seven_day_sonnet` | `utilization` |

`resets_at` → `WindowReading.windowResetsAt`. `used`/`limit` are **unavailable** (null) → store `null` and present percentage only. See [[Data-Model]].
