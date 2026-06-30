# Usage Limits and Windows

Claude Meter tracks usage against more than one limit at the same time. Each limit is a **window**: a span of time with its own allowance and its own reset point.

## Windows are discovered dynamically

Rather than hardcoding a fixed list, Claude Meter **discovers windows from each [[API-Reference-Usage-Endpoint|usage response]]**. Every non-null bucket the endpoint returns becomes a window. This means new model-scoped limits (e.g. an Opus weekly bucket that activates only once you use Opus) appear automatically without a code or config change.

| Window | Id | `kind` / scope | Model granularity |
|---|---|---|---|
| 5-hour rolling | `5h` | `session` | **Global** — combined across all models (API does not split the 5h limit per model) |
| Weekly (all models) | `weekly` | `weekly_all` | Combined across all models |
| Weekly · Sonnet | `weekly:sonnet` | `weekly_scoped`, `scope.model = Sonnet` | **Per-model** |
| Weekly · Opus | `weekly:opus` | `weekly_scoped`, `scope.model = Opus` | **Per-model** (appears when present) |
| *(other scoped buckets)* | `weekly:<model>` | `weekly_scoped` | Per-model, as the endpoint exposes them |

> [!warning] What per-model tracking can and cannot do
> The app can show, threshold, and alert on **every window the endpoint reports** — including each model-scoped weekly bucket — because each is treated independently (see [[Notifications-and-Alerts]]).
> It **cannot** invent granularity the API doesn't provide: there is **no per-model 5-hour usage**, and the all-models `weekly` bucket cannot be decomposed into per-model slices. "All available models" therefore means *all model-scoped buckets the endpoint surfaces*, which today is Sonnet (and Opus when active). Tracked in [[Open-Questions]].

> [!note]
> The exact reset semantics (true rolling vs. fixed-boundary) depend on what the [[Usage-Data-Provider]] reports. The model stores a concrete `windowResetsAt` timestamp per window and treats it as authoritative, so it works either way. A scoped window may report `resets_at: null` and `is_active: false` until you actually use that model.

## Window id & display naming

| Source `kind` | `scope.model` | Window id | Display name |
|---|---|---|---|
| `session` | — | `5h` | "5-hour" |
| `weekly_all` | — | `weekly` | "Weekly (all models)" |
| `weekly_scoped` | `Sonnet` | `weekly:sonnet` | "Weekly · Sonnet" |
| `weekly_scoped` | `Opus` | `weekly:opus` | "Weekly · Opus" |

The `group` (`session` / `weekly`) is preserved so config can set defaults per group — see [[Configuration-Reference#Per-window and per-group thresholds]].

## Why track several at once

A user can be comfortably under the weekly limit but about to exhaust the 5-hour limit, or be fine on the combined weekly while close to the **Sonnet-** or **Opus-scoped** weekly cap. The [[System-Tray|tray icon]] reflects the **most urgent** window across all of them, while notifications and the tooltip identify **which** window (and which model) triggered.

```plantuml
@startuml
skinparam shadowing false
concise "5h window %" as FiveH
concise "Weekly window %" as Week

@FiveH
0 is "55%"
+30 is "72%" #orange
+20 is "absolute reset"
@FiveH
0 <-> +30 : within 5h window

@Week
0 is "40%"
+30 is "41%"
+20 is "43%"
@enduml
```

## Percentage is the common currency

The usage endpoint reports each window as a **`utilization` value already in percent (0–100 float)** with no raw token/message counts (see [[API-Reference-Usage-Endpoint]]). So percentage isn't just convenient — it's the only native unit:

```
percentUsed = utilization      # already 0–100, e.g. 3.0 = 3%
```

Thresholds in [[Alert-Configuration]] are expressed as percentages so they apply uniformly to every window.

> [!note] Three windows are available
> The endpoint exposes `five_hour` → **`5h`**, `seven_day` → **`weekly`** (all-models), and `seven_day_sonnet` → an optional **`weekly_sonnet`** window. Whether to surface the Sonnet-scoped weekly limit (and the `extra_usage` overage block) is a display choice tracked in [[Open-Questions]].

## Window lifecycle and alert reset

When a window's `windowResetsAt` passes:

1. The [[Data-Model|Usage Model]] expects `used` to drop on the next poll.
2. The [[Notifications-and-Alerts|Alert Engine]] **clears the fired-threshold memory** for that window, so crossing 70% again in the new window will notify again.

See the edge/reset logic in [[Notifications-and-Alerts]].
