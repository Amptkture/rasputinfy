"""Read and write playback state shared with the onevent handler."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DEFAULT_STATE_PATH = Path(
    os.environ.get("RASPUTINFY_STATE_PATH", "/var/lib/rasputinfy/state.json")
)


@dataclass
class PlaybackState:
    status: str = "idle"
    artist: str = ""
    title: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlaybackState":
        return cls(
            status=str(data.get("status", "idle")),
            artist=str(data.get("artist", "")),
            title=str(data.get("title", "")),
        )


def read_state(path: Path | None = None) -> PlaybackState:
    state_path = path or DEFAULT_STATE_PATH
    if not state_path.exists():
        return PlaybackState()

    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return PlaybackState()

    return PlaybackState.from_dict(data)


def write_state(state: PlaybackState, path: Path | None = None) -> None:
    state_path = path or DEFAULT_STATE_PATH
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = state_path.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps(state.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(state_path)


def parse_onevent_env(environ: dict[str, str] | None = None) -> PlaybackState:
    """Translate librespot PLAYER_EVENT env vars into playback state."""
    env = environ if environ is not None else os.environ
    event = env.get("PLAYER_EVENT", "")

    idle_events = {
        "stop",
        "stopped",
        "inactive",
        "session_terminated",
        "end_of_track",
        "unavailable",
    }

    if event in idle_events:
        return PlaybackState(status="idle")

    title = env.get("NAME", "").strip()
    artists_raw = env.get("ARTISTS", "").strip()
    artist = ", ".join(
        part.strip() for part in artists_raw.split("\n") if part.strip()
    )

    if event == "track_changed" and title:
        return PlaybackState(status="playing", artist=artist, title=title)

    if event == "paused" and title:
        return PlaybackState(status="paused", artist=artist, title=title)

    if event in {"playing", "start", "change"} and title:
        return PlaybackState(status="playing", artist=artist, title=title)

    if event in {"playing", "start", "change", "paused"}:
        previous = read_state()
        if previous.title:
            status = "paused" if event == "paused" else "playing"
            return PlaybackState(status=status, artist=previous.artist, title=previous.title)

    return read_state()
