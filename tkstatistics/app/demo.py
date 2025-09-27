# tkstatistics/app/demo.py

"""
Generates an in-memory demo dataset and project for instant use on startup.
"""
from __future__ import annotations

import random
from typing import Any, Dict

from tkstatistics.core.dataset import DataSet, TabularData


def create_demo_dataset() -> TabularData:
    """
    Generates a sample dataset with 50 rows and 4 columns (x1, x2, x3, y).

    The 'y' variable is constructed as a noisy linear combination of the others
    to make it suitable for regression analysis later.
    """
    data: DataSet = []
    for _ in range(50):
        x1 = random.uniform(10.0, 90.0)
        x2 = random.uniform(50.0, 150.0)
        x3 = random.gauss(5.0, 2.0)

        # Create a plausible relationship for y
        noise = random.gauss(0, 15)
        y = (1.8 * x1) + (0.5 * x2) - (4.3 * x3) + 75 + noise

        data.append({"x1": round(x1, 2), "x2": round(x2, 2), "x3": round(x3, 2), "y": round(y, 2)})

    return TabularData.from_list_of_dicts("demo_data", data)


def get_demo_spec() -> Dict[str, Any]:
    """
    Returns a pre-defined JSON spec for a descriptives analysis on the demo data.
    """
    return {
        "analysis": "describe",
        "dataset": "demo_data",
        "inputs": {"data": "y"},  # Input role 'data' mapped to variable 'y'
        "options": {},
        "seed": 20250926,
        "version": "tkstatistics 0.1",
    }
