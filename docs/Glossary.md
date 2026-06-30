# Glossary

Terms used across the Claude Meter notes.

| Term | Meaning |
|---|---|
| **Window** | A usage limit period with its own allowance and reset point. We track `5h` (5-hour) and `weekly`. See [[Usage-Limits-and-Windows]]. |
| **Threshold** | A percentage (e.g. 70) that, when crossed upward, triggers a warning. See [[Alert-Configuration]]. |
| **Rising-edge** | Firing an alert only when usage first crosses a threshold going up, not on every poll. See [[Notifications-and-Alerts]]. |
| **`lastNotified`** | Per-window memory of the highest threshold already alerted in the current window period. See [[Data-Model]]. |
| **Worst window** | The window with the highest current percentage; drives the [[System-Tray|tray icon]] state. |
| **Provider / Usage Data Provider** | The pluggable component that fetches raw usage from the underlying source. See [[Usage-Data-Provider]]. |
| **Reading** | A single raw usage measurement for one window from the provider, normalised into the model. See [[Data-Model]]. |
| **Stale** | State where the last fetch failed; usage shown is last-known, not current. See [[System-Tray]]. |
| **Poll** | One scheduled cycle of fetching usage and re-evaluating alerts. See [[Workflows]]. |
| **KStatusNotifierItem** | KDE/Plasma system tray item API. See [[Technology-Stack]]. |
| **KNotifications** | KDE framework for desktop notification popups. |
| **KConfig** | KDE framework for reading/writing app configuration. |
| **KWallet** | KDE secure secret storage (for the account token). |
| **Max plan** | The Claude subscription tier this app is built for, with 5-hour and weekly limits. |
