"""Configuration loading for Claude Meter.

Config lives at $XDG_CONFIG_HOME/claude-meter/config.toml (default ~/.config/...).
A default file is written on first run. See docs/Configuration-Reference.md.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_THRESHOLDS = [70, 80, 90, 100]
MIN_POLL_SECONDS = 15

_DEFAULT_TOML = """\
# Claude Meter configuration. See docs/Configuration-Reference.md
pollIntervalSeconds = 60

[windows]
mode = "auto"            # "auto" = track every window the API returns (incl. per-model)
includeInactive = false  # show dormant per-model windows (0%, no reset) too

[thresholds]
# Global warning percentages (rising-edge alerts fire once per crossing per window).
default = [70, 80, 90, 100]

# Optional per-group overrides ("session" = 5h, "weekly" = all weekly windows)
[thresholds.per_group]
# weekly = [70, 85, 95, 100]

# Optional per-window overrides (e.g. a specific model's weekly limit)
[thresholds.per_window]
# "weekly:opus" = [50, 75, 90, 100]

# threshold% -> urgency ("normal" | "high" | "critical")
[urgency]
90 = "high"
100 = "critical"
"""


@dataclass
class Config:
    path: Path
    poll_interval_seconds: int = 60
    thresholds: list[int] = field(default_factory=lambda: list(DEFAULT_THRESHOLDS))
    per_group: dict[str, list[int]] = field(default_factory=dict)
    per_window: dict[str, list[int]] = field(default_factory=dict)
    windows_mode: str = "auto"
    include_inactive: bool = False
    urgency: dict[int, str] = field(default_factory=lambda: {90: "high", 100: "critical"})

    def resolve_thresholds(self, window_id: str, group: str) -> list[int]:
        if window_id in self.per_window:
            return self.per_window[window_id]
        if group in self.per_group:
            return self.per_group[group]
        return self.thresholds

    def urgency_for(self, threshold: int) -> str:
        if threshold in self.urgency:
            return self.urgency[threshold]
        if threshold >= 100:
            return "critical"
        if threshold >= 90:
            return "high"
        return "normal"


def _config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(base) / "claude-meter" / "config.toml"


def _clean(vals) -> list[int]:
    out = sorted({int(v) for v in vals})
    return [v for v in out if 1 <= v <= 100]


def load_config() -> Config:
    path = _config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_DEFAULT_TOML)
    try:
        raw = tomllib.loads(path.read_text())
    except (tomllib.TOMLDecodeError, OSError):
        raw = {}

    th = raw.get("thresholds", {})
    if isinstance(th, list):  # tolerate a bare array form too
        th = {"default": th}
    thresholds = _clean(th.get("default", DEFAULT_THRESHOLDS)) or list(DEFAULT_THRESHOLDS)
    per_group = {g: _clean(v) for g, v in (th.get("per_group") or {}).items() if _clean(v)}
    per_window = {w: _clean(v) for w, v in (th.get("per_window") or {}).items() if _clean(v)}

    windows = raw.get("windows", {}) or {}
    urgency = {int(k): str(v) for k, v in (raw.get("urgency", {}) or {}).items()}

    poll = max(MIN_POLL_SECONDS, int(raw.get("pollIntervalSeconds", 60)))

    return Config(
        path=path,
        poll_interval_seconds=poll,
        thresholds=thresholds,
        per_group=per_group,
        per_window=per_window,
        windows_mode=str(windows.get("mode", "auto")),
        include_inactive=bool(windows.get("includeInactive", False)),
        urgency=urgency or {90: "high", 100: "critical"},
    )
