# Components

Detailed responsibilities for each box in the [[Architecture]] diagram.

## Usage Data Provider

The boundary between Claude Meter and wherever the usage numbers actually come from. It exposes one conceptual operation: *"give me the current usage for every limit window I care about."*

- **Input:** which windows to query (5-hour, weekly).
- **Output:** a list of raw usage readings → normalised into the [[Data-Model|Usage Model]].
- **Pluggable:** concrete implementations are an open decision — see [[Usage-Data-Provider]] and [[Open-Questions]].
- **Failure handling:** must report fetch failures distinctly from "0% used" so the UI can show a *stale/unknown* state rather than a misleading green.

## Poller / Scheduler

Drives the refresh loop.

- Fires the provider on the configured `pollIntervalSeconds`.
- Applies **backoff** on repeated failures so we don't hammer a failing source.
- Can be triggered **manually** via the tray menu ("Refresh now").
- Never blocks the UI thread.

## Usage Model (in-memory state)

The single source of truth at runtime. Holds, per window: amount used, the limit, the derived percentage, and the window reset time. Emits a "changed" signal when new data arrives. See [[Data-Model]] for fields.

## Alert Engine

Decides **when** to notify.

- Compares each window's percentage against the sorted threshold list (default 70/80/90/100).
- Fires only on a **newly crossed** threshold (rising edge) to avoid spam — see the edge logic in [[Notifications-and-Alerts]].
- **Resets** a window's fired-threshold memory when that window rolls over (its reset time passes), so the next cycle can warn again.

## Notification Service

Thin wrapper over KDE notifications.

- Renders a popup with severity, window name, current %, and reset time.
- Maps threshold → urgency (e.g. 100% = critical).
- Is the only component that talks to KNotifications, so the popup mechanism can be tested/replaced in isolation.

## Tray Controller

Owns the `KStatusNotifierItem`.

- Reflects the **worst-case** window (highest %) in the icon colour/state.
- Provides a **tooltip / menu** breaking down each window.
- Hosts actions: *Refresh now*, *Settings…*, *Pause alerts*, *Quit*.
- See [[System-Tray]] for the state machine.

## Settings / Config

Loads and persists user preferences via KConfig.

- Supplies thresholds, windows, interval, and display prefs to the other components.
- Watches the config file so edits apply without a restart (nice-to-have).
- Schema documented in [[Configuration-Reference]].

## Settings UI (optional, later)

A small dialog to edit the config without hand-editing the file. Not required for v1 — the [[Configuration-Reference|config file]] is the primary interface initially.

## Responsibility matrix

| Component | Knows about Claude source? | Touches KDE UI? | Holds state? |
|---|---|---|---|
| Usage Data Provider | ✅ | ❌ | ❌ |
| Poller | ❌ | ❌ | timer only |
| Usage Model | ❌ | ❌ | ✅ |
| Alert Engine | ❌ | ❌ | fired-edges |
| Notification Service | ❌ | ✅ | ❌ |
| Tray Controller | ❌ | ✅ | ❌ |
| Config | ❌ | ❌ | ✅ (persisted) |
