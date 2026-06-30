"""In-memory usage model. See docs/Data-Model.md."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .provider import AuthState, ProviderResult, UsageReading


@dataclass
class WindowUsage:
    window_id: str
    display_name: str
    group: str
    kind: str
    scope_model: str | None
    percent: float
    resets_at: datetime | None
    is_active: bool

    @classmethod
    def from_reading(cls, r: UsageReading) -> "WindowUsage":
        return cls(
            window_id=r.window_id,
            display_name=r.display_name,
            group=r.group,
            kind=r.kind,
            scope_model=r.scope_model,
            # `utilization` is already a percentage (0-100), not a 0..1 fraction.
            percent=round(r.utilization or 0.0, 1),
            resets_at=r.resets_at,
            is_active=r.is_active,
        )

    @property
    def is_dormant(self) -> bool:
        """A per-model window with no usage and no active reset — hidden by default."""
        return self.scope_model is not None and self.percent <= 0 and self.resets_at is None


class UsageModel:
    def __init__(self):
        self.windows: dict[str, WindowUsage] = {}
        self.auth_state: AuthState = AuthState.UNKNOWN
        self.stale: bool = True
        self.last_updated: datetime | None = None
        self.last_error: str | None = None

    def update(self, result: ProviderResult) -> None:
        self.auth_state = result.auth_state
        if result.auth_state == AuthState.AUTH:
            self.windows = {r.window_id: WindowUsage.from_reading(r) for r in result.readings}
            self.last_updated = result.fetched_at
            self.stale = False
            self.last_error = None
        else:
            # keep last-known windows; flag stale so the UI can show it
            self.stale = True
            self.last_error = result.error

    def visible(self, include_inactive: bool = False) -> list[WindowUsage]:
        ws = [w for w in self.windows.values() if include_inactive or not w.is_dormant]
        return sorted(ws, key=lambda w: (w.group != "session", -w.percent, w.window_id))

    def worst_percent(self, include_inactive: bool = False) -> float:
        return max((w.percent for w in self.visible(include_inactive)), default=0.0)

    def age_seconds(self) -> float | None:
        if self.last_updated is None:
            return None
        return (datetime.now(timezone.utc) - self.last_updated).total_seconds()
