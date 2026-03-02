#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_PATH="${SCRIPT_DIR}/demo.statproj"
SPEC_PATH="${SCRIPT_DIR}/spec.describe.json"
DATASET_PATH="${SCRIPT_DIR}/dataset.csv"

if command -v uv >/dev/null 2>&1; then
	PYTHON_CMD=(uv run python)
else
	PYTHON_CMD=(python)
fi

"${PYTHON_CMD[@]}" - "${PROJECT_PATH}" "${DATASET_PATH}" <<'PY'
import csv
from pathlib import Path
import sys

from tkstatistics.core.dataset import TabularData
from tkstatistics.core.project import Project

project_path = Path(sys.argv[1])
dataset_path = Path(sys.argv[2])

rows = []
with dataset_path.open("r", encoding="utf-8", newline="") as handle:
    reader = csv.DictReader(handle)
    for row in reader:
        converted = {}
        for key, value in row.items():
            try:
                converted[key] = int(value)
            except (TypeError, ValueError):
                try:
                    converted[key] = float(value)
                except (TypeError, ValueError):
                    converted[key] = value
        rows.append(converted)

dataset = TabularData.from_list_of_dicts("mean_test_demo", rows)

project = Project(project_path)
try:
    project.save_dataset(dataset)
finally:
    project.close()
PY

"${PYTHON_CMD[@]}" -m tkstatistics --run "${SPEC_PATH}" --project "${PROJECT_PATH}"
