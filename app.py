"""Streamlit dashboard for running speed and heart-rate trends."""

from pathlib import Path

import pandas as pd
import streamlit as st

CSV_PATH = Path(__file__).parent / "data" / "runs.csv"

st.set_page_config(page_title="Garmin Running Progress", page_icon="🏃", layout="wide")
st.title("Garmin Running Progress")
st.caption("Track running speed and heart rate over time")

if not CSV_PATH.exists():
    st.info("No run data yet. Set up your Garmin Personal API key, then run `garmin-runs sync`.")
    st.stop()

data = pd.read_csv(CSV_PATH)
if data.empty:
    st.info("The activity CSV is empty. Run `garmin-runs sync` to import your runs.")
    st.stop()

data["start_time"] = pd.to_datetime(data["start_time"], errors="coerce")
data = data.dropna(subset=["start_time"]).sort_values("start_time")
for column in ("distance_km", "duration_seconds", "pace_min_per_km", "speed_kmh", "average_hr_bpm", "max_hr_bpm"):
    data[column] = pd.to_numeric(data[column], errors="coerce")
if data.empty:
    st.warning("No valid activity dates were found in the CSV.")
    st.stop()

total_km = data["distance_km"].sum()
run_count = len(data)
recent = data.tail(10)
avg_pace = recent["pace_min_per_km"].mean()
avg_hr = recent["average_hr_bpm"].mean()

metric_columns = st.columns(4)
metric_columns[0].metric("Runs", f"{run_count}")
metric_columns[1].metric("Total distance", f"{total_km:.1f} km")
metric_columns[2].metric("Average pace · last 10 runs", f"{avg_pace:.2f} min/km" if pd.notna(avg_pace) else "—")
metric_columns[3].metric("Average HR · last 10 runs", f"{avg_hr:.0f} bpm" if pd.notna(avg_hr) else "—")

st.subheader("Pace and heart rate over time")
st.caption("Lower pace means faster running. Compare these trends across runs; route and effort can affect both.")
pace_trend, hr_trend = st.columns(2)
with pace_trend:
    st.caption("Pace · min/km (lower is faster)")
    st.line_chart(data.set_index("start_time")["pace_min_per_km"], height=260)
with hr_trend:
    st.caption("Average heart rate · bpm")
    st.line_chart(data.set_index("start_time")["average_hr_bpm"], height=260)

left, right = st.columns(2)
with left:
    st.subheader("Speed at similar heart rates")
    paired = data.dropna(subset=["average_hr_bpm", "pace_min_per_km"]).copy()
    if paired.empty:
        st.info("Heart-rate and pace values are needed to compare runs.")
    else:
        paired["HR band (bpm)"] = (paired["average_hr_bpm"] / 5).round() * 5
        by_hr = paired.groupby("HR band (bpm)", as_index=False).agg(
            runs=("activity_id", "count"), pace_min_per_km=("pace_min_per_km", "mean")
        )
        by_hr = by_hr.rename(columns={"pace_min_per_km": "Average pace (min/km)"}).set_index("HR band (bpm)")
        st.bar_chart(by_hr["Average pace (min/km)"])
        st.caption("Average pace grouped into 5 bpm bands. Lower is faster.")
with right:
    st.subheader("Weekly running volume")
    weekly = data.set_index("start_time")["distance_km"].resample("W-MON").sum().rename("Distance (km)")
    st.bar_chart(weekly)

st.subheader("Recent runs")
display = data.sort_values("start_time", ascending=False).head(20).copy()
display["start_time"] = display["start_time"].dt.strftime("%Y-%m-%d")
st.dataframe(
    display[["start_time", "activity_name", "distance_km", "pace_min_per_km", "speed_kmh", "average_hr_bpm", "max_hr_bpm"]],
    hide_index=True,
    use_container_width=True,
)
