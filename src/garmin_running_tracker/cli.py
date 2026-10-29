"""Command line entry point."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .sync import INITIAL_SYNC_START, sync_activities

DEFAULT_CSV = Path("data/runs.csv")


def main() -> None:
    parser = argparse.ArgumentParser(prog="garmin-runs", description="Sync Garmin running activities to CSV.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    sync_parser = subparsers.add_parser("sync", help="Import or update running activities.")
    sync_parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help=f"CSV path (default: {DEFAULT_CSV}).")
    sync_parser.add_argument(
        "--start-date",
        type=date.fromisoformat,
        default=None,
        help="Earliest date to include (default: 2026-09-29).",
    )
    sync_parser.add_argument("--end-date", type=date.fromisoformat, help="Latest date to include (default: today).")
    args = parser.parse_args()
    if args.command == "sync":
        sync_activities(args.csv, start_date=args.start_date, end_date=args.end_date)


if __name__ == "__main__":
    main()
