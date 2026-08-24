"""Optional MPRIS metadata reader for librespot/raspotify."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from rasputinfy.state import PlaybackState


def _parse_playerctl_output(output: str) -> PlaybackState | None:
    metadata: dict[str, str] = {}
    status = "idle"

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower() in {"playing", "paused", "stopped"}:
            status = line.lower()
            continue
        if " " not in line:
            continue
        key, value = line.split(" ", 1)
        metadata[key.rsplit(".", 1)[-1]] = value.strip()

    title = metadata.get("title", "")
    artist = metadata.get("artist", "")
    if not title and not artist:
        return None

    if status == "stopped":
        playback_status = "idle"
    elif status == "paused":
        playback_status = "paused"
    else:
        playback_status = "playing"

    return PlaybackState(status=playback_status, artist=artist, title=title)


def read_mpris_state() -> PlaybackState | None:
    """Return playback state from playerctl when librespot MPRIS is available."""
    if not shutil.which("playerctl"):
        return None

    try:
        players = subprocess.run(
            ["playerctl", "-l"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    player_names = [
        line.strip()
        for line in players.stdout.splitlines()
        if line.strip()
    ]
    librespot_players = [
        name for name in player_names if "librespot" in name.lower()
    ]
    if not librespot_players:
        return None

    player = librespot_players[0]
    try:
        status_result = subprocess.run(
            ["playerctl", "-p", player, "status"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
        metadata_result = subprocess.run(
            ["playerctl", "-p", player, "metadata"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    combined = "\n".join(
        part.strip()
        for part in (status_result.stdout.strip(), metadata_result.stdout.strip())
        if part.strip()
    )
    return _parse_playerctl_output(combined)


def merge_with_mpris(state: PlaybackState) -> PlaybackState:
    """Prefer MPRIS when it reports active playback metadata."""
    mpris_state = read_mpris_state()
    if mpris_state is None:
        return state

    if mpris_state.status == "idle" and state.status != "idle":
        return state

    if mpris_state.title or mpris_state.status == "idle":
        return mpris_state

    return state
