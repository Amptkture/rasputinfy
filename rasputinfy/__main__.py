"""CLI entry point for Rasputinfy."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from rasputinfy.demo import DemoController
from rasputinfy.server import create_app


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rasputinfy — retro now-playing display for Raspotify"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Simulate changing tracks for local development",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("RASPUTINFY_HOST", "127.0.0.1"),
        help="Host to bind (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("RASPUTINFY_PORT", "8765")),
        help="Port to bind (default: 8765)",
    )
    parser.add_argument(
        "--state-path",
        default=os.environ.get("RASPUTINFY_STATE_PATH", "/var/lib/rasputinfy/state.json"),
        help="Path to shared playback state file",
    )
    parser.add_argument(
        "--no-mpris",
        action="store_true",
        help="Disable optional MPRIS metadata lookup",
    )
    args = parser.parse_args()

    state_path = Path(args.state_path)
    os.environ["RASPUTINFY_STATE_PATH"] = str(state_path)

    demo_controller: DemoController | None = None
    if args.demo:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        demo_controller = DemoController(state_path=state_path)
        demo_controller.start()
        print(f"Demo mode enabled — open http://{args.host}:{args.port}")

    app = create_app(
        demo=args.demo,
        use_mpris=not args.no_mpris,
        state_path=state_path,
    )

    try:
        app.run(host=args.host, port=args.port, debug=False, threaded=True)
    finally:
        if demo_controller:
            demo_controller.stop()


if __name__ == "__main__":
    main()
