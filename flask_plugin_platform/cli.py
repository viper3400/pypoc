from __future__ import annotations

import argparse

from waitress import serve

from flask_plugin_platform import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Flask plugin platform server.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", default=5000, type=int, help="Port to bind.")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Use Flask's development server with debug mode enabled.",
    )
    parser.add_argument(
        "--threads",
        default=8,
        type=int,
        help="Number of Waitress worker threads for non-debug runs.",
    )
    args = parser.parse_args()

    app = create_app()
    if args.debug:
        app.run(host=args.host, port=args.port, debug=True)
        return

    serve(app, host=args.host, port=args.port, threads=args.threads)


if __name__ == "__main__":
    main()
