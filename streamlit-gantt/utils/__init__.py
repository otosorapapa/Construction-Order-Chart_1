"""Shared utilities."""

from __future__ import annotations

from typing import TypedDict


class Project(TypedDict, total=False):
    id: str
    name: str
    client: str
    site: str
    work_type: str
    owner: str
    progress: str
    note: str
    color: str


class Segment(TypedDict, total=False):
    segment_id: str
    project_id: str
    label: str
    start_date: str
    end_date: str


__all__ = ["Project", "Segment"]
