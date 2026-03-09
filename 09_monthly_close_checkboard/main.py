"""月次決算 チェックボード の分析ロジック。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

APP_TITLE = "月次決算 チェックボード"
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
RESULT_FILENAME = "monthly_close_report.csv"
TODAY = pd.Timestamp(date.today())


def load_data(filepath: Path) -> pd.DataFrame:
    """CSV を読み込み、基本的な型変換を行う。"""
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df["期限日"] = pd.to_datetime(df["期限日"])
    df["完了日"] = pd.to_datetime(df["完了日"], errors="coerce")

    return df


def analyze(filepath: Path) -> pd.DataFrame:
    """CSV を分析して、画面表示向けの DataFrame を返す。"""
    df = load_data(filepath)
    result = df.copy()
    result["遅延日数"] = result.apply(
        lambda row: (row["完了日"] - row["期限日"]).days if pd.notna(row["完了日"]) else (TODAY - row["期限日"]).days,
        axis=1,
    )

    def status(row: pd.Series) -> str:
        if pd.notna(row["完了日"]) and row["遅延日数"] > 0:
            return "遅延完了"
        if pd.notna(row["完了日"]):
            return "完了"
        if row["遅延日数"] > 0:
            return "未完了(遅延)"
        return "進行中"

    result["状況"] = result.apply(status, axis=1)
    order = {"未完了(遅延)": 0, "遅延完了": 1, "進行中": 2, "完了": 3}
    result = result.sort_values("状況", key=lambda s: s.map(order))

    return result.reset_index(drop=True)


def get_summary(df: pd.DataFrame) -> dict[str, str]:
    """サマリー表示用の辞書を返す。"""
    return {
        "タスク数": f"{len(df)} 件",
        "完了率": f"{(df['状況'].isin(['完了', '遅延完了']).mean() * 100):.0f} %",
        "遅延中": f"{(df['状況'] == '未完了(遅延)').sum()} 件",
        "高優先度未完了": f"{len(df[(df['優先度'] == '高') & (~df['状況'].isin(['完了', '遅延完了']))])} 件",
    }



def get_chart_data(df: pd.DataFrame) -> dict[str, object]:
    """グラフ描画用のデータを返す。"""
    counts = df["状況"].value_counts().reindex(["完了", "遅延完了", "進行中", "未完了(遅延)"]).fillna(0)
    return {
        "kind": "pie",
        "labels": counts.index.tolist(),
        "values": counts.tolist(),
        "title": "月次決算タスク状況",
    }



def save_results(df: pd.DataFrame) -> Path:
    """結果を CSV に保存する。"""
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / RESULT_FILENAME
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    """サンプルデータの既定パスを返す。"""
    return DATA_DIR / "monthly_close.csv"
