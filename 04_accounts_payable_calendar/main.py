"""支払予定カレンダーツール の分析ロジック。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

APP_TITLE = "支払予定カレンダーツール"
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
RESULT_FILENAME = "payable_calendar_report.csv"
TODAY = pd.Timestamp(date.today())


def load_data(filepath: Path) -> pd.DataFrame:
    """CSV を読み込み、基本的な型変換を行う。"""
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df["請求日"] = pd.to_datetime(df["請求日"])
    df["支払予定日"] = pd.to_datetime(df["支払予定日"])
    df["金額"] = pd.to_numeric(df["金額"], errors="coerce").fillna(0.0)

    return df


def analyze(filepath: Path) -> pd.DataFrame:
    """CSV を分析して、画面表示向けの DataFrame を返す。"""
    df = load_data(filepath)
    result = df.copy()
    result["残日数"] = (result["支払予定日"] - TODAY).dt.days

    def judge(row: pd.Series) -> str:
        if row["支払状況"] == "支払済":
            return "完了"
        if row["残日数"] < 0:
            return "期限超過"
        if row["残日数"] <= 7:
            return "直近"
        return "予定"

    result["状況"] = result.apply(judge, axis=1)
    result = result.sort_values(["支払予定日", "金額"], ascending=[True, False])

    return result.reset_index(drop=True)


def get_summary(df: pd.DataFrame) -> dict[str, str]:
    """サマリー表示用の辞書を返す。"""
    unpaid = df[df["支払状況"] != "支払済"]
    return {
        "未払件数": f"{len(unpaid)} 件",
        "未払総額": f"{unpaid['金額'].sum():,.0f} 円",
        "7日以内": f"{(df['状況'] == '直近').sum()} 件",
        "期限超過": f"{(df['状況'] == '期限超過').sum()} 件",
    }



def get_chart_data(df: pd.DataFrame) -> dict[str, object]:
    """グラフ描画用のデータを返す。"""
    daily = (
        df[df["支払状況"] != "支払済"]
        .groupby(df["支払予定日"].dt.strftime("%m/%d"))["金額"]
        .sum()
        .reset_index()
    )
    return {
        "kind": "line",
        "labels": daily["支払予定日"].tolist(),
        "values": daily["金額"].tolist(),
        "ylabel": "支払予定額（円）",
        "title": "日別 支払予定額",
        "line_color": "#d9534f",
    }



def save_results(df: pd.DataFrame) -> Path:
    """結果を CSV に保存する。"""
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / RESULT_FILENAME
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    """サンプルデータの既定パスを返す。"""
    return DATA_DIR / "payables.csv"
