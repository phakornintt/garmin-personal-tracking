"""Streamlit dashboard for running speed and heart-rate trends."""

from math import floor
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

CSV_PATH = Path(__file__).parent / "data" / "runs.csv"


def format_pace(pace_min_per_km: float) -> str:
    total_seconds = round(pace_min_per_km * 60)
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d} min/km"


def parse_pace(value: str) -> float | None:
    parts = value.strip().split(":")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        return None
    minutes, seconds = map(int, parts)
    if seconds >= 60:
        return None
    return minutes + seconds / 60


def make_hover_chart(
    data,
    field,
    y_encoding,
    x_encoding,
    color,
    tooltip_title,
    tooltip_format,
    hover,
    tooltip_field=None,
    guide_data=None,
):
    base = alt.Chart(data)
    line = base.mark_line(color=color).encode(x=x_encoding, y=y_encoding)
    layers = [line]
    if data["start_time"].nunique() > 1:
        layers.append(
            base.transform_regression(on="start_time", regression=field)
            .mark_line(color="#777777", opacity=1, strokeDash=[6, 4], size=1.5)
            .encode(x=x_encoding, y=y_encoding)
        )
    tooltip_value = (
        alt.Tooltip(f"{tooltip_field}:N", title=tooltip_title)
        if tooltip_field
        else alt.Tooltip(field, title=tooltip_title, format=tooltip_format)
    )
    selector = base.mark_point(size=180, opacity=0, cursor="pointer").encode(
        x=x_encoding,
        y=y_encoding,
        tooltip=[
            alt.Tooltip("start_time:T", title="Date"),
            tooltip_value,
        ],
    ).add_params(hover)
    highlighted_point = base.mark_point(size=90, color=color).encode(
        x=x_encoding,
        y=y_encoding,
        opacity=alt.condition(hover, alt.value(1), alt.value(0)),
    )
    guide_base = alt.Chart(guide_data) if guide_data is not None else base
    guide = guide_base.mark_rule(color="#888", strokeDash=[4, 3]).encode(
        x=x_encoding,
    ).transform_filter(hover)
    layers.extend([selector, highlighted_point, guide])
    return alt.layer(*layers).properties(height=180)


PACE_AXIS_LABEL = "floor(round(datum.value * 60) / 60) + ':' + (round(datum.value * 60) % 60 < 10 ? '0' : '') + (round(datum.value * 60) % 60)"

st.set_page_config(page_title="Garmin Running Progress", page_icon="🏃", layout="wide")
st.title("Garmin Running Progress")
st.caption("Track running pace and heart rate over time")

if not CSV_PATH.exists():
    st.info("No run data yet. Set up your Garmin Personal API key, then run `garmin-runs sync`.")
    st.stop()

data = pd.read_csv(CSV_PATH)
if data.empty:
    st.info("The activity CSV is empty. Run `garmin-runs sync` to import your runs.")
    st.stop()

for column in ("averageSpeed", "maxSpeed", "average_pace_min_per_km", "max_pace_min_per_km"):
    if column not in data:
        data[column] = pd.NA

data["start_time"] = pd.to_datetime(data["start_time"], errors="coerce")
data = data.dropna(subset=["start_time"]).sort_values("start_time")
for column in ("distance_km", "duration_seconds", "averageSpeed", "maxSpeed", "average_pace_min_per_km", "max_pace_min_per_km", "average_hr_bpm", "max_hr_bpm"):
    data[column] = pd.to_numeric(data[column], errors="coerce")
if data.empty:
    st.warning("No valid activity dates were found in the CSV.")
    st.stop()

total_km = data["distance_km"].sum()
run_count = len(data)
latest = data.iloc[-1]

metric_columns = st.columns(4)
metric_columns[0].metric("Runs", f"{run_count}")
metric_columns[1].metric("Total distance", f"{total_km:.1f} km")
metric_columns[2].metric("Latest average pace", format_pace(latest["average_pace_min_per_km"]) if pd.notna(latest["average_pace_min_per_km"]) else "—")
metric_columns[3].metric("Pace at max speed", format_pace(latest["max_pace_min_per_km"]) if pd.notna(latest["max_pace_min_per_km"]) else "—")

