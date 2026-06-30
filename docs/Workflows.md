# Workflows

End-to-end sequences for the main scenarios, tying together the [[Components]].

## 1. Startup

```plantuml
@startuml
skinparam shadowing false
actor User
participant "App (main)" as App
participant "Config" as Cfg
participant "Tray Controller" as Tray
participant "Poller" as Poll
participant "Usage Data Provider" as Prov

User -> App : login session / launch
App -> Cfg : load config (or defaults)
App -> Tray : create tray icon (state: Unknown)
App -> Poll : start(interval)
Poll -> Prov : isAuthenticated()?
alt not authenticated
  Prov --> Poll : false
  Poll -> Tray : state = Unauthenticated
else authenticated
  Poll -> Prov : fetchUsage(windows)
  Prov --> Poll : readings
  Poll -> Tray : state = OK/Warning/...
end
@enduml
```

## 2. Normal poll cycle (threshold crossed)

```plantuml
@startuml
skinparam shadowing false
participant "Poller" as Poll
participant "Usage Data Provider" as Prov
participant "Usage Model" as Model
participant "Alert Engine" as Alert
participant "Notification Service" as Notif
participant "Tray Controller" as Tray
node "KNotifications" as KN

Poll -> Prov : fetchUsage(["5h","weekly"])
Prov --> Poll : readings
Poll -> Model : onReadings(readings)
Model -> Model : compute percent, worstWindow
Model -> Alert : usage changed
Alert -> Alert : crossed = thresholds newly exceeded
opt crossed not empty
  Alert -> Notif : fire(window, threshold, percent, urgency)
  Notif -> KN : show popup
end
Model -> Tray : refresh icon + tooltip
@enduml
```

## 3. Window rollover (alert memory reset)

```plantuml
@startuml
skinparam shadowing false
participant "Poller" as Poll
participant "Usage Model" as Model
participant "Alert Engine" as Alert

Poll -> Model : onReadings (now > resetsAt for 5h)
Model -> Alert : usage changed
Alert -> Alert : now > windowResetsAt["5h"]?
Alert -> Alert : lastNotified["5h"] = 0
note right : next time 5h crosses 70%,\nit will warn again
@enduml
```

See the rule in [[Notifications-and-Alerts#Core rule: notify on rising-edge crossings only]].

## 4. User pauses alerts

```plantuml
@startuml
skinparam shadowing false
actor User
participant "Tray Controller" as Tray
participant "Alert Engine" as Alert

User -> Tray : menu → Pause alerts → 1h
Tray -> Alert : paused = true, pausedUntil = now+1h
note right of Alert
  Icon still shows real usage.
  Notifications suppressed until
  pausedUntil passes.
end note
Alert -> Alert : on each evaluate, if now > pausedUntil → resume
@enduml
```

## 5. Fetch failure (stale state)

```plantuml
@startuml
skinparam shadowing false
participant "Poller" as Poll
participant "Usage Data Provider" as Prov
participant "Tray Controller" as Tray

Poll -> Prov : fetchUsage(...)
Prov --> Poll : error / ok=false
Poll -> Tray : state = Stale (grey icon)
Poll -> Poll : apply backoff, retry later
note right of Poll : no false "0%" shown;\nlast good values kept in tooltip
@enduml
```

Related: [[System-Tray]], [[Data-Model]].
