"""銀行明細 消込チェックツール の分析ロジック。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

APP_TITLE = "銀行明細 消込チェックツール"
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
RESULT_FILENAME = "bank_match_report.csv"
TODAY = pd.Timestamp(date.today())


def load_data(filepath: Path) -> pd.DataFrame:
    """CSV を読み込み、基本的な型変換を行う。"""
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df["日付"] = pd.to_datetime(df["日付"])
    for col in ["元帳金額", "銀行金額"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df


def analyze(filepath: Path) -> pd.DataFrame:
    """CSV を分析して、画面表示向けの DataFrame を返す。"""
    df = load_data(filepath)
    result = df.copy()
    result["差額"] = result["銀行金額"] - result["元帳金額"]

    def judge(row: pd.Series) -> str:
        if row["元帳金額"] == 0 or row["銀行金額"] == 0:
            return "未消込"
        if abs(row["差額"]) == 0:
            return "一致"
        if abs(row["差額"]) <= 200:
            return "要確認"
        return "不一致"

    result["消込状況"] = result.apply(judge, axis=1)
    order = {"不一致": 0, "未消込": 1, "要確認": 2, "一致": 3}
    result = result.sort_values("消込状況", key=lambda s: s.map(order))

    return result.reset_index(drop=True)


def get_summary(df: pd.DataFrame) -> dict[str, str]:
    """サマリー表示用の辞書を返す。"""
    return {
        "明細数": f"{len(df)} 件",
        "一致": f"{(df['消込状況'] == '一致').sum()} 件",
        "未消込": f"{(df['消込状況'] == '未消込').sum()} 件",
        "差額合計": f"{df['差額'].sum():,.0f} 円",
    }



def get_chart_data(df: pd.DataFrame) -> dict[str, object]:
    """グラフ描画用のデータを返す。"""
    counts = df["消込状況"].value_counts().reindex(["一致", "要確認", "未消込", "不一致"]).fillna(0)
    return {
        "kind": "bar",
        "labels": counts.index.tolist(),
        "values": counts.tolist(),
        "colors": ["#5cb85c", "#f0ad4e", "#d9534f", "#8b0000"],
        "ylabel": "件数",
        "title": "消込状況 件数",
    }



def save_results(df: pd.DataFrame) -> Path:
    """結果を CSV に保存する。"""
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / RESULT_FILENAME
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    """サンプルデータの既定パスを返す。"""
    return DATA_DIR / "bank_match.csv"
