"""Plotly Gantt chart builder."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

import numpy as np
import pandas as pd

PLOTLY_IMPORT_ERROR: str | None = None

try:  # pragma: no cover - optional dependency import
    import plotly.express as px
    import plotly.graph_objects as go
except ModuleNotFoundError as exc:  # pragma: no cover - executed when Plotly is missing
    px = None  # type: ignore[assignment]
    go = None  # type: ignore[assignment]
    PLOTLY_IMPORT_ERROR = str(exc)

from utils.dates import make_month_annotations, make_tickvals, make_week_lines

DEFAULT_COLOR = "#f97316"
PROGRESS_COLORS = {
    "予定": "#f59e0b",  # amber
    "進行": "#f97316",  # orange
    "完了": "#22c55e",  # green
}


def build_gantt_dataframe(
    projects_df: pd.DataFrame,
    segments_df: pd.DataFrame,
    view_start: datetime,
    view_end: datetime,
) -> pd.DataFrame:
    """Prepare dataframe for gantt drawing."""

    merged = segments_df.merge(
        projects_df,
        left_on="project_id",
        right_on="id",
        how="left",
        suffixes=("_segment", ""),
    )
    merged["color"] = merged["color"].fillna(DEFAULT_COLOR)

    merged["start"] = pd.to_datetime(merged["start_date"])
    merged["end"] = pd.to_datetime(merged["end_date"])

    merged["start"] = merged["start"].clip(lower=view_start)
    merged["end"] = merged["end"].clip(upper=view_end)

    merged = merged[(merged["end"] >= view_start) & (merged["start"] <= view_end)]
    merged.sort_values(["project_id", "start"], inplace=True)
    merged["row"] = merged.groupby("project_id").cumcount()
    merged["display_name"] = merged["name"] + " / " + merged["label"]
    return merged


def _ensure_plotly_modules() -> tuple[Any, Any]:
    """Return Plotly modules or raise a helpful error when unavailable."""

    if go is None or px is None:
        raise ModuleNotFoundError(
            "Plotly is required to render the gantt chart. "
            "Install the optional dependencies with `pip install -r requirements.txt`."
        )
    return go, px


def build_gantt_figure(
    projects_df: pd.DataFrame,
    segments_df: pd.DataFrame,
    view_start: datetime,
    view_end: datetime,
    settings: dict,
    selected_ids: Iterable[str] | None = None,
) -> go.Figure:
    """Create a Plotly figure with custom annotations and grid lines."""

    go_module, px_module = _ensure_plotly_modules()
    selected_ids = set(selected_ids or [])

    data = build_gantt_dataframe(projects_df, segments_df, view_start, view_end)
    if data.empty:
        fig = go_module.Figure()
        fig.update_layout(
            title="表示対象のデータがありません",
            xaxis=dict(title="期間", type="date"),
            yaxis=dict(title="案件"),
        )
        return fig

    data["opacity"] = np.where(data["project_id"].isin(selected_ids), 1.0, 0.7)

    fig = px_module.timeline(
        data,
        x_start="start",
        x_end="end",
        y="name",
        color="progress",
        color_discrete_map=PROGRESS_COLORS,
        custom_data=["segment_id", "project_id", "label"],
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>区間: %{customdata[2]}<br>"
            "開始: %{x|%Y-%m-%d}<br>終了: %{x_end|%Y-%m-%d}<extra></extra>"
        ),
        marker=dict(opacity=data["opacity"]),
    )

    zoom = settings.get("zoom", "month")
    if zoom == "week":
        dtick = 7 * 24 * 60 * 60 * 1000
    elif zoom == "quarter":
        dtick = "M3"
    else:
        dtick = "M1"

    fig.update_layout(
        barmode="overlay",
        bargap=0.2,
        title="",
        showlegend=True,
        legend_title="進捗",
        xaxis=dict(type="date", dtick=dtick),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=10, t=30, b=40),
        hoverlabel=dict(bgcolor="rgba(0,0,0,0.75)", font=dict(color="white")),
    )

    tickvals = make_tickvals(view_start, view_end)
    fig.update_xaxes(tickvals=tickvals, tickformat="%d", tickfont=dict(size=11))

    if settings.get("grid_mode") == "day":
        days = pd.date_range(view_start, view_end, freq="D")
        for day in days:
            fig.add_vline(x=day, line_color="rgba(150,150,150,0.15)", line_width=1)
    else:
        for line in make_week_lines(view_start, view_end):
            fig.add_vline(x=line, line_color="rgba(120,120,120,0.2)", line_width=1)

    months = make_month_annotations(view_start, view_end)
    for label, midpoint in months:
        month_start = datetime(midpoint.year, midpoint.month, 1)
        fig.add_vline(x=month_start, line_color="rgba(0,0,0,0.25)", line_width=2)
        fig.add_annotation(
            x=midpoint,
            y=1.02,
            xref="x",
            yref="paper",
            text=label,
            showarrow=False,
            font=dict(size=12, color="#111"),
        )

    if settings.get("show_today"):
        today = datetime.now()
        if view_start <= today <= view_end:
            fig.add_vline(x=today, line_color="#ef4444", line_width=2, line_dash="dash")
            fig.add_annotation(
                x=today,
                y=1.05,
                xref="x",
                yref="paper",
                text="今日",
                font=dict(color="#ef4444"),
                showarrow=False,
            )

    fig.update_yaxes(title="")
    fig.update_xaxes(range=[view_start, view_end])

    return fig


__all__ = [
    "build_gantt_figure",
    "build_gantt_dataframe",
    "DEFAULT_COLOR",
    "PROGRESS_COLORS",
    "PLOTLY_IMPORT_ERROR",
]
