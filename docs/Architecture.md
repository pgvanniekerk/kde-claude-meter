# Architecture

This note describes the overall structure of [[Overview|Claude Meter]]. The design favours a small number of clearly-separated components so the **source of usage data** can change later without touching the rest of the app.

## Architectural principles

1. **Single responsibility components.** Polling, modelling, alerting, and presentation are separate.
2. **Pluggable data source.** The [[Usage-Data-Provider]] sits behind an interface so it can be swapped (e.g. local-file reader vs. HTTP API) — see [[Open-Questions]].
3. **State-driven UI.** The tray icon and notifications are derived from a single in-memory [[Data-Model|Usage Model]]; there is one source of truth.
4. **Stateless alerts, persisted edges.** The Alert Engine only fires on a *newly crossed* threshold, so we persist which thresholds were already notified per window (see [[Notifications-and-Alerts]]).
5. **Config first.** Behaviour is data-driven from [[Configuration-Reference|config]]; sane defaults ship out of the box.

## Component diagram

```plantuml
@startuml
skinparam shadowing false
skinparam componentStyle rectangle

package "Claude Meter" {

  component "Usage Data Provider" as Provider <<interface>>
  note bottom of Provider
    Pluggable. Knows how to read
    raw usage for each limit window.
    See [[Usage-Data-Provider]].
  end note

  component "Poller / Scheduler" as Poller
  component "Usage Model\n(in-memory state)" as Model
  component "Alert Engine" as Alerts
  component "Notification Service" as Notif
  component "Tray Controller\n(KStatusNotifierItem)" as Tray
  component "Settings / Config\n(KConfig)" as Config
  component "Settings UI\n(optional)" as UI
}

cloud "Usage Source" as Source
node "KNotifications /\nPlasma popups" as Plasma

Poller --> Provider : poll(interval)
Provider --> Source : read raw usage
Provider --> Model : normalised usage
Model --> Alerts : usage changed
Alerts --> Notif : fire(threshold, window)
Notif --> Plasma : show popup
Model --> Tray : update icon + tooltip
Config --> Poller : interval
Config --> Alerts : thresholds, windows
Config --> Tray : display prefs
UI --> Config : edit settings
Tray --> UI : "Settings…" menu item

@enduml
```

## Runtime shape

Claude Meter is a single long-running process started at login (autostart `.desktop` entry). Internally it is event-driven on the Qt event loop:

- A **timer** drives the Poller at the configured interval.
- Polling and any network/file I/O happen **off the UI thread** (or async) so the tray stays responsive.
- Results flow into the Usage Model, which emits change signals consumed by the Alert Engine and Tray Controller.

```plantuml
@startuml
skinparam shadowing false
state "Idle (waiting on timer)" as Idle
state "Polling" as Polling
state "Updating model" as Update
state "Evaluating alerts" as Eval
state "Refreshing tray" as TrayUp

[*] --> Idle
Idle --> Polling : timer tick
Polling --> Update : data received
Polling --> Idle : fetch failed (log + backoff)
Update --> Eval
Eval --> TrayUp
TrayUp --> Idle
@enduml
```

## Where to read next

- The responsibility of each box: [[Components]]
- The data that flows between them: [[Data-Model]]
- The end-to-end flows: [[Workflows]]
