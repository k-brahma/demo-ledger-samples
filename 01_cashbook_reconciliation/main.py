"""現金出納帳 突合チェックツール の分析ロジック。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

APP_TITLE = "現金出納帳 突合チェックツール"
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
RESULT_FILENAME = "cashbook_report.csv"
TODAY = pd.Timestamp(date.today())


def load_data(filepath: Path) -> pd.DataFrame:
    """CSV を読み込み、基本的な型変換を行う。"""
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df["日付"] = pd.to_datetime(df["日付"])
    for col in ["入金", "出金", "帳簿残高", "実査残高"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df


def analyze(filepath: Path) -> pd.DataFrame:
    """CSV を分析して、画面表示向けの DataFrame を返す。"""
    df = load_data(filepath)
    result = df.copy()
    result["差異"] = result["実査残高"] - result["帳簿残高"]
    result["差異率(%)"] = (result["差異"] / result["帳簿残高"].replace(0, 1) * 100).round(2)
    result["状況"] = result["差異"].abs().apply(
        lambda x: "要調査" if x >= 2000 else ("警告" if x >= 500 else "正常")
    )
    result = result.sort_values(["状況", "差異"], ascending=[True, False])

    return result.reset_index(drop=True)


def get_summary(df: pd.DataFrame) -> dict[str, str]:
    """サマリー表示用の辞書を返す。"""
    return {
        "件数": f"{len(df)} 件",
        "差異合計": f"{df['差異'].sum():,.0f} 円",
        "要調査": f"{(df['状況'] == '要調査').sum()} 件",
        "最大差異": f"{df['差異'].abs().max():,.0f} 円",
    }



def get_chart_data(df: pd.DataFrame) -> dict[str, object]:
    """グラフ描画用のデータを返す。"""
    top = df.sort_values("差異", key=lambda s: s.abs(), ascending=False).head(8)
    colors = top["状況"].map({"正常": "#5cb85c", "警告": "#f0ad4e", "要調査": "#d9534f"})
    return {
        "kind": "barh",
        "labels": (top["日付"].dt.strftime("%m/%d") + " " + top["担当者"]).tolist(),
        "values": top["差異"].abs().tolist(),
        "colors": colors.tolist(),
        "xlabel": "差異額（円）",
        "title": "差異の大きい締め日",
    }



def save_results(df: pd.DataFrame) -> Path:
    """結果を CSV に保存する。"""
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / RESULT_FILENAME
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    """サンプルデータの既定パスを返す。"""
    return DATA_DIR / "cashbook.csv"
