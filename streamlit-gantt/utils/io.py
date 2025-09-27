"""I/O helpers for CSV/JSON import and export."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO, IOBase
from typing import Dict

import pandas as pd
import streamlit as st

REQUIRED_COLUMNS = [
    "name",
    "client",
    "site",
    "work_type",
    "owner",
    "progress",
    "start_date",
    "end_date",
]


@dataclass
class ImportResult:
    projects_df: pd.DataFrame
    segments_df: pd.DataFrame


def _normalize_columns(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    renamed = df.rename(columns=mapping)
    missing = [col for col in REQUIRED_COLUMNS if col not in renamed.columns]
    if missing:
        raise ValueError(f"必要な列が不足しています: {', '.join(missing)}")
    return renamed[REQUIRED_COLUMNS]


def _generate_segments(projects: pd.DataFrame) -> pd.DataFrame:
    segments = projects.reset_index(drop=True).assign(
        project_id=lambda d: d.index.astype(str),
        label="メイン工期",
        segment_id=lambda d: d.index.astype(str) + "-main",
    )[["segment_id", "project_id", "label", "start_date", "end_date"]]
    return segments


def load_projects_csv(buffer: BytesIO | IOBase, mapping: Dict[str, str] | None = None) -> ImportResult:
    df = pd.read_csv(buffer)
    if mapping:
        df = _normalize_columns(df, mapping)
    segments = _generate_segments(df)
    return ImportResult(projects_df=df, segments_df=segments)


def load_projects_json(buffer: BytesIO | IOBase, mapping: Dict[str, str] | None = None) -> ImportResult:
    df = pd.read_json(buffer)
    if mapping:
        df = _normalize_columns(df, mapping)
    segments = _generate_segments(df)
    return ImportResult(projects_df=df, segments_df=segments)


def export_dataframe(df: pd.DataFrame, fmt: str) -> bytes:
    if fmt == "csv":
        return df.to_csv(index=False).encode("utf-8-sig")
    if fmt == "json":
        return df.to_json(orient="records", force_ascii=False, date_format="iso").encode("utf-8")
    raise ValueError("サポートされていない形式です")


def notify_error(message: str) -> None:
    st.error(message, icon="⚠️")


def toast(message: str) -> None:
    st.toast(message)


def ensure_directory(path) -> None:
    path.mkdir(parents=True, exist_ok=True)


__all__ = [
    "ImportResult",
    "ensure_directory",
    "export_dataframe",
    "load_projects_csv",
    "load_projects_json",
    "notify_error",
    "toast",
]
