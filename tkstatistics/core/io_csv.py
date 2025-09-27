# tkstatistics/core/io_csv.py

"""
Handles the import and export of data from/to CSV and TSV files.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, Dict, List, Optional

from .dataset import DataSet, TabularData


def _convert_type(value: str) -> Any:
    """Attempt to convert a string value to a more specific type."""
    if value == "":
        return None
    # Try converting to integer
    try:
        return int(value)
    except ValueError:
        pass
    # Try converting to float
    try:
        return float(value)
    except ValueError:
        pass
    # Otherwise, return as string
    return value


def import_csv(file_path: Path, encoding: str = "utf-8-sig") -> TabularData:
    """
    Imports data from a CSV or TSV file into a TabularData object.

    It automatically detects the dialect (delimiter, quoting) and converts
    numeric columns to their appropriate types.

    Args:
        file_path: The path to the CSV/TSV file.
        encoding: The file encoding to use. Defaults to 'utf-8-sig' to handle BOM.

    Returns:
        A TabularData instance containing the imported data.
    """
    try:
        with file_path.open("r", newline="", encoding=encoding) as f:
            # Sniff the dialect from a sample of the file
            sniffer = csv.Sniffer()
            sample = f.read(2048)
            f.seek(0)
            dialect = sniffer.sniff(sample)

            reader = csv.DictReader(f, dialect=dialect)

            raw_data: DataSet = []
            for row in reader:
                converted_row = {key: _convert_type(val) for key, val in row.items()}
                raw_data.append(converted_row)

        dataset_name = file_path.stem
        return TabularData.from_list_of_dicts(dataset_name, raw_data)

    except (IOError, UnicodeDecodeError) as e:
        # Fallback for encoding errors
        if encoding == "utf-8-sig":
            try:
                return import_csv(file_path, encoding="latin-1")
            except Exception:
                raise e  # Raise original error if fallback fails
        raise e


def export_csv(table: TabularData, file_path: Path):
    """
    Exports a TabularData object to a CSV file.

    Args:
        table: The TabularData instance to export.
        file_path: The destination path for the CSV file.
    """
    if not table.column_names:
        # Write an empty file for an empty dataset
        file_path.write_text("")
        return

    with file_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=table.column_names)
        writer.writeheader()
        writer.writerows(table.to_list_of_dicts())
