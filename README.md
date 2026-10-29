# Garmin Running Progress

A local dashboard that tracks running pace and heart rate using your Garmin Connect Personal API data. Activities are stored in `data/runs.csv`.

## Requirements

- Python 3.12 or newer
- A Garmin Connect Personal API key

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Set `GARMIN_PERSONAL_API_KEY` in your shell, or save the key by itself in Garmin's default key file at `~/.config/garmin/connect-personal-api-key`. The official Garmin client caches its bearer token in your user config directory. Do not put either credential in this project.

## Sync

The initial import includes activities dated September 30, 2026 onward (after September 29, 2026):

```bash
garmin-runs sync
```

Later syncs start from the latest activity date already in the CSV, so activities added on the same day are picked up and existing rows are updated by activity ID. You can set a one-off date range with `--start-date` and `--end-date`; the September 30 cutoff still applies.

## Dashboard

```bash
streamlit run app.py
```

The dashboard shows overall running volume, recent pace and heart rate, pace grouped by 5 bpm heart-rate bands, weekly distance, and recent activities. Pace is displayed in minutes per kilometer; speed is also stored in kilometers per hour.

## CSV fields

`data/runs.csv` contains one row per run: activity ID, start time, activity name, distance, duration, pace, speed, average heart rate, and maximum heart rate. Heart-rate fields are left blank when Garmin does not provide them.
