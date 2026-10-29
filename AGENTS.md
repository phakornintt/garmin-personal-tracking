# Repository Guidelines

## Project Structure & Module Organization

- `app.py` contains the Streamlit dashboard.
- `src/garmin_running_tracker/` contains the installable Python package: `cli.py` defines the `garmin-runs` command, `sync.py` fetches and normalizes Garmin activities, and `csv_store.py` reads and writes `data/runs.csv`.
- `README.md` documents setup and use. Runtime data and credentials are local and should not be committed; `data/`, `.env`, and virtual environments are ignored.
- There is no test or asset directory yet.

## Build, Test, and Development Commands

Use Python 3.12 or newer:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

- `garmin-runs sync` imports or updates activities in the CSV; it requires a configured Garmin Personal API key.
- `streamlit run app.py` starts the local dashboard.
- No automated test suite or test runner is configured yet. If adding tests, place them under `tests/` and document the chosen runner and command.

## Coding Style & Naming Conventions

Use four spaces for Python indentation, `snake_case` for modules, functions, and variables, and `PascalCase` for classes. Keep data normalization and CSV field changes aligned between the sync code, CSV store, and dashboard. No formatter or linter is configured; keep changes focused and consistent with the surrounding code.

## Testing Guidelines

For changes to sync or CSV handling, verify activity IDs are deduplicated and existing rows remain intact. For dashboard changes, verify empty CSVs and missing heart-rate values display cleanly. Do not run live Garmin syncs for routine checks; they require personal credentials and modify local activity data.

## Commit & Pull Request Guidelines

The repository currently has one commit (`Initial commit: Garmin running tracker`), so no established commit convention exists. Use a short, descriptive subject, such as `Show pace trend by heart-rate band`. PRs should summarize the change, list checks performed, and include a screenshot for visible dashboard changes. Link related issues when applicable.

## Security & Configuration

Never commit Garmin API keys, bearer tokens, or personal activity exports. Use `GARMIN_PERSONAL_API_KEY` or Garmin's user-level key file described in the README. Keep generated CSV data local.
