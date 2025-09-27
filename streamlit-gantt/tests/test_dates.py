from datetime import date, datetime

import pytest

from utils.dates import clip_segment_to_range, make_tickvals


def test_make_tickvals_includes_defined_days():
    start = date(2025, 7, 1)
    end = date(2025, 7, 31)
    ticks = make_tickvals(start, end)
    expected_days = {6, 12, 18, 24, 31}
    actual_days = {tick.day for tick in ticks}
    assert expected_days == actual_days


def test_clip_segment_inside_range():
    segment = clip_segment_to_range("1", "A", "2025-07-01", "2025-07-31", "2025-07-10", "2025-07-20")
    assert segment is not None
    assert segment.start.date() == date(2025, 7, 10)
    assert segment.end.date() == date(2025, 7, 20)


def test_clip_segment_outside_range_returns_none():
    segment = clip_segment_to_range("1", "A", "2025-07-01", "2025-07-05", "2025-07-10", "2025-07-20")
    assert segment is None


def test_clip_segment_invalid_range():
    with pytest.raises(ValueError):
        clip_segment_to_range("1", "A", "2025-07-10", "2025-07-01", "2025-07-01", "2025-07-31")
