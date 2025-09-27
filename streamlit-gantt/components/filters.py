"""Sidebar filters and import/export tools."""

from __future__ import annotations

from datetime import date, datetime
from io import BytesIO
from typing import Dict, Iterable, Tuple

import pandas as pd
import streamlit as st

from utils import io
from utils.state import AppState, update_data

DEFAULT_FROM = date(2025, 7, 1)
DEFAULT_TO = date(2026, 6, 30)


def _render_mapping_ui(columns: Iterable[str]) -> Dict[str, str] | None:
    st.write("### カラムマッピング")
    st.caption("インポートするファイルの列を選択してください")
    mapping: Dict[str, str] = {}
    for target in io.REQUIRED_COLUMNS:
        mapping[target] = st.selectbox(
            f"{target}",
            options=["選択しない", *columns],
            index=columns.index(target) + 1 if target in columns else 0,
            key=f"mapping_{target}",
        )
    if any(value == "選択しない" for value in mapping.values()):
        st.info("すべての列をマッピングするとインポートできます")
        return None
    normalized = {k: v for k, v in mapping.items() if v != "選択しない"}
    return normalized


def render_sidebar(state: AppState) -> Tuple[pd.DataFrame, pd.DataFrame, datetime, datetime, Dict[str, str | bool]]:
    with st.sidebar:
        st.title("案件フィルタ")
        st.markdown("期間・キーワード・属性で絞り込みできます。")

        view_range = st.date_input(
            "表示期間",
            value=(DEFAULT_FROM, DEFAULT_TO),
            min_value=date(2024, 1, 1),
            max_value=date(2027, 12, 31),
        )
        if isinstance(view_range, tuple):
            view_start, view_end = view_range
        else:
            view_start, view_end = DEFAULT_FROM, DEFAULT_TO

        search = st.text_input("検索（案件名/顧客/現場/担当）", value=state.filters.get("search", ""))
        work_types = st.multiselect(
            "工種", options=sorted(state.projects_df["work_type"].unique()), default=state.filters.get("work_type", [])
        )
        progresses = st.multiselect(
            "進捗", options=["予定", "進行", "完了"], default=state.filters.get("progress", [])
        )
        owners = st.multiselect(
            "担当", options=sorted(state.projects_df["owner"].unique()), default=state.filters.get("owner", [])
        )

        st.markdown("---")
        st.subheader("データ入出力")
        uploaded = st.file_uploader("CSV/JSON インポート", type=["csv", "json"], accept_multiple_files=False)
        if uploaded is not None:
            content = uploaded.getvalue()
            try:
                if uploaded.type == "text/csv":
                    df = pd.read_csv(BytesIO(content))
                else:
                    df = pd.read_json(BytesIO(content))
                mapping = None
                if set(df.columns) != set(io.REQUIRED_COLUMNS):
                    mapping = _render_mapping_ui(df.columns)
                if mapping is None and set(df.columns) != set(io.REQUIRED_COLUMNS):
                    st.stop()
                if uploaded.type == "text/csv":
                    result = io.load_projects_csv(BytesIO(content), mapping)
                else:
                    result = io.load_projects_json(BytesIO(content), mapping)
                projects = result.projects_df.reset_index(drop=True).assign(id=lambda d: d.index.astype(str))
                segments = result.segments_df.copy()
                segments["project_id"] = segments["project_id"].astype(str)
                update_data(state, projects, segments)
                io.toast("インポートが完了しました")
            except Exception as exc:  # noqa: BLE001
                io.notify_error(str(exc))

        col1, col2 = st.columns(2)
        with col1:
            if st.download_button(
                "CSVエクスポート", io.export_dataframe(state.projects_df, "csv"), file_name="projects.csv"
            ):
                io.toast("CSVを出力しました")
        with col2:
            if st.download_button(
                "JSONエクスポート", io.export_dataframe(state.projects_df, "json"), file_name="projects.json"
            ):
                io.toast("JSONを出力しました")

        st.markdown("---")
        st.subheader("表示設定")
        grid_mode = st.radio("グリッド", options=["week", "day"], format_func=lambda x: "週" if x == "week" else "日")
        show_today = st.checkbox("今日のラインを表示", value=state.settings.get("show_today", True))
        zoom = st.radio(
            "ズーム",
            options=["week", "month", "quarter"],
            index=["week", "month", "quarter"].index(state.settings.get("zoom", "month")),
            horizontal=True,
        )

    filters = {
        "search": search,
        "work_type": work_types,
        "progress": progresses,
        "owner": owners,
    }
    state.filters = filters
    state.settings.update({"grid_mode": grid_mode, "show_today": show_today, "zoom": zoom})

    projects_df = state.projects_df.copy()
    segments_df = state.segments_df.copy()

    if search:
        mask = (
            projects_df["name"].str.contains(search, case=False)
            | projects_df["client"].str.contains(search, case=False)
            | projects_df["site"].str.contains(search, case=False)
            | projects_df["owner"].str.contains(search, case=False)
        )
        projects_df = projects_df[mask]
    if work_types:
        projects_df = projects_df[projects_df["work_type"].isin(work_types)]
    if progresses:
        projects_df = projects_df[projects_df["progress"].isin(progresses)]
    if owners:
        projects_df = projects_df[projects_df["owner"].isin(owners)]

    filtered_segments = segments_df[segments_df["project_id"].isin(projects_df["id"])]

    return (
        projects_df,
        filtered_segments,
        datetime.combine(view_start, datetime.min.time()),
        datetime.combine(view_end, datetime.min.time()),
        state.settings,
    )


__all__ = ["render_sidebar"]
