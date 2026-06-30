#!/usr/bin/env bash
# Install Claude Meter into a local venv and register a KDE autostart entry.
# Uses --system-site-packages so the already-installed PySide6 is reused (no large download).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$REPO/.venv"
LAUNCHER="$VENV/bin/claude-meter"

echo "Repo:   $REPO"
echo "Venv:   $VENV"

# Create a venv that reuses system site-packages (PySide6 lives there) and skips
# pip/ensurepip — we run via a launcher + PYTHONPATH, so no build/install step is needed.
if ! "$VENV/bin/python" -c "import PySide6" 2>/dev/null; then
  rm -rf "$VENV"
  python3 -m venv --system-site-packages --without-pip "$VENV"
fi

if ! "$VENV/bin/python" -c "import PySide6" 2>/dev/null; then
  echo "ERROR: PySide6 is not importable from the venv. Install it system-wide first." >&2
  exit 1
fi

# Launcher script runs the package from src/ without needing a build step.
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$REPO/src\${PYTHONPATH:+:\$PYTHONPATH}"
exec "$VENV/bin/python" -m claude_meter "\$@"
EOF
chmod +x "$LAUNCHER"

# KDE/XDG autostart entry.
AUTOSTART="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
mkdir -p "$AUTOSTART"
cat > "$AUTOSTART/claude-meter.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Claude Meter
Comment=Claude Max plan usage in the system tray
Exec=$LAUNCHER
Icon=claude-meter
Terminal=false
Categories=Utility;Network;
X-KDE-autostart-phase=2
EOF

echo "Launcher:  $LAUNCHER"
echo "Autostart: $AUTOSTART/claude-meter.desktop"
echo "Done. Start now with: $LAUNCHER"
