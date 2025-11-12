# tkstatistics/core/project.py

"""
Manages the SQLite project file, including schema, data storage, and retrieval.
"""
from __future__ import annotations

import datetime
import json
import sqlite3
from pathlib import Path
from typing import Any

from .dataset import DataSet, TabularData


class Project:
    """Manages a single tkstatistics project file (*.statproj)."""

    SCHEMA_SQL = """
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS rows (
                dataset_id INTEGER NOT NULL,
                row_idx INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                PRIMARY KEY (dataset_id, row_idx),
                FOREIGN KEY (dataset_id) REFERENCES datasets(id)
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY,
                dataset_id INTEGER,
                spec_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """

    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        self.conn = sqlite3.connect(self.filepath)
        self._create_schema()

    def _create_schema(self):
        """Executes the schema DDL if tables don't exist."""
        with self.conn:
            self.conn.executescript(self.SCHEMA_SQL)

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()

    def get_dataset_id(self, name: str) -> int | None:
        """Finds the ID of a dataset by its name."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM datasets WHERE name = ?", (name,))
        result = cursor.fetchone()
        return result[0] if result else None

    # ... (save_dataset, load_dataset, list_datasets are unchanged) ...
    def save_dataset(self, table: TabularData):
        """Saves or updates a TabularData object in the database."""
        now = datetime.datetime.now().isoformat()
        with self.conn:
            cursor = self.conn.cursor()
            dataset_id = self.get_dataset_id(table.name)
            if dataset_id:
                cursor.execute("UPDATE datasets SET updated_at = ? WHERE id = ?", (now, dataset_id))
                # Clear old data for this dataset
                cursor.execute("DELETE FROM rows WHERE dataset_id = ?", (dataset_id,))
            else:
                cursor.execute(
                    "INSERT INTO datasets (name, created_at, updated_at) VALUES (?, ?, ?)", (table.name, now, now)
                )
                dataset_id = cursor.lastrowid

            rows_to_insert = [(dataset_id, i, json.dumps(row)) for i, row in enumerate(table.to_list_of_dicts())]
            if rows_to_insert:
                cursor.executemany(
                    "INSERT INTO rows (dataset_id, row_idx, payload_json) VALUES (?, ?, ?)", rows_to_insert
                )

    def load_dataset(self, name: str) -> TabularData:
        """Loads a dataset from the database by name."""
        dataset_id = self.get_dataset_id(name)
        if not dataset_id:
            raise ValueError(f"Dataset '{name}' not found in project.")

        cursor = self.conn.cursor()
        cursor.execute("SELECT payload_json FROM rows WHERE dataset_id = ? ORDER BY row_idx", (dataset_id,))

        data: DataSet = [json.loads(row[0]) for row in cursor.fetchall()]
        return TabularData.from_list_of_dicts(name, data)

    def list_datasets(self) -> list[str]:
        """Returns a list of all dataset names in the project."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM datasets ORDER BY name")
        return [row[0] for row in cursor.fetchall()]

    # --- New methods for handling analyses ---

    def save_analysis(self, spec: dict[str, Any]):
        """Saves an analysis spec to the database."""
        dataset_name = spec.get("dataset")
        dataset_id = self.get_dataset_id(dataset_name) if dataset_name else None

        now = datetime.datetime.now().isoformat()
        spec_json = json.dumps(spec)

        with self.conn:
            self.conn.execute(
                "INSERT INTO analyses (dataset_id, spec_json, created_at) VALUES (?, ?, ?)",
                (dataset_id, spec_json, now),
            )

    def list_analyses(self) -> list[dict[str, Any]]:
        """Returns a list of all saved analysis specs."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT spec_json FROM analyses ORDER BY id")
        return [json.loads(row[0]) for row in cursor.fetchall()]
