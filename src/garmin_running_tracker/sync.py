"""Fetch Garmin activities and maintain the local running CSV."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .csv_store import read_activities, write_activities

INITIAL_SYNC_START = date(2026, 9, 29)
PAGE_SIZE = 100


def _first(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = record.get(key)
        if value is not None and value != "":
            return value
    return None


def _as_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None and value != "" else None
    except (TypeError, ValueError):
        return None


def _activity_id(activity: dict[str, Any]) -> str | None:
    value = _first(activity, "activityId", "activity_id", "id")
    return str(value) if value is not None else None


def _activity_type(activity: dict[str, Any]) -> str:
    value = _first(activity, "activityTypeKey", "sportTypeKey", "activityType")
    if isinstance(value, dict):
        value = _first(value, "typeKey", "key", "name")
    return str(value or "").lower().replace(" ", "_")


def _is_running(activity: dict[str, Any]) -> bool:
    return "run" in _activity_type(activity)


def _start_time(activity: dict[str, Any]) -> str | None:
    raw = _first(activity, "startTimeLocal", "startTime", "startTimeGMT", "start_time")
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        seconds = raw / 1000 if raw > 10_000_000_000 else raw
        return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
    value = str(raw)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return value


def normalize_activity(summary: dict[str, Any], details: dict[str, Any] | None = None) -> dict[str, str] | None:
    """Convert Garmin's summary/detail fields into one stable CSV row."""
    details = details or {}
    merged = {**summary, **details}
    identifier = _activity_id(merged)
    started = _start_time(merged)
    if not identifier or not started:
        return None

    distance_m = _as_float(_first(merged, "distance", "totalDistance", "distanceInMeters"))
    duration_s = _as_float(_first(merged, "duration", "elapsedDuration", "movingDuration"))
    distance_km = distance_m / 1000 if distance_m is not None else None
    average_speed = _first(merged, "averageSpeed")
    max_speed = _first(merged, "maxSpeed")
    average_hr = _as_float(_first(merged, "averageHR", "avgHR", "averageHeartRate"))
    maximum_hr = _as_float(_first(merged, "maxHR", "maximumHR", "maxHeartRate"))
    name = _first(merged, "activityName", "name", "activity_name") or ""

    def formatted(value: float | None, places: int = 2) -> str:
        return "" if value is None else f"{value:.{places}f}"

    def pace_from_speed(speed: Any) -> str:
        speed_mps = _as_float(speed)
        return "" if speed_mps is None or speed_mps <= 0 else formatted(1000 / speed_mps / 60)

    return {
        "activity_id": identifier,
        "start_time": started,
        "activity_name": str(name),
        "distance_km": formatted(distance_km),
        "duration_seconds": formatted(duration_s, 1),
        "averageSpeed": "" if average_speed is None else str(average_speed),
        "maxSpeed": "" if max_speed is None else str(max_speed),
        "average_pace_min_per_km": pace_from_speed(average_speed),
        "max_pace_min_per_km": pace_from_speed(max_speed),
        "average_hr_bpm": formatted(average_hr, 0),
        "max_hr_bpm": formatted(maximum_hr, 0),
    }


def _extract_activity_list(response: Any) -> list[dict[str, Any]]:
    if isinstance(response, list):
        return [item for item in response if isinstance(item, dict)]
    if isinstance(response, dict):
        for key in ("activities", "activityList", "results", "items"):
            value = response.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise ValueError("Unexpected Garmin activities response; expected a list of activities.")


def sync_activities(csv_path: Path, start_date: date | None = None, end_date: date | None = None) -> int:
    """Sync runs after the default cutoff, or from the latest stored day onward."""
    try:
        from garmin_personal_api import GarminPersonalApiClient, PersonalApiAuthenticator, resolve_api_key
    except ImportError as exc:
        raise RuntimeError("Install project dependencies first: python -m pip install -e .") from exc

    existing = read_activities(csv_path)
    stored_dates = [date.fromisoformat(row["start_time"][:10]) for row in existing if row.get("start_time")]
    if start_date is not None:
        requested_start = max(start_date, INITIAL_SYNC_START)
    elif stored_dates and min(stored_dates) > INITIAL_SYNC_START:
        requested_start = INITIAL_SYNC_START
    else:
        requested_start = max(max(stored_dates, default=INITIAL_SYNC_START), INITIAL_SYNC_START)
    requested_end = end_date or date.today()
    if requested_start > requested_end:
        print(f"Already up to date through {requested_end.isoformat()}.")
        return 0

    with PersonalApiAuthenticator() as authenticator:
        token = authenticator.obtain_token(resolve_api_key())
    with GarminPersonalApiClient(token.access_token) as client:
        summaries: list[dict[str, Any]] = []
        offset = 0
        while True:
            response = client.search_activities(
                start=offset,
                limit=PAGE_SIZE,
                start_date=requested_start,
                end_date=requested_end,
            )
            page = _extract_activity_list(response)
            summaries.extend(page)
            if len(page) < PAGE_SIZE:
                break
            offset += len(page)

        indexed = {row["activity_id"]: row for row in existing if row.get("activity_id")}
        imported = 0
        for summary in summaries:
            if not _is_running(summary):
                continue
            identifier = _activity_id(summary)
            if not identifier:
                continue
            details = client.get_activity(int(identifier))
            if not isinstance(details, dict):
                details = {}
            row = normalize_activity(summary, details)
            if row is None or row["start_time"][:10] < INITIAL_SYNC_START.isoformat():
                continue
            indexed[row["activity_id"]] = row
            imported += 1

    write_activities(csv_path, list(indexed.values()))
    print(f"Synced {imported} running activit{'y' if imported == 1 else 'ies'} to {csv_path}.")
    return imported
