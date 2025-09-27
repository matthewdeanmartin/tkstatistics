# tkstatistics/cli.py

"""
Command-line interface for tkstatistics.
Launches the GUI or runs analyses headlessly.
"""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="tkstatistics: A Pure-Stdlib Statistical Desktop Application.")
    parser.add_argument(
        "--run",
        metavar="SPEC_FILE",
        help="Run an analysis headlessly from a JSON specification file.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Force launch the GUI (default action if no other flags are given).",
    )

    if argv is None:
        argv = sys.argv[1:]

    args = parser.parse_args(argv)

    if args.run:
        print(f"Headless mode: Running analysis from {args.run}...")
        # TODO: Implement spec runner logic from core.specs
        print("(Not yet implemented)")
        return 0
    else:
        # Default action is to launch the GUI
        print("Launching GUI...")
        try:
            # We lazy-import the GUI to avoid loading tkinter for CLI-only tasks
            from tkstatistics.app import main as app_main

            app_main.launch_app()
        except ImportError:
            print("Error: Could not import the GUI application.", file=sys.stderr)
            print("Please ensure tkinter is available in your Python installation.", file=sys.stderr)
            return 1
        return 0


if __name__ == "__main__":
    sys.exit(main())
