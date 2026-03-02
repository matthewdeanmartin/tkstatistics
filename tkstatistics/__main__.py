# tkstatistics/__main__.py

"""
Allows the tkstatistics package to be executed as a script.
Example: python -m tkstatistics --gui
"""

import sys

from tkstatistics.cli import main as cli_main


def main() -> int:
    """Console script entrypoint."""
    return cli_main()


if __name__ == "__main__":
    sys.exit(main())
