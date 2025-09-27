# tkstatistics/__main__.py

"""
Allows the tkstatistics package to be executed as a script.
Example: python -m tkstatistics --gui
"""
import sys

from tkstatistics.cli import main

if __name__ == "__main__":
    sys.exit(main())
