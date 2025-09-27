"""Segment editor shown when a bar is clicked."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from utils.dates import to_date
from utils.state import AppState, push_history


def _get_segment_row(state: AppState, segment_id: str) -> pd.Series | None:
    matches = state.segments_df[state.segments_df["segment_id"] == segment_id]
    if matches.empty:
        return None
    return matches.iloc[0]


def render_editor(state: AppState, selected_segment_id: str | None) -> None:
    st.subheader("セグメント編集")
    if not selected_segment_id:
        st.info("ガントチャートのバーをクリックすると編集できます")
        return

    row = _get_segment_row(state, selected_segment_id)
    if row is None:
        st.warning("選択されたセグメントが見つかりませんでした")
        return

    project = state.projects_df[state.projects_df["id"] == row["project_id"]].iloc[0]

    st.markdown(f"**案件:** {project['name']}")

    with st.form(f"segment_form_{selected_segment_id}"):
        label = st.text_input("区間名", value=row["label"])
        start_date = st.date_input("開始日", value=to_date(str(row["start_date"])) )
        end_date = st.date_input("終了日", value=to_date(str(row["end_date"])) )
        progress = st.selectbox("進捗", options=["予定", "進行", "完了"], index=["予定", "進行", "完了"].index(project["progress"]))
        note = st.text_area("メモ", value=project.get("note", ""))

        submitted = st.form_submit_button("保存")

    if submitted:
        if end_date < start_date:
            st.error("終了日は開始日以降に設定してください")
            return
        push_history(state)
        state.segments_df.loc[state.segments_df["segment_id"] == selected_segment_id, ["label", "start_date", "end_date"]] = [
            label,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
        ]
        state.projects_df.loc[state.projects_df["id"] == project["id"], ["progress", "note"]] = [progress, note]
        st.success("更新しました")


__all__ = ["render_editor"]
