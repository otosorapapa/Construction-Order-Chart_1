"""Utility helpers for optional dependency imports."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any, Callable, Iterable

PLOTLY_INSTALL_INSTRUCTIONS = (
    "Plotly 関連のライブラリが見つかりません。\n"
    "アプリを利用するには以下のコマンドのいずれかを実行して必要な依存関係をインストールしてください。\n"
    "  - `pip install -r requirements.txt` (streamlit-gantt ディレクトリで実行)\n"
    "  - `pip install -r streamlit-gantt/requirements.txt` (リポジトリルートで実行)"
)


def _load_modules(names: Iterable[str]) -> tuple[dict[str, ModuleType] | None, str | None]:
    """Attempt to import modules, returning the first error message when missing."""

    loaded: dict[str, ModuleType] = {}
    for name in names:
        try:
            loaded[name] = import_module(name)
        except ModuleNotFoundError as exc:  # pragma: no cover - depends on environment
            return None, str(exc)
    return loaded, None


def format_plotly_error(details: str) -> str:
    """Return a user-friendly error message for missing Plotly dependencies."""

    return f"{PLOTLY_INSTALL_INSTRUCTIONS}\n\n詳細: {details}"


def import_plotly_core() -> tuple[Any, Any]:
    """Import the core Plotly modules required for chart rendering."""

    modules, error = _load_modules(["plotly.graph_objects", "plotly.express"])
    if error is not None:  # pragma: no cover - depends on environment
        raise ModuleNotFoundError(format_plotly_error(error)) from None
    return modules["plotly.graph_objects"], modules["plotly.express"]


def import_plotly_streamlit_runtime() -> tuple[Any, Callable[..., Any]]:
    """Import Plotly helpers used by the Streamlit front-end."""

    modules, error = _load_modules(["plotly.io", "streamlit_plotly_events"])
    if error is not None:  # pragma: no cover - depends on environment
        raise ModuleNotFoundError(format_plotly_error(error)) from None

    pio = modules["plotly.io"]
    events_module = modules["streamlit_plotly_events"]
    return pio, events_module.plotly_events


__all__ = [
    "PLOTLY_INSTALL_INSTRUCTIONS",
    "format_plotly_error",
    "import_plotly_core",
    "import_plotly_streamlit_runtime",
]
