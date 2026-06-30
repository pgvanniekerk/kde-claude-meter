"""Programmatic Claude-style tray icon (no SVG dependency).

Draws the Claude "sunburst" mark in terracotta, with a small status dot
overlay (green/amber/red/grey) reflecting the worst window / app state.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPixmap

CLAUDE_CLAY = QColor("#D97757")

_STATE_COLORS = {
    "ok": QColor("#4CAF50"),
    "warning": QColor("#E8A33D"),
    "critical": QColor("#D14D41"),
    "stale": QColor("#9E9E9E"),
    "unauth": QColor("#9E9E9E"),
    "paused": QColor("#5E81AC"),
}

_RENDER = 128
_cache: dict[str, QIcon] = {}


def _draw_burst(p: QPainter, size: int, color: QColor) -> None:
    cx = cy = size / 2.0
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(color))
    n = 12
    inner = size * 0.07
    outer = size * 0.44
    width = size * 0.085
    for i in range(n):
        p.save()
        p.translate(cx, cy)
        p.rotate(360.0 / n * i)
        ray = QRectF(-width / 2.0, -outer, width, outer - inner)
        p.drawRoundedRect(ray, width / 2.0, width / 2.0)
        p.restore()


def _draw_status_dot(p: QPainter, size: int, color: QColor) -> None:
    d = size * 0.40
    x = size - d
    y = size - d
    # white ring for contrast on any panel colour
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(255, 255, 255, 235)))
    p.drawEllipse(QRectF(x - size * 0.03, y - size * 0.03, d + size * 0.06, d + size * 0.06))
    p.setBrush(QBrush(color))
    p.drawEllipse(QRectF(x, y, d, d))


def make_icon(state: str = "ok") -> QIcon:
    if state in _cache:
        return _cache[state]
    pm = QPixmap(_RENDER, _RENDER)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _draw_burst(p, _RENDER, CLAUDE_CLAY)
    dot = _STATE_COLORS.get(state)
    if dot is not None:
        _draw_status_dot(p, _RENDER, dot)
    p.end()
    icon = QIcon(pm)
    _cache[state] = icon
    return icon
