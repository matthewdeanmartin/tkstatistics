# tkstatistics/cli.py

"""
Command-line interface for tkstatistics.
Launches the GUI or runs analyses headlessly.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tkstatistics.core import render, specs


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="tkstatistics: A Pure-Stdlib Statistical Desktop Application.")
    parser.add_argument(
        "--run",
        metavar="SPEC_FILE",
        help="Run an analysis headlessly from a JSON specification file.",
    )
    parser.add_argument(
        "--project",
        metavar="PROJECT_FILE",
        help="Project file used by --run.",
    )
    parser.add_argument(
        "--output",
        metavar="OUTPUT_FILE",
        help="Optional path to write the JSON run artifact.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format for stdout (default: json). The --output file is always JSON.",
    )
    parser.add_argument(
        "--commit-plan",
        metavar="PLAN_FILE",
        help="Commit a pre-registration plan (JSON) to the project. Prints the plan_id.",
    )
    parser.add_argument(
        "--audit",
        metavar="DATASET",
        help="Print a transparency report for DATASET (declared vs executed tests).",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Force launch the GUI (default action if no other flags are given).",
    )

    if argv is None:
        argv = sys.argv[1:]

    args = parser.parse_args(argv)

    if args.commit_plan:
        if not args.project:
            print("Error: --project is required when using --commit-plan.", file=sys.stderr)
            return 2
        from tkstatistics.core.project import Project

        try:
            plan = json.loads(Path(args.commit_plan).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Error reading plan file: {exc}", file=sys.stderr)
            return 1
        project = Project(Path(args.project))
        try:
            plan_id = project.commit_plan(plan)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        finally:
            project.close()
        print(plan_id)
        return 0

    if args.audit:
        if not args.project:
            print("Error: --project is required when using --audit.", file=sys.stderr)
            return 2
        from tkstatistics.core.project import Project

        project = Project(Path(args.project))
        try:
            report = specs.audit_dataset(project, args.audit)
        finally:
            project.close()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    if args.run:
        if not args.project:
            print("Error: --project is required when using --run.", file=sys.stderr)
            return 2

        spec_path = Path(args.run)
        project_path = Path(args.project)

        try:
            artifact = specs.run_spec(spec_path, project_path)
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        artifact_json = json.dumps(artifact, indent=2, sort_keys=True)
        if args.output:
            output_path = Path(args.output)
            try:
                output_path.write_text(artifact_json + "\n", encoding="utf-8")
            except OSError as exc:
                print(f"Error writing output artifact: {exc}", file=sys.stderr)
                return 1

        if args.format == "text":
            print(render.render_artifact(artifact))
        else:
            print(artifact_json)
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
