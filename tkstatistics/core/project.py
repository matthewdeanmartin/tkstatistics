# tkstatistics/core/project.py

"""
Manages the SQLite project file, including schema, data storage, and retrieval.
"""

from __future__ import annotations

import datetime
import json
import math
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

            CREATE TABLE IF NOT EXISTS analysis_runs (
                id INTEGER PRIMARY KEY,
                dataset_id INTEGER,
                spec_hash TEXT NOT NULL UNIQUE,
                spec_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS analysis_plans (
                id INTEGER PRIMARY KEY,
                plan_id TEXT NOT NULL UNIQUE,
                plan_hash TEXT NOT NULL,
                dataset_id INTEGER,
                plan_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                committed_at TEXT
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
                cursor.execute("INSERT INTO datasets (name, created_at, updated_at) VALUES (?, ?, ?)", (table.name, now, now))
                dataset_id = cursor.lastrowid

            rows_to_insert = [(dataset_id, i, json.dumps(row)) for i, row in enumerate(table.to_list_of_dicts())]
            if rows_to_insert:
                cursor.executemany("INSERT INTO rows (dataset_id, row_idx, payload_json) VALUES (?, ?, ?)", rows_to_insert)

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

    def save_run_artifact(self, artifact: dict[str, Any]):
        """Saves or updates a headless run artifact keyed by spec hash."""
        spec = artifact.get("spec", {})
        spec_hash = artifact.get("spec_hash")
        if not isinstance(spec_hash, str) or not spec_hash:
            raise ValueError("Run artifact must include a non-empty spec_hash.")

        dataset_name = spec.get("dataset") if isinstance(spec, dict) else None
        dataset_id = self.get_dataset_id(dataset_name) if dataset_name else None

        now = datetime.datetime.now().isoformat()
        spec_json = json.dumps(spec, sort_keys=True)
        result_json = json.dumps(artifact, sort_keys=True)

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO analysis_runs (dataset_id, spec_hash, spec_json, result_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(spec_hash) DO UPDATE SET
                    dataset_id = excluded.dataset_id,
                    spec_json = excluded.spec_json,
                    result_json = excluded.result_json,
                    updated_at = excluded.updated_at
                """,
                (dataset_id, spec_hash, spec_json, result_json, now, now),
            )

    def get_p_values_for_dataset(self, dataset_name: str) -> list[tuple[str, float]]:
        """Returns [(spec_hash, p_value), ...] for all saved runs on dataset with a p_value."""
        dataset_id = self.get_dataset_id(dataset_name)
        if dataset_id is None:
            return []
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT spec_hash, result_json FROM analysis_runs WHERE dataset_id = ? ORDER BY id",
            (dataset_id,),
        )
        results = []
        for spec_hash, result_json_str in cursor.fetchall():
            try:
                artifact = json.loads(result_json_str)
                result = artifact.get("result", {})
                p_value = None
                for key in ("p_value", "p_value_exact", "p_value_approx"):
                    candidate = result.get(key) if isinstance(result, dict) else None
                    if isinstance(candidate, (int, float)):
                        p_value = candidate
                        break
                if isinstance(p_value, (int, float)) and math.isfinite(p_value):
                    results.append((spec_hash, float(p_value)))
            except (json.JSONDecodeError, AttributeError):
                continue
        return results

    # --- Pre-registration (analysis plans) ---

    def commit_plan(self, plan: dict[str, Any]) -> str:
        """Persist a plan as committed (immutable) and return its plan_id.

        Re-committing an identical plan (same hash) is idempotent. Attempting to
        store a different plan under an existing plan_id raises.
        """
        from . import plans as plans_mod

        pid = plans_mod.plan_id(plan)
        plan_hash = plans_mod.compute_plan_hash(plan)
        dataset_name = plan.get("dataset")
        dataset_id = self.get_dataset_id(dataset_name) if dataset_name else None
        now = datetime.datetime.now().isoformat()
        plan_json = json.dumps(plan, sort_keys=True)

        existing = self.get_plan(pid)
        if existing is not None:
            if plans_mod.compute_plan_hash(existing) != plan_hash:
                raise ValueError(f"A different plan already exists under id '{pid}'.")
            return pid  # idempotent

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO analysis_plans (plan_id, plan_hash, dataset_id, plan_json, created_at, committed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (pid, plan_hash, dataset_id, plan_json, now, now),
            )
        return pid

    def get_plan(self, plan_id: str) -> dict[str, Any] | None:
        """Fetch a committed plan dict by its plan_id, or None if absent."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT plan_json FROM analysis_plans WHERE plan_id = ?", (plan_id,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def list_plans(self, dataset_name: str | None = None) -> list[dict[str, Any]]:
        """List committed plans, optionally filtered to one dataset."""
        cursor = self.conn.cursor()
        if dataset_name is not None:
            dataset_id = self.get_dataset_id(dataset_name)
            if dataset_id is None:
                return []
            cursor.execute(
                "SELECT plan_json FROM analysis_plans WHERE dataset_id = ? ORDER BY id",
                (dataset_id,),
            )
        else:
            cursor.execute("SELECT plan_json FROM analysis_plans ORDER BY id")
        return [json.loads(row[0]) for row in cursor.fetchall()]
