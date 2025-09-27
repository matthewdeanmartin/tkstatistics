# tkstatistics/core/dataset.py

"""
Defines the in-memory data model for a tabular dataset.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

# A Row is a dictionary from column names (str) to values (Any)
Row = Dict[str, Any]
# A DataSet is a list of such rows
DataSet = List[Row]


class TabularData:
    """A wrapper for a list of dictionaries representing a dataset."""

    def __init__(self, name: str, data: Optional[DataSet] = None):
        self.name = name
        self._data: DataSet = data if data is not None else []
        self._column_names: List[str] = []
        if self._data:
            self._column_names = list(self._data[0].keys())

    @property
    def shape(self) -> tuple[int, int]:
        """Returns (number of rows, number of columns)."""
        return len(self._data), len(self._column_names)

    @property
    def column_names(self) -> List[str]:
        """Returns the list of column names."""
        return self._column_names

    def get_column(self, name: str) -> List[Any]:
        """Extracts a column by name."""
        if name not in self._column_names:
            raise ValueError(f"Column '{name}' not found.")
        return [row.get(name) for row in self._data]

    def get_row(self, index: int) -> Row:
        """Extracts a row by its index."""
        return self._data[index]

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, index: int) -> Row:
        return self._data[index]

    def to_list_of_dicts(self) -> DataSet:
        """Returns the raw internal data structure."""
        return self._data

    @classmethod
    def from_list_of_dicts(cls, name: str, data: DataSet) -> TabularData:
        """Creates a TabularData instance from a list of dictionaries."""
        if not data:
            return cls(name, [])
        # Ensure all dicts have the same keys
        keys = data[0].keys()
        if any(row.keys() != keys for row in data):
            raise ValueError("All dictionaries in the list must have the same keys.")
        return cls(name, data)
