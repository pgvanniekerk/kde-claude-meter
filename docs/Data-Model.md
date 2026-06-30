# Data Model

The core runtime data structures. These are conceptual (language-agnostic) — the [[Technology-Stack|implementation]] will likely render them as C++/Qt types. See how they connect in [[Architecture]].

## Class diagram

```plantuml
@startuml
skinparam shadowing false

class UsageModel {
  + windows : map<string, WindowUsage>
  + lastUpdated : datetime
  + authState : AuthState
  + worstWindow() : WindowUsage
  + onReadings(UsageReading[]) : void
}

class WindowUsage {
  + windowId : string      ' "5h" | "weekly" | "weekly:sonnet" | "weekly:opus" | ...
  + displayName : string
  + group : string         ' "session" | "weekly"
  + kind : string          ' session | weekly_all | weekly_scoped
  + scopeModel : string?   ' "Sonnet" | "Opus" | null (for scoped windows)
  + percent : number       ' utilization * 100 (0..100+)
  + used : number?         ' usually null - endpoint reports no count
  + limit : number?        ' usually null
  + unit : string          ' "percent" (native unit)
  + resetsAt : datetime?   ' may be null when window inactive
  + isActive : bool        ' from limits[].is_active
  + ok : bool              ' false => stale/unknown
}

class UsageReading {
  + windowId : string
  + used : number
  + limit : number
  + unit : string
  + windowResetsAt : datetime
  + fetchedAt : datetime
  + ok : bool
}

class AlertState {
  + lastNotified : map<string,int>  ' windowId -> highest fired threshold
  + paused : bool
  + pausedUntil : datetime?
  + evaluate(UsageModel, Config) : AlertEvent[]
  + onWindowReset(windowId) : void
}

class AlertEvent {
  + windowId : string
  + threshold : int
  + percent : number
  + urgency : string
}

enum AuthState {
  Authenticated
  Unauthenticated
  Unknown
}

UsageReading ..> WindowUsage : normalised into
UsageModel "1" o-- "many" WindowUsage
AlertState ..> UsageModel : reads
AlertState ..> AlertEvent : produces
UsageModel --> AuthState
@enduml
```

## Notes on key fields

- **`percent` comes straight from the endpoint's `utilization`** (which is already a 0–100 percent, used as-is — *not* multiplied by 100); the endpoint does **not** report raw used/limit counts, so `used`/`limit` are usually `null` and percentage is the native unit. See the field mapping in [[API-Reference-Usage-Endpoint]]. Percentage is the common currency for thresholds (see [[Usage-Limits-and-Windows]]).
- **`ok` / `AuthState`** let the [[System-Tray]] show *stale* and *unauthenticated* states distinctly from low usage.
- **`AlertState.lastNotified`** is the rising-edge memory described in [[Notifications-and-Alerts]]. It is **keyed per window id**, so per-model windows (`weekly:opus`, `weekly:sonnet`) alert and reset independently of each other and of the global windows.
- **`group` / `kind` / `scopeModel`** drive both display naming and config threshold resolution (per-window → per-group → global). See [[Usage-Limits-and-Windows#Window id & display naming]] and [[Configuration-Reference#Per-window and per-group thresholds]].
- Windows are **discovered from the response**, not a fixed enum — the model rebuilds its window map each poll, adding/removing entries as buckets appear or go inactive.
- **`pausedUntil`** backs the tray "Pause alerts" feature (see [[System-Tray]]).

## What gets persisted vs. in-memory

| Data | Lifetime |
|---|---|
| `UsageModel`, `WindowUsage` | in-memory (rebuilt each poll) |
| `AlertState.lastNotified` | in-memory; reset on window rollover. (Optionally persisted across restarts to avoid re-warning — TBD in [[Open-Questions]].) |
| Config | persisted (KConfig) — see [[Configuration-Reference]] |
| Account token | **not stored by us** — read read-only from Claude Code's `~/.claude/.credentials.json` at poll time. See [[Usage-Data-Provider#Token handling rules]] |
