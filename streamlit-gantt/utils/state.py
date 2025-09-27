"""Session state helpers for undo/redo and persistent data."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List

import pandas as pd
import streamlit as st

DEFAULT_SETTINGS = {
    "show_today": True,
    "grid_mode": "week",  # week|day
    "zoom": "month",  # week|month|quarter
}

HISTORY_LIMIT = 20


@dataclass
class AppState:
    projects_df: pd.DataFrame
    segments_df: pd.DataFrame
    filters: Dict[str, str | list | None] = field(default_factory=dict)
    settings: Dict[str, str | bool] = field(default_factory=lambda: DEFAULT_SETTINGS.copy())
    history: Deque[tuple[pd.DataFrame, pd.DataFrame]] = field(
        default_factory=lambda: deque(maxlen=HISTORY_LIMIT)
    )
    future: Deque[tuple[pd.DataFrame, pd.DataFrame]] = field(
        default_factory=lambda: deque(maxlen=HISTORY_LIMIT)
    )


STATE_KEY = "gantt_app_state"


def init_state(projects_df: pd.DataFrame, segments_df: pd.DataFrame) -> AppState:
    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = AppState(projects_df=projects_df, segments_df=segments_df)
    return st.session_state[STATE_KEY]


def get_state() -> AppState:
    return st.session_state[STATE_KEY]


def push_history(state: AppState) -> None:
    state.history.append((state.projects_df.copy(), state.segments_df.copy()))
    state.future.clear()


def undo(state: AppState) -> None:
    if not state.history:
        st.toast("元に戻せる操作がありません")
        return
    state.future.appendleft((state.projects_df.copy(), state.segments_df.copy()))
    prev_projects, prev_segments = state.history.pop()
    state.projects_df = prev_projects
    state.segments_df = prev_segments


def redo(state: AppState) -> None:
    if not state.future:
        st.toast("やり直せる操作がありません")
        return
    state.history.append((state.projects_df.copy(), state.segments_df.copy()))
    next_projects, next_segments = state.future.popleft()
    state.projects_df = next_projects
    state.segments_df = next_segments


def update_data(state: AppState, projects_df: pd.DataFrame, segments_df: pd.DataFrame) -> None:
    push_history(state)
    state.projects_df = projects_df
    state.segments_df = segments_df


__all__ = [
    "AppState",
    "DEFAULT_SETTINGS",
    "HISTORY_LIMIT",
    "STATE_KEY",
    "get_state",
    "init_state",
    "redo",
    "undo",
    "update_data",
]
