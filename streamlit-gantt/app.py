"""工事受注案件の予定表（ガントチャート）アプリ."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd
import streamlit as st

from components.editor import render_editor
from components.filters import render_sidebar
from utils import Segment
from utils.state import init_state, redo, undo

PLOTLY_IMPORT_ERROR: str | None = None

try:  # pragma: no cover - environment dependent import
    import plotly.io as pio
    from streamlit_plotly_events import plotly_events
except ModuleNotFoundError as exc:  # pragma: no cover - executed when optional deps missing
    pio = None  # type: ignore[assignment]
    plotly_events = None  # type: ignore[assignment]
    PLOTLY_IMPORT_ERROR = str(exc)

try:  # pragma: no cover - environment dependent import
    from components.gantt import (
        PLOTLY_IMPORT_ERROR as GANTT_PLOTLY_IMPORT_ERROR,
        build_gantt_figure,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - executed when optional deps missing
    build_gantt_figure = None  # type: ignore[assignment]
    PLOTLY_IMPORT_ERROR = str(exc)
else:  # pragma: no cover - executed when imports succeed
    if GANTT_PLOTLY_IMPORT_ERROR and not PLOTLY_IMPORT_ERROR:
        PLOTLY_IMPORT_ERROR = GANTT_PLOTLY_IMPORT_ERROR

DATA_DIR = Path(__file__).parent / "data"
DEFAULT_FILE = DATA_DIR / "sample_projects.csv"


st.set_page_config(page_title="工事受注案件ガントチャート", layout="wide")

if PLOTLY_IMPORT_ERROR:
    st.error(
        "Plotly 関連のライブラリが見つかりません。\n"
        "アプリを利用するには `pip install -r requirements.txt` を実行して"
        "必要な依存関係をインストールしてください。\n\n"
        f"詳細: {PLOTLY_IMPORT_ERROR}"
    )
    st.stop()


def _load_initial_projects() -> pd.DataFrame:
    df = pd.read_csv(DEFAULT_FILE)
    df = df.assign(id=lambda d: d.index.astype(str))
    if "note" not in df.columns:
        df["note"] = ""
    if "color" not in df.columns:
        df["color"] = ""
    return df


def _build_segments(projects: pd.DataFrame) -> pd.DataFrame:
    segments: List[Segment] = []
    for _, row in projects.iterrows():
        segments.append(
            {
                "segment_id": f"{row['id']}-main",
                "project_id": row["id"],
                "label": "基本工期",
                "start_date": row["start_date"],
                "end_date": row["end_date"],
            }
        )

    extra_segments = {
        "0": [
            ("基礎工", "2025-07-08", "2025-08-20"),
            ("建方", "2025-08-21", "2025-10-30"),
        ],
        "3": [
            ("配水池施工", "2025-09-01", "2025-11-30"),
            ("設備据付", "2025-12-01", "2026-01-15"),
        ],
        "5": [
            ("橋面補修", "2025-07-01", "2025-08-30"),
            ("舗装復旧", "2025-09-01", "2025-11-18"),
        ],
    }

    for project_id, segs in extra_segments.items():
        for order, (label, start, end) in enumerate(segs, start=1):
            segments.append(
                {
                    "segment_id": f"{project_id}-extra-{order}",
                    "project_id": project_id,
                    "label": label,
                    "start_date": start,
                    "end_date": end,
                }
            )

    segments_df = pd.DataFrame(segments).drop_duplicates(subset=["segment_id"], keep="last")
    return segments_df


@st.cache_data(show_spinner=False)
def load_initial_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    projects = _load_initial_projects()
    segments = _build_segments(projects)
    return projects, segments


projects_df, segments_df = load_initial_data()
state = init_state(projects_df, segments_df)

filtered_projects, filtered_segments, view_start, view_end, settings = render_sidebar(state)

st.title("工事受注案件の予定表")

left, right = st.columns([2, 1])

with left:
    st.markdown(
        "### 案件一覧"
        "\nチェックボックスで選択した案件がガントチャートで強調されます。"
    )

    if "selected_ids" not in st.session_state:
        st.session_state["selected_ids"] = []

    display_df = filtered_projects.copy()
    display_df = display_df.assign(選択=display_df["id"].isin(st.session_state["selected_ids"]))
    display_df_for_editor = display_df[["選択", "id", "name", "client", "site", "owner", "progress", "start_date", "end_date"]]
    edited_df = st.data_editor(
        display_df_for_editor,
        num_rows="fixed",
        hide_index=True,
        column_config={
            "選択": st.column_config.CheckboxColumn(help="ガント上で強調表示"),
            "id": st.column_config.TextColumn("ID", disabled=True, visible=False),
        },
        use_container_width=True,
        key="projects_editor",
    )

    selected_ids = edited_df.loc[edited_df["選択"], "id"].tolist()
    st.session_state["selected_ids"] = selected_ids

    st.markdown(
        f"**表示件数:** {len(filtered_projects)} 件 / **全体:** {len(state.projects_df)} 件"
    )
    st.caption(
        "Ctrl+Z / Ctrl+Y で Undo/Redo、テーブルで Enter で編集にフォーカスできます。"
    )

with right:
    st.markdown("### 履歴操作")
    undo_button, redo_button = st.columns(2)
    with undo_button:
        if st.button("元に戻す", use_container_width=True):
            undo(state)
    with redo_button:
        if st.button("やり直す", use_container_width=True):
            redo(state)

    render_editor(state, st.session_state.get("active_segment"))

with st.expander("出力・印刷ヒント", expanded=True):
    st.markdown(
        "- PNG ボタンで現在の表示範囲を画像保存できます。\n"
        "- PDF は PNG をブラウザ印刷で A3 横向き・余白小で出力するときれいです。"
    )

fig = build_gantt_figure(
    filtered_projects,
    filtered_segments,
    view_start,
    view_end,
    settings,
    selected_ids=st.session_state.get("selected_ids", []),
)

fig.update_layout(height=550)

col_chart, col_export = st.columns([4, 1])
with col_chart:
    st.markdown(
        f"#### ガントチャート\n表示期間: {view_start.date()} 〜 {view_end.date()}"
    )
    event = plotly_events(fig, click_event=True, hover_event=False, select_event=False, override_height=550)

with col_export:
    st.markdown("#### 出力")
    if st.button("PNG生成", use_container_width=True):
        try:
            png_bytes = pio.to_image(fig, format="png", engine="kaleido", width=1600, height=900, scale=2)
            st.download_button("PNGダウンロード", png_bytes, file_name="gantt.png")
        except Exception as exc:  # noqa: BLE001
            st.error(f"PNG 出力に失敗しました: {exc}")

if event:
    selected = event[0]
    segment_id = selected["customdata"][0]
    st.session_state["active_segment"] = segment_id
    st.experimental_rerun()

st.caption(
    "検索やフィルタ、CSV/JSON入出力、クリック編集を組み合わせて運用できます。"
)
