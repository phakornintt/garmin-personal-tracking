"""CSV persistence for normalized running activities."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

CSV_FIELDS = [
    "activity_id",
    "start_time",
    "activity_name",
    "distance_km",
    "duration_seconds",
    "averageSpeed",
    "maxSpeed",
    "average_pace_min_per_km",
    "max_pace_min_per_km",
    "average_hr_bpm",
    "max_hr_bpm",
]


def read_activities(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames:
            return []
        rows = [dict(row) for row in reader]
        for row in rows:
            row.setdefault("averageSpeed", "")
            row.setdefault("maxSpeed", "")
            row.setdefault("average_pace_min_per_km", "")
            row.setdefault("max_pace_min_per_km", "")
            row.pop("pace_min_per_km", None)
            row.pop("speed_kmh", None)
        return rows


def write_activities(path: Path, activities: list[dict[str, str]]) -> None:
    """Replace the CSV atomically so an interrupted sync won't truncate it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(activities, key=lambda row: (row.get("start_time", ""), row.get("activity_id", "")))
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows({field: row.get(field, "") for field in CSV_FIELDS} for row in rows)
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
