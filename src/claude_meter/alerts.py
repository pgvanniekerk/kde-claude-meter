"""Alert engine: rising-edge threshold crossings, per window.
See docs/Notifications-and-Alerts.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class AlertEvent:
    window_id: str
    display_name: str
    threshold: int
    percent: float
    urgency: str
    resets_at: datetime | None


class AlertEngine:
    def __init__(self):
        # highest threshold already notified, per window id
        self.last_notified: dict[str, int] = {}
        # last seen reset timestamp per window, to detect rollovers
        self._last_reset: dict[str, str | None] = {}
        self.paused_until: datetime | None = None

    def pause(self, minutes: int) -> None:
        if minutes <= 0:
            self.paused_until = None
        else:
            from datetime import timedelta

            self.paused_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)

    @property
    def is_paused(self) -> bool:
        return self.paused_until is not None and datetime.now(timezone.utc) < self.paused_until

    def evaluate(self, model, config) -> list[AlertEvent]:
        events: list[AlertEvent] = []
        for w in model.visible(config.include_inactive):
            reset_id = w.resets_at.isoformat() if w.resets_at else None
            # On a genuine rollover (reset timestamp changed since we last saw it),
            # clear this window's notified memory so it can warn again.
            if w.window_id in self._last_reset and self._last_reset[w.window_id] != reset_id:
                self.last_notified[w.window_id] = 0
            self._last_reset[w.window_id] = reset_id

            thresholds = config.resolve_thresholds(w.window_id, w.group)
            prev = self.last_notified.get(w.window_id, 0)
            crossed = [t for t in thresholds if w.percent >= t and t > prev]
            if not crossed:
                continue
            top = max(crossed)
            self.last_notified[w.window_id] = top
            events.append(
                AlertEvent(
                    window_id=w.window_id,
                    display_name=w.display_name,
                    threshold=top,
                    percent=w.percent,
                    urgency=config.urgency_for(top),
                    resets_at=w.resets_at,
                )
            )

        if self.is_paused:
            # Suppress delivery but keep the edge memory updated above,
            # so we don't fire a backlog when alerts resume.
            return []
        return events
