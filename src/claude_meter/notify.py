"""Notification delivery via the system tray (Plasma renders these as popups)."""

from __future__ import annotations

from PySide6.QtWidgets import QSystemTrayIcon

_URGENCY_ICON = {
    "normal": QSystemTrayIcon.MessageIcon.Information,
    "high": QSystemTrayIcon.MessageIcon.Warning,
    "critical": QSystemTrayIcon.MessageIcon.Critical,
}


class NotificationService:
    def __init__(self, tray: QSystemTrayIcon):
        self.tray = tray

    def notify(self, title: str, body: str, urgency: str = "normal") -> None:
        icon = _URGENCY_ICON.get(urgency, QSystemTrayIcon.MessageIcon.Information)
        timeout_ms = 0 if urgency == "critical" else 10000
        self.tray.showMessage(title, body, icon, timeout_ms)
