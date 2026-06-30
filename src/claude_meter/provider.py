"""Usage data providers.

Primary: OAuthHttpProvider — reads the Bearer token Claude Code stores at
~/.claude/.credentials.json (read-only) and GETs the undocumented usage endpoint.
See docs/Usage-Data-Provider.md and docs/API-Reference-Usage-Endpoint.md.
"""

from __future__ import annotations

import enum
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone

USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
CRED_PATH = os.path.expanduser("~/.claude/.credentials.json")


class AuthState(enum.Enum):
    AUTH = "authenticated"
    UNAUTH = "unauthenticated"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class UsageReading:
    window_id: str
    display_name: str
    group: str
    kind: str
    scope_model: str | None
    utilization: float
    resets_at: datetime | None
    is_active: bool


@dataclass
class ProviderResult:
    auth_state: AuthState
    readings: list[UsageReading] = field(default_factory=list)
    error: str | None = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _window_meta(entry: dict):
    """Map a limits[] entry -> (window_id, display_name, group, scope_model, typed_key)."""
    kind = entry.get("kind")
    if kind == "session":
        return "5h", "5-hour", "session", None, "five_hour"
    if kind == "weekly_all":
        return "weekly", "Weekly (all models)", "weekly", None, "seven_day"
    if kind == "weekly_scoped":
        scope = entry.get("scope") or {}
        model = (scope.get("model") or {}).get("display_name") or "scoped"
        mid = model.lower().replace(" ", "-")
        return f"weekly:{mid}", f"Weekly · {model}", "weekly", model, f"seven_day_{mid}"
    group = entry.get("group") or "other"
    return str(kind), str(kind), group, None, None


class OAuthHttpProvider:
    def __init__(self, config=None, usage_url: str = USAGE_URL, cred_path: str = CRED_PATH):
        self.usage_url = usage_url
        self.cred_path = cred_path

    def _read_token(self) -> str | None:
        with open(self.cred_path) as f:
            data = json.load(f)
        return (data.get("claudeAiOauth") or {}).get("accessToken")

    def _parse(self, data: dict) -> list[UsageReading]:
        readings: list[UsageReading] = []
        for entry in data.get("limits", []) or []:
            window_id, name, group, scope_model, typed_key = _window_meta(entry)
            typed = data.get(typed_key) if typed_key else None
            if isinstance(typed, dict) and typed.get("utilization") is not None:
                util = float(typed["utilization"])
                resets = _parse_dt(typed.get("resets_at"))
            else:
                util = float(entry.get("percent") or 0.0)
                resets = _parse_dt(entry.get("resets_at"))
            readings.append(
                UsageReading(
                    window_id=window_id,
                    display_name=name,
                    group=group,
                    kind=str(entry.get("kind")),
                    scope_model=scope_model,
                    utilization=util,
                    resets_at=resets,
                    is_active=bool(entry.get("is_active")),
                )
            )
        return readings

    def fetch(self) -> ProviderResult:
        try:
            token = self._read_token()
        except FileNotFoundError:
            return ProviderResult(AuthState.UNAUTH, error="Claude Code credentials not found")
        except (OSError, json.JSONDecodeError) as e:
            return ProviderResult(AuthState.ERROR, error=f"reading credentials: {e}")
        if not token:
            return ProviderResult(AuthState.UNAUTH, error="no access token (run `claude` to log in)")

        req = urllib.request.Request(
            self.usage_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "claude-meter/0.1",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                return ProviderResult(AuthState.UNAUTH, error=f"HTTP {e.code} — re-run `claude`")
            return ProviderResult(AuthState.ERROR, error=f"HTTP {e.code}")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            return ProviderResult(AuthState.ERROR, error=f"network: {e}")
        except json.JSONDecodeError as e:
            return ProviderResult(AuthState.ERROR, error=f"bad response: {e}")

        return ProviderResult(AuthState.AUTH, readings=self._parse(data))
