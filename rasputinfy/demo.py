"""Demo mode track rotation for local development."""

from __future__ import annotations

import itertools
import threading
import time

from rasputinfy.state import DEFAULT_STATE_PATH, PlaybackState, write_state

DEMO_TRACKS: list[tuple[str, str]] = [
    ("A-ha", "Take On Me"),
    ("Depeche Mode", "Enjoy the Silence"),
    ("The Human League", "Don't You Want Me"),
    ("Pet Shop Boys", "West End Girls"),
    ("New Order", "Blue Monday"),
    ("Tears for Fears", "Everybody Wants to Rule the World"),
    ("Duran Duran", "Hungry Like the Wolf"),
    ("Cyndi Lauper", "Girls Just Want to Have Fun"),
    ("Prince", "Purple Rain"),
    ("Madonna", "Material Girl"),
]

TRACK_SECONDS = 15
IDLE_SECONDS = 8


class DemoController:
    def __init__(
        self,
        state_path=DEFAULT_STATE_PATH,
        track_seconds: int = TRACK_SECONDS,
        idle_seconds: int = IDLE_SECONDS,
    ) -> None:
        self.state_path = state_path
        self.track_seconds = track_seconds
        self.idle_seconds = idle_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        cycle = itertools.cycle(DEMO_TRACKS)
        while not self._stop_event.is_set():
            write_state(PlaybackState(status="idle"), self.state_path)
            if self._stop_event.wait(self.idle_seconds):
                break

            artist, title = next(cycle)
            write_state(
                PlaybackState(status="playing", artist=artist, title=title),
                self.state_path,
            )
            if self._stop_event.wait(self.track_seconds):
                break

            write_state(
                PlaybackState(status="paused", artist=artist, title=title),
                self.state_path,
            )
            if self._stop_event.wait(4):
                break
