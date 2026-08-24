# Rasputinfy

Retro 80s now-playing display for [Raspotify](https://github.com/dtcooper/raspotify). Shows the current artist and track on a connected monitor or CRT, with a synthwave playing screen and a classic TV test-card standby mode when nothing is playing.

## Features

- **Now playing** — large neon artist and track names on a synthwave grid horizon
- **Standby mode** — SMPTE-style test card when Spotify is idle
- **Demo mode** — simulate track changes on your dev machine
- **Pi kiosk** — optional fullscreen Chromium service for a dedicated display
- **Low overhead** — Python + Flask, vanilla HTML/CSS/JS (no build step)

## How it works

Raspotify (librespot) calls a `--onevent` script whenever playback changes. That script writes `/var/lib/rasputinfy/state.json`. The Rasputinfy web server reads that file and serves it to the browser. Optionally, if your Raspotify build exposes MPRIS, the server can also read metadata via `playerctl`.

---

## Development machine (demo mode)

Use this on any computer while building or previewing the UI.

### Prerequisites

- Python 3.10+
- `git`
- `gh` (only needed to create/push the GitHub repo)

### Setup

```bash
git clone git@github.com:<your-user>/rasputinfy.git
cd rasputinfy
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run demo mode

```bash
python3 -m rasputinfy --demo --state-path ./state.json
```

Open **http://127.0.0.1:8765** in your browser.

Demo mode cycles through 80s-style fake tracks, pauses, and idle periods so you can preview both UI modes.

### CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--demo` | off | Simulate changing tracks |
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `8765` | Bind port |
| `--state-path` | `/var/lib/rasputinfy/state.json` | Shared state file |
| `--no-mpris` | off | Disable MPRIS lookup |

Environment variables: `RASPUTINFY_HOST`, `RASPUTINFY_PORT`, `RASPUTINFY_STATE_PATH`.

### Create the GitHub repo

From the project root, after installing `git` and `gh` and running `gh auth login`:

```bash
bash scripts/create-github-repo.sh
```

This creates a **private** repo named `rasputinfy` and pushes the initial commit.

---

## Raspberry Pi (production)

Run the display on the **same Pi** as Raspotify, with a monitor connected via HDMI (or composite for CRT).

### Prerequisites

- Raspberry Pi OS (Debian Bullseye or newer)
- Raspotify installed and working ([install guide](https://github.com/dtcooper/raspotify))
- Display connected and desktop/session available (for kiosk mode)
- Network not required after install (everything is local)

Packages installed by the setup script:

- `python3`, `python3-venv`, `python3-pip`
- `git`
- `chromium-browser`
- `playerctl` (optional MPRIS support)

### Install

```bash
sudo git clone git@github.com:<your-user>/rasputinfy.git /opt/rasputinfy
cd /opt/rasputinfy
sudo bash scripts/install-pi.sh
```

The install script will:

1. Create a Python virtualenv at `/opt/rasputinfy/.venv`
2. Create `/var/lib/rasputinfy/` for shared state
3. Install systemd units for the web server (and optional kiosk)
4. Add a raspotify drop-in so the `raspotify` user can write state
5. Append `--onevent /opt/rasputinfy/scripts/onevent_handler.py` to `/etc/default/raspotify`

### Enable fullscreen kiosk (recommended)

```bash
sudo systemctl enable --now rasputinfy-kiosk.service
```

This launches Chromium in kiosk mode pointing at `http://127.0.0.1:8765`.

### Manual raspotify configuration

If you prefer to configure raspotify yourself, add to `/etc/default/raspotify`:

```bash
OPTIONS="--onevent /opt/rasputinfy/scripts/onevent_handler.py"
```

Ensure the handler is executable:

```bash
sudo chmod 755 /opt/rasputinfy/scripts/onevent_handler.py
```

Add a systemd drop-in so raspotify can write state:

```ini
# /etc/systemd/system/raspotify.service.d/rasputinfy.conf
[Service]
ReadWritePaths=+/var/lib/rasputinfy
```

Then reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart raspotify
sudo systemctl restart rasputinfy
```

### Verify onevent is working

```bash
journalctl -u raspotify -f
```

Play a track from Spotify Connect. You should see librespot log lines like `Running [.../onevent_handler.py]`.

Check state file:

```bash
cat /var/lib/rasputinfy/state.json
```

Check API:

```bash
curl http://127.0.0.1:8765/api/now-playing
```

---

## CRT / small monitor tips

- The layout uses ~8% safe margins for overscan.
- Optimized for 4:3 resolutions (640×480, 800×600).
- For composite CRT output, set a 4:3 mode in Raspberry Pi display settings.
- If scanlines or static noise are distracting, remove the `scanlines` class from `<body>` in `static/index.html`, or disable `.noise` in CSS.

To force a lower Chromium resolution in kiosk mode, edit `/etc/systemd/system/rasputinfy-kiosk.service` and add flags such as:

```bash
--window-size=800,600 --force-device-scale-factor=1
```

Then run `sudo systemctl daemon-reload && sudo systemctl restart rasputinfy-kiosk`.

---

## Optional: MPRIS metadata

Some Raspotify builds expose MPRIS. Check with:

```bash
playerctl -l
```

If you see a `librespot` player, Rasputinfy will prefer its metadata automatically. Install is included in `install-pi.sh`. MPRIS is **not required** — the onevent hook is the primary source.

---

## Troubleshooting

| Problem | Things to check |
|---------|-----------------|
| Standby screen never leaves | Is Spotify playing to this Raspotify device? Check `state.json` and `journalctl -u raspotify -f` |
| `state.json` not updating | Handler permissions (`chmod 755`), raspotify `OPTIONS`, `ReadWritePaths` drop-in |
| Blank browser | Is `rasputinfy.service` running? `systemctl status rasputinfy` |
| Kiosk won't start | Desktop running? `DISPLAY=:0`, user `pi` logged in, try opening Chromium manually |
| Permission denied on state file | `sudo chown raspotify:raspotify /var/lib/rasputinfy` and ensure drop-in exists |
| Wrong metadata | Try `--no-mpris` if MPRIS conflicts with onevent state |

---

## Project layout

```
rasputinfy/
├── rasputinfy/          # Python package
├── static/              # Web UI
├── scripts/             # onevent handler + Pi installer
├── systemd/             # Service units
└── requirements.txt
```

---

## License

MIT — use freely for personal projects. Raspotify/librespot require a Spotify Premium account for playback.
