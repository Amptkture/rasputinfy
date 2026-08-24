#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/rasputinfy"
STATE_DIR="/var/lib/rasputinfy"
RASPOTIFY_DEFAULT="/etc/default/raspotify"
ONEVENT_PATH="${INSTALL_DIR}/scripts/onevent_handler.py"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo $0"
  exit 1
fi

if [[ ! -d "${INSTALL_DIR}" ]]; then
  echo "Expected repo at ${INSTALL_DIR}. Clone it first:"
  echo "  sudo git clone <your-repo-url> ${INSTALL_DIR}"
  exit 1
fi

echo "==> Installing system packages"
apt-get update
apt-get install -y python3 python3-venv python3-pip git chromium-browser playerctl

echo "==> Creating Python virtualenv"
python3 -m venv "${INSTALL_DIR}/.venv"
"${INSTALL_DIR}/.venv/bin/pip" install --upgrade pip
"${INSTALL_DIR}/.venv/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"

echo "==> Preparing state directory"
install -d -m 775 "${STATE_DIR}"
chown raspotify:raspotify "${STATE_DIR}" 2>/dev/null || chown pi:pi "${STATE_DIR}"

echo "==> Making onevent handler executable"
chmod 755 "${ONEVENT_PATH}"

echo "==> Installing systemd units"
install -m 644 "${INSTALL_DIR}/systemd/rasputinfy.service" /etc/systemd/system/rasputinfy.service
install -m 644 "${INSTALL_DIR}/systemd/rasputinfy-kiosk.service" /etc/systemd/system/rasputinfy-kiosk.service

echo "==> Configuring raspotify onevent hook"
install -d /etc/systemd/system/raspotify.service.d
cat > /etc/systemd/system/raspotify.service.d/rasputinfy.conf <<EOF
[Service]
ReadWritePaths=+${STATE_DIR}
EOF

if [[ -f "${RASPOTIFY_DEFAULT}" ]]; then
  if grep -q "onevent_handler.py" "${RASPOTIFY_DEFAULT}"; then
    echo "Raspotify already references onevent_handler.py"
  else
    if grep -q '^OPTIONS=' "${RASPOTIFY_DEFAULT}"; then
      sed -i "s|^OPTIONS=\"|OPTIONS=\"--onevent ${ONEVENT_PATH} |" "${RASPOTIFY_DEFAULT}"
    else
      echo "OPTIONS=\"--onevent ${ONEVENT_PATH}\"" >> "${RASPOTIFY_DEFAULT}"
    fi
  fi
else
  echo "WARNING: ${RASPOTIFY_DEFAULT} not found. Add manually:"
  echo "OPTIONS=\"--onevent ${ONEVENT_PATH}\""
fi

echo "==> Enabling services"
systemctl daemon-reload
systemctl enable rasputinfy.service
systemctl restart raspotify.service || true
systemctl restart rasputinfy.service

echo
echo "Install complete."
echo "Optional kiosk mode (fullscreen Chromium):"
echo "  sudo systemctl enable --now rasputinfy-kiosk.service"
echo
echo "Verify playback events:"
echo "  journalctl -u raspotify -f"
echo "Open display manually:"
echo "  http://127.0.0.1:8765"