st.subheader("Pace and heart rate over time")
st.caption("Activities are ordered by date. Lower pace means faster running; dashed lines show linear trends.")
pace_data = data.dropna(subset=["average_pace_min_per_km"]).copy()
pace_data["Pace label"] = pace_data["average_pace_min_per_km"].map(format_pace)
hr_data = data.dropna(subset=["average_hr_bpm"]).copy()
shared_hover = alt.selection_point(
    name="run_hover",
    nearest=True,
    on="pointermove",
    fields=["start_time"],
    encodings=["x"],
    empty=False,
    resolve="global",
)

pace_hr_columns = st.columns(2)
with pace_hr_columns[0]:
    pace_start_default = max(0.0, floor(pace_data["average_pace_min_per_km"].min()) - 1) if not pace_data.empty else 0.0
    pace_start_text = st.text_input(
        "Pace y-axis starts at (m:ss min/km)",
        value=format_pace(pace_start_default).removesuffix(" min/km"),
        help="Enter minutes:seconds, for example 7:30. Runs with a slower pace may be clipped.",
    )
    pace_y_start = parse_pace(pace_start_text)
    if pace_y_start is None or pace_y_start > 100:
        st.error("Enter pace as minutes:seconds, such as 7:30.")
        pace_y_start = float(pace_start_default)
with pace_hr_columns[1]:
    hr_start_default = max(0, floor(hr_data["average_hr_bpm"].min() / 10) * 10 - 10) if not hr_data.empty else 0
    hr_y_start = st.number_input(
        "Heart-rate y-axis starts at (bpm)",
        min_value=0,
        max_value=300,
        value=int(hr_start_default),
        step=5,
        help="Runs with a lower heart rate than this value may be clipped from the chart.",
    )

pace_chart = make_hover_chart(
    pace_data,
    "average_pace_min_per_km",
    alt.Y(
        "average_pace_min_per_km:Q",
        title="Average pace (min/km)",
        axis=alt.Axis(labelExpr=PACE_AXIS_LABEL),
        scale=alt.Scale(domainMin=pace_y_start),
    ),
    alt.X("start_time:T", title=None, axis=alt.Axis(labels=False, ticks=False)),
    "#4c78a8",
    "Average pace (min/km)",
    ".2f",
    shared_hover,
    "Pace label",
    data,
)

hr_chart = make_hover_chart(
    hr_data,
    "average_hr_bpm",
    alt.Y("average_hr_bpm:Q", title="Average heart rate (bpm)", scale=alt.Scale(domainMin=hr_y_start)),
    alt.X("start_time:T", title="Run date", axis=alt.Axis(format="%b %d", labelAngle=-45)),
    "#e45756",
    "Average heart rate (bpm)",
    ".0f",
    shared_hover,
    guide_data=data,
)

st.altair_chart(
    alt.vconcat(pace_chart, hr_chart)
    .resolve_scale(x="shared", y="independent"),
    use_container_width=True,
)

st.subheader("Weekly running volume")
weekly = data.set_index("start_time")["distance_km"].resample("W-MON").sum().rename("Distance (km)")
st.bar_chart(weekly)

st.subheader("Recent runs")
display = data.sort_values("start_time", ascending=False).head(20).copy()
display["start_time"] = display["start_time"].dt.strftime("%Y-%m-%d")
display["average_pace_min_per_km"] = display["average_pace_min_per_km"].map(
    lambda pace: format_pace(pace) if pd.notna(pace) else "—"
)
display["max_pace_min_per_km"] = display["max_pace_min_per_km"].map(
    lambda pace: format_pace(pace) if pd.notna(pace) else "—"
)
st.dataframe(
    display[["start_time", "activity_name", "distance_km", "average_pace_min_per_km", "max_pace_min_per_km", "average_hr_bpm", "max_hr_bpm"]],
    hide_index=True,
    use_container_width=True,
)
