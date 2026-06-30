# Claude Meter

A native **KDE/Plasma system-tray** app that shows your current **Claude Max plan** usage and pops up desktop warnings as you approach your limits — across the rolling **5-hour** window, the **weekly** window, and any **per-model** weekly windows (e.g. Sonnet, Opus). Alerts fire at configurable thresholds (default **70 / 80 / 90 / 100%**), once per crossing.

The tray icon reflects your **most-used** window at a glance; hover it for a per-window breakdown.

> Planning notes and architecture live in [`docs/`](docs/) (an Obsidian vault with PlantUML diagrams — start at [`docs/Overview.md`](docs/Overview.md)).

---

## How it works

Claude Meter reads the OAuth token that **Claude Code** already stores on your machine (read-only) and calls Anthropic's usage endpoint — the same data shown at `claude.ai/settings/usage`. It does **not** log you in, refresh tokens, or store any credentials of its own; Claude Code owns the token lifecycle.

This means:

- ✅ **You must have [Claude Code](https://claude.com/claude-code) installed and logged in** (run `claude` once). That's where the token comes from.
- ⚠️ The usage endpoint is **undocumented** and may change without notice. If it breaks, the tray shows a *stale* state rather than crashing.

---

## Requirements

- **KDE Plasma** (or any desktop with a system-tray / StatusNotifier host)
- **Claude Code**, logged in to your Claude (Max/Pro) account
- **Python 3.11+**
- **PySide6** — specifically the `QtCore`, `QtGui`, and `QtWidgets` modules

> On Debian/Ubuntu/KDE Neon, PySide6 is split into per-module packages, so installing "PySide6" alone is not enough — see below.

---

## Installation

### 1. Install the system dependencies (PySide6)

**Debian / Ubuntu / KDE Neon:**
```bash
sudo apt install python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtwidgets
```

**Arch / Manjaro:**
```bash
sudo pacman -S pyside6
```

**Fedora:**
```bash
sudo dnf install python3-pyside6
```

**Any distro (via pip, if system packages aren't available):** create a normal venv and `pip install PySide6` — then skip the `--system-site-packages` behaviour of the installer and point it at that venv.

### 2. Clone the repository

```bash
git clone https://github.com/pgvanniekerk/kde-claude-meter.git
cd kde-claude-meter
```

### 3. Run the installer

```bash
./scripts/install.sh
```

This:
- creates a local virtualenv at `./.venv` that **reuses your system PySide6** (no large download),
- generates a launcher at `./.venv/bin/claude-meter`,
- writes a KDE/XDG **autostart** entry to `~/.config/autostart/claude-meter.desktop`.

> If venv creation fails with an `ensurepip`/`python3-venv` error, the installer already uses `--without-pip` to avoid it. If you still hit it on your distro, install your `python3-venv` package and re-run.

### 4. Start it

```bash
./.venv/bin/claude-meter
```

The Claude icon appears in your system tray. If you don't see it, expand the panel's tray-overflow arrow, or set it to *Shown* in **System Settings → Quick Settings / System Tray → Entries**.

---

## Autostart at login

The installer already registers autostart, so Claude Meter launches automatically the next time you log in.

- **Manage it:** System Settings → **Autostart** → *Claude Meter*. You can "Run Now" to test it without logging out.
- **Disable it:** toggle it off there, or delete `~/.config/autostart/claude-meter.desktop`.
- **Note:** the autostart entry points at this repo's `./.venv` and `src/`. If you **move or rename the project folder**, re-run `./scripts/install.sh` to update the paths.

---

## Configuration

A default config is written on first run to:

```
~/.config/claude-meter/config.toml
```

(or `$XDG_CONFIG_HOME/claude-meter/config.toml`). Use the tray menu's **Open config…** to edit it. Key options:

```toml
pollIntervalSeconds = 60        # how often to check usage (minimum 15)

[windows]
mode = "auto"                   # track every window the API returns, incl. per-model
includeInactive = false         # also show dormant per-model windows (0%, no reset)

[thresholds]
default = [70, 80, 90, 100]     # warning percentages, applied per window

[thresholds.per_group]          # optional: override by group ("session" = 5h, "weekly")
# weekly = [70, 85, 95, 100]

[thresholds.per_window]         # optional: override a specific window, incl. per-model
# "weekly:opus" = [50, 75, 90, 100]

[urgency]                       # threshold% -> "normal" | "high" | "critical"
90 = "high"
100 = "critical"
```

Full reference: [`docs/Configuration-Reference.md`](docs/Configuration-Reference.md).

---

## Tray menu

- **Refresh now** — poll immediately.
- **Pause alerts** — suppress notifications for 15 min / 1 hour (icon still shows real usage).
- **Open config…** — open the config file.
- **Quit** — exit (autostart still relaunches at next login).

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Tray icon greyed / "Not logged in" | Run `claude` to log in to Claude Code, then **Refresh now**. |
| `ModuleNotFoundError: No module named 'PySide6.QtGui'` | Install the per-module PySide6 packages (see step 1). |
| `ensurepip is not available` during install | Install `python3-venv` for your Python version, or rely on the installer's `--without-pip`. |
| No tray icon at all | Ensure your desktop has a system-tray widget; on minimal setups a StatusNotifier host may be missing. |
| Icon shows ⚠ *stale* | A fetch failed (network or endpoint change); it retries on the next poll and keeps the last-known values. |

---

## Uninstall

```bash
rm -f ~/.config/autostart/claude-meter.desktop   # remove autostart
rm -rf ~/.config/claude-meter                     # remove config (optional)
# then delete the cloned repo folder (which contains ./.venv)
```

---

## Status

Early **v0.1** — works end to end (live usage, per-model windows, rising-edge alerts, autostart). Development happens on the `develop` branch until v0.1 stabilises. Privacy: the app only ever **reads** your Claude Code token locally and talks to `api.anthropic.com`; it sends nothing to any third party.
