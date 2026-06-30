"""Claude Meter application — wires provider, model, alerts, tray together."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import icon as iconmod
from .alerts import AlertEngine
from .config import load_config
from .model import UsageModel
from .notify import NotificationService
from .provider import AuthState, OAuthHttpProvider, ProviderResult


class _FetchSignals(QObject):
    done = Signal(object)  # ProviderResult


class _FetchTask(QRunnable):
    def __init__(self, provider):
        super().__init__()
        self.provider = provider
        self.signals = _FetchSignals()
        self.setAutoDelete(False)

    def run(self):
        self.signals.done.emit(self.provider.fetch())


def _fmt_reset(dt: datetime | None) -> str:
    if dt is None:
        return ""
    local = dt.astimezone()
    now = datetime.now(local.tzinfo)
    if local.date() == now.date():
        return f"resets {local:%H:%M}"
    return f"resets {local:%a %H:%M}"


class App:
    def __init__(self, qapp: QApplication):
        self.qapp = qapp
        self.config = load_config()
        self.provider = OAuthHttpProvider(self.config)
        self.model = UsageModel()
        self.alerts = AlertEngine()
        self._tasks: set[_FetchTask] = set()

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(iconmod.make_icon("stale"))
        self.tray.setToolTip("Claude Meter — starting…")
        self.notify = NotificationService(self.tray)
        self._build_menu()
        self.tray.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.poll)
        self.timer.start(self.config.poll_interval_seconds * 1000)
        QTimer.singleShot(0, self.poll)  # poll immediately on startup

    # ---- menu ----------------------------------------------------------
    def _build_menu(self):
        menu = QMenu()
        self.header = QAction("Claude Meter", menu)
        self.header.setEnabled(False)
        menu.addAction(self.header)
        menu.addSeparator()

        refresh = QAction("Refresh now", menu)
        refresh.triggered.connect(self.poll)
        menu.addAction(refresh)

        pause_menu = menu.addMenu("Pause alerts")
        for label, mins in (("15 minutes", 15), ("1 hour", 60)):
            act = QAction(label, pause_menu)
            act.triggered.connect(lambda _checked=False, m=mins: self._pause(m))
            pause_menu.addAction(act)
        resume = QAction("Resume", pause_menu)
        resume.triggered.connect(lambda _checked=False: self._pause(0))
        pause_menu.addAction(resume)

        open_cfg = QAction("Open config…", menu)
        open_cfg.triggered.connect(self._open_config)
        menu.addAction(open_cfg)

        menu.addSeparator()
        quit_act = QAction("Quit", menu)
        quit_act.triggered.connect(self.qapp.quit)
        menu.addAction(quit_act)

        self.menu = menu
        self.tray.setContextMenu(menu)

    def _pause(self, minutes: int):
        self.alerts.pause(minutes)
        self._refresh_tray()

    def _open_config(self, *_):
        subprocess.Popen(["xdg-open", str(self.config.path)])

    # ---- polling -------------------------------------------------------
    def poll(self, *_):
        task = _FetchTask(self.provider)
        task.signals.done.connect(lambda res, t=task: self._on_result(res, t))
        self._tasks.add(task)
        QThreadPool.globalInstance().start(task)

    def _on_result(self, result: ProviderResult, task: _FetchTask):
        self._tasks.discard(task)
        self.model.update(result)
        for ev in self.alerts.evaluate(self.model, self.config):
            reset = _fmt_reset(ev.resets_at)
            body = f"You've used {ev.percent:.0f}% of your {ev.display_name} limit."
            if reset:
                body += f" ({reset})"
            self.notify.notify(
                f"Claude usage: {ev.percent:.0f}% — {ev.display_name}", body, ev.urgency
            )
        self._refresh_tray()

    # ---- tray presentation --------------------------------------------
    def _state(self) -> str:
        if self.model.auth_state == AuthState.UNAUTH:
            return "unauth"
        if self.model.stale:
            return "stale"
        if self.alerts.is_paused:
            return "paused"
        worst = self.model.worst_percent(self.config.include_inactive)
        if worst >= 100:
            return "critical"
        if worst >= min(self.config.thresholds):
            return "warning"
        return "ok"

    def _refresh_tray(self):
        state = self._state()
        self.tray.setIcon(iconmod.make_icon(state))
        self.tray.setToolTip(self._tooltip(state))

    def _tooltip(self, state: str) -> str:
        lines = ["Claude Meter"]
        if self.model.auth_state == AuthState.UNAUTH:
            lines.append(f"  Not logged in — {self.model.last_error or 'run `claude`'}")
            return "\n".join(lines)
        windows = self.model.visible(self.config.include_inactive)
        if not windows:
            lines.append("  (no usage data yet)")
        for w in windows:
            reset = _fmt_reset(w.resets_at)
            reset = f"  ({reset})" if reset else ""
            lines.append(f"  {w.display_name}: {w.percent:.0f}%{reset}")
        if state == "stale":
            lines.append(f"  ⚠ stale — {self.model.last_error or 'fetch failed'}")
        if self.alerts.is_paused:
            lines.append("  ⏸ alerts paused")
        age = self.model.age_seconds()
        if age is not None:
            lines.append(f"  Updated {int(age)}s ago")
        return "\n".join(lines)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Claude Meter")
    app.setApplicationDisplayName("Claude Meter")
    app.setDesktopFileName("claude-meter")
    app.setQuitOnLastWindowClosed(False)  # tray-only app, no windows

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("No system tray available on this session.", file=sys.stderr)
        return 1

    App(app)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
