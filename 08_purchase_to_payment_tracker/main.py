"""発注〜支払 進捗トラッカーツール の分析ロジック。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

APP_TITLE = "発注〜支払 進捗トラッカーツール"
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
RESULT_FILENAME = "purchase_flow_report.csv"
TODAY = pd.Timestamp(date.today())


def load_data(filepath: Path) -> pd.DataFrame:
    """CSV を読み込み、基本的な型変換を行う。"""
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    for col in ["発注日", "検収日", "請求日", "支払日"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["金額"] = pd.to_numeric(df["金額"], errors="coerce").fillna(0.0)

    return df


def analyze(filepath: Path) -> pd.DataFrame:
    """CSV を分析して、画面表示向けの DataFrame を返す。"""
    df = load_data(filepath)
    result = df.copy()

    def stage(row: pd.Series) -> str:
        if pd.notna(row["支払日"]):
            return "支払完了"
        if pd.notna(row["請求日"]) and pd.notna(row["検収日"]):
            return "支払待ち"
        if pd.notna(row["請求日"]) and pd.isna(row["検収日"]):
            return "未検収請求"
        if pd.notna(row["検収日"]):
            return "請求待ち"
        return "発注済"

    result["進捗"] = result.apply(stage, axis=1)
    result["経過日数"] = (TODAY - result["発注日"]).dt.days
    result["要対応"] = result.apply(
        lambda row: "要確認" if row["進捗"] in ["未検収請求", "支払待ち"] and row["経過日数"] >= 10 else "通常",
        axis=1,
    )
    order = {"未検収請求": 0, "支払待ち": 1, "請求待ち": 2, "発注済": 3, "支払完了": 4}
    result = result.sort_values("進捗", key=lambda s: s.map(order))

    return result.reset_index(drop=True)


def get_summary(df: pd.DataFrame) -> dict[str, str]:
    """サマリー表示用の辞書を返す。"""
    return {
        "案件数": f"{len(df)} 件",
        "支払待ち": f"{(df['進捗'] == '支払待ち').sum()} 件",
        "未検収請求": f"{(df['進捗'] == '未検収請求').sum()} 件",
        "未払総額": f"{df.loc[df['進捗'] != '支払完了', '金額'].sum():,.0f} 円",
    }



def get_chart_data(df: pd.DataFrame) -> dict[str, object]:
    """グラフ描画用のデータを返す。"""
    counts = df["進捗"].value_counts().reindex(["発注済", "請求待ち", "未検収請求", "支払待ち", "支払完了"]).fillna(0)
    return {
        "kind": "bar",
        "labels": counts.index.tolist(),
        "values": counts.tolist(),
        "colors": ["#5bc0de", "#f0ad4e", "#d9534f", "#c9302c", "#5cb85c"],
        "ylabel": "件数",
        "title": "案件の進捗分布",
    }



def save_results(df: pd.DataFrame) -> Path:
    """結果を CSV に保存する。"""
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / RESULT_FILENAME
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    """サンプルデータの既定パスを返す。"""
    return DATA_DIR / "purchase_flow.csv"
