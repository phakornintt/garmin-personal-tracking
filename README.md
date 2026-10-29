# Garmin Running Progress

A local dashboard that tracks running pace and heart rate using your Garmin Connect Personal API data. Activities are stored in `data/runs.csv`.

## Requirements

- Python 3.12 or newer (the project has been run with Python 3.13)
- [`uv`](https://docs.astral.sh/uv/) or an installed Python 3.12+ interpreter
- A Garmin Connect Personal API key

## Setup

With `uv`:

```bash
uv python install 3.13
uv venv --clear --python 3.13 .venv
uv pip install --python .venv/bin/python -e .
```

Or, if Python 3.12 or newer is already installed:

```bash
python3.12 -m venv --clear .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools
python -m pip install -e .
```

The virtual environment must use Python 3.12 or newer. Check it with `source .venv/bin/activate` followed by `python --version`. Recreate older environments with `uv venv --clear --python 3.13 .venv` or `python3.12 -m venv --clear .venv` before installing.

## Garmin API Key

Create a Personal API key in Garmin Connect Web under **Profile & Account → Settings → Personal API Key → Create Key**. Garmin displays the new key once.

Save it outside the project in the default key file:

```bash
mkdir -p ~/.config/garmin
nano ~/.config/garmin/connect-personal-api-key
chmod 600 ~/.config/garmin/connect-personal-api-key
```

Paste only the key into the editor, save, and exit. Alternatively, set `GARMIN_PERSONAL_API_KEY` in the shell before running the sync. The Garmin client caches its bearer token in your user config directory. Never commit API keys, tokens, or activity exports.

## Sync

The initial import includes activities dated September 29, 2026 onward:

```bash
source .venv/bin/activate
garmin-runs sync
```

Later syncs start from the latest activity date already in the CSV, so activities added on the same day are picked up and existing rows are updated by activity ID. If the CSV starts after the September 29 cutoff, sync checks from the cutoff to fill in earlier missing activities. You can set a one-off date range with `--start-date` and `--end-date`; the September 29 cutoff still applies.

## Dashboard

```bash
source .venv/bin/activate
streamlit run app.py --server.address 127.0.0.1
```

Open `http://127.0.0.1:8501` in your browser. The server listens on localhost only. Stop it with `Ctrl+C`. The dashboard shows total runs and distance, latest average and maximum-speed pace, aligned daily pace and heart-rate charts with trend lines, weekly distance, and recent activities. You can set the starting value for each chart's y-axis. Pace is displayed in minutes per kilometer.

## CSV fields

`data/runs.csv` contains one row per run: activity ID, start time, activity name, distance in kilometers, duration in seconds, average and maximum speed in meters per second, average and maximum pace in minutes per kilometer, and average and maximum heart rate in beats per minute. Pace and heart-rate fields are left blank when Garmin does not provide the source values.
