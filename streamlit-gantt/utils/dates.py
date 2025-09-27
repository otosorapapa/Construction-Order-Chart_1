"""Utility helpers for date calculations and timeline rendering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, List, Sequence, Tuple, TYPE_CHECKING

try:  # pragma: no cover - optional dependency setup
    import pandas as pd  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback when pandas missing
    pd = None  # type: ignore

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd  # noqa: F401

DateLike = date | datetime | str


def to_date(value: DateLike) -> date:
    """Coerce a value into a ``date`` object."""

    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return datetime.fromisoformat(value).date()
    raise TypeError(f"Unsupported date value: {value!r}")


def month_range(start: DateLike, end: DateLike) -> List[Tuple[date, date]]:
    """Return a list of ``(month_start, month_end)`` tuples covering the span."""

    current = to_date(start).replace(day=1)
    last = to_date(end)
    months: List[Tuple[date, date]] = []
    while current <= last:
        next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_end = min(next_month - timedelta(days=1), last)
        months.append((current, month_end))
        current = next_month
    return months


def make_tickvals(start: DateLike, end: DateLike) -> List[datetime]:
    """Return tick positions for 6/12/18/24/last day of each month."""

    ticks: List[datetime] = []
    for month_start, month_end in month_range(start, end):
        for day in (6, 12, 18, 24):
            if day <= month_end.day:
                tick_date = month_start.replace(day=day)
                if month_start <= tick_date <= month_end:
                    ticks.append(datetime.combine(tick_date, datetime.min.time()))
        ticks.append(datetime.combine(month_end, datetime.min.time()))
    return [tick for tick in ticks if to_date(start) <= tick.date() <= to_date(end)]


def make_month_annotations(start: DateLike, end: DateLike) -> List[Tuple[str, datetime]]:
    """Return ``(label, midpoint_datetime)`` for each month in range."""

    annotations: List[Tuple[str, datetime]] = []
    for month_start, month_end in month_range(start, end):
        label = f"{month_start.year}年{month_start.month}月"
        midpoint = month_start + (month_end - month_start) / 2
        annotations.append((label, datetime.combine(midpoint, datetime.min.time())))
    return annotations


def make_week_lines(start: DateLike, end: DateLike) -> List[datetime]:
    """Return Monday based weekly grid lines."""

    start_date = to_date(start)
    aligned_start = start_date - timedelta(days=start_date.weekday())
    end_date = to_date(end)
    lines: List[datetime] = []
    current = aligned_start
    while current <= end_date:
        lines.append(datetime.combine(current, datetime.min.time()))
        current += timedelta(days=7)
    return lines


@dataclass
class ClippedSegment:
    project_id: str
    label: str
    start: datetime
    end: datetime


def clip_segment_to_range(
    project_id: str,
    label: str,
    start: DateLike,
    end: DateLike,
    view_start: DateLike,
    view_end: DateLike,
) -> ClippedSegment | None:
    """Clip a segment to the visible range. Returns ``None`` when no overlap."""

    start_dt = datetime.combine(to_date(start), datetime.min.time())
    end_dt = datetime.combine(to_date(end), datetime.min.time())
    if end_dt < start_dt:
        raise ValueError("end_date must be greater than or equal to start_date")

    view_start_dt = datetime.combine(to_date(view_start), datetime.min.time())
    view_end_dt = datetime.combine(to_date(view_end), datetime.min.time())

    if end_dt < view_start_dt or start_dt > view_end_dt:
        return None
    clipped_start = max(start_dt, view_start_dt)
    clipped_end = min(end_dt, view_end_dt)
    return ClippedSegment(project_id, label, clipped_start, clipped_end)


def to_dataframe_dates(df: "pd.DataFrame", columns: Sequence[str]) -> "pd.DataFrame":
    if pd is None:  # pragma: no cover - environment without pandas
        raise ImportError("pandas is required for to_dataframe_dates")
    converted = df.copy()
    for col in columns:
        converted[col] = pd.to_datetime(converted[col], format="%Y-%m-%d", errors="raise")
    return converted


def business_days(start: DateLike, end: DateLike) -> int:
    start_date = to_date(start)
    end_date = to_date(end)
    if end_date < start_date:
        raise ValueError("end_date must be greater than or equal to start_date")
    try:
        import numpy as np

        return int(np.busday_count(start_date, end_date + timedelta(days=1)))
    except Exception:  # pragma: no cover - fallback for numpy missing
        if pd is None:
            raise ImportError("pandas or numpy is required for business_days")
        days = pd.bdate_range(start_date, end_date)
        return len(days)


__all__ = [
    "ClippedSegment",
    "business_days",
    "clip_segment_to_range",
    "make_month_annotations",
    "make_tickvals",
    "make_week_lines",
    "month_range",
    "to_date",
    "to_dataframe_dates",
]
