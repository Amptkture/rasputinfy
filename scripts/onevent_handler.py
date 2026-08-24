#!/usr/bin/env python3
"""Librespot onevent hook — updates Rasputinfy playback state."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rasputinfy.state import parse_onevent_env, write_state  # noqa: E402


def main() -> int:
    state = parse_onevent_env()
    write_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
