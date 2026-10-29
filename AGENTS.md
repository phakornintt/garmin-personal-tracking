# Repository Guidelines

## Project Structure & Module Organization

- `app.py` contains the Streamlit dashboard.
- `src/garmin_running_tracker/` contains the installable Python package: `cli.py` defines the `garmin-runs` command, `sync.py` fetches and normalizes Garmin activities, and `csv_store.py` reads and writes `data/runs.csv`.
- `README.md` documents setup and use. Runtime data and credentials are local and should not be committed; `data/`, `.env`, and virtual environments are ignored.
- There is no test or asset directory yet.

## Build, Test, and Development Commands

Use Python 3.12 or newer. For setup and API-key configuration, follow `README.md`. The project is currently run with Python 3.13 via `uv`:

```bash
uv python install 3.13
uv venv --clear --python 3.13 .venv
uv pip install --python .venv/bin/python -e .
source .venv/bin/activate
```

If using an installed Python 3.12+ instead:

```bash
python3.12 -m venv --clear .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools
python -m pip install -e .
```

- `garmin-runs sync` imports or updates activities in the CSV; it requires a configured Garmin Personal API key.
- `streamlit run app.py --server.address 127.0.0.1` starts the dashboard on localhost only.
- No automated test suite or test runner is configured yet. If adding tests, place them under `tests/` and document the chosen runner and command.

## Coding Style & Naming Conventions

Use four spaces for Python indentation, `snake_case` for modules, functions, and variables, and `PascalCase` for classes. Keep data normalization and CSV field changes aligned between the sync code, CSV store, and dashboard. No formatter or linter is configured; keep changes focused and consistent with the surrounding code.

## Testing Guidelines

For changes to sync or CSV handling, verify activity IDs are deduplicated and existing rows remain intact. For dashboard changes, verify empty CSVs and missing heart-rate values display cleanly. Do not run live Garmin syncs for routine checks; they require personal credentials and modify local activity data.

## Commit & Pull Request Guidelines

Recent commits use short, descriptive subjects, such as `Add repository contributor guidelines`. Follow that style. PRs should summarize the change, list checks performed, and include a screenshot for visible dashboard changes. Link related issues when applicable.

## Security & Configuration

Never commit Garmin API keys, bearer tokens, or personal activity exports. Use `GARMIN_PERSONAL_API_KEY` or Garmin's user-level key file described in the README. Keep generated CSV data local.

## Documentation Sync on Push Request

Use `$docs-before-push` only after the user explicitly asks to push changes to GitHub. First finish the implementation, then review and update relevant documentation before staging, committing, or pushing. Do not run documentation sync after ordinary implementation requests. After sync, proceed with the explicitly requested push; the skill itself does not publish changes.
