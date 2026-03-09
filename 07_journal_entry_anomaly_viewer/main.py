"""仕訳異常スコアリングツール の分析ロジック。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

APP_TITLE = "仕訳異常スコアリングツール"
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
RESULT_FILENAME = "journal_anomaly_report.csv"
TODAY = pd.Timestamp(date.today())


def load_data(filepath: Path) -> pd.DataFrame:
    """CSV を読み込み、基本的な型変換を行う。"""
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df["起票日時"] = pd.to_datetime(df["起票日時"])
    df["金額"] = pd.to_numeric(df["金額"], errors="coerce").fillna(0.0)

    return df


def analyze(filepath: Path) -> pd.DataFrame:
    """CSV を分析して、画面表示向けの DataFrame を返す。"""
    df = load_data(filepath)
    result = df.copy()
    result["休日起票"] = result["起票日時"].dt.dayofweek >= 5
    result["深夜起票"] = result["起票日時"].dt.hour >= 21
    result["端数不自然"] = result["金額"] % 1000 != 0
    result["注意摘要"] = result["摘要"].str.contains("緊急|特別|至急|調整", regex=True)
    result["異常スコア"] = (
        result["休日起票"].astype(int) * 2
        + result["深夜起票"].astype(int) * 2
        + result["端数不自然"].astype(int)
        + result["注意摘要"].astype(int)
    )
    result["判定"] = result["異常スコア"].apply(lambda x: "高" if x >= 4 else ("中" if x >= 2 else "低"))
    result = result.sort_values(["異常スコア", "金額"], ascending=[False, False])

    return result.reset_index(drop=True)


def get_summary(df: pd.DataFrame) -> dict[str, str]:
    """サマリー表示用の辞書を返す。"""
    return {
        "仕訳件数": f"{len(df)} 件",
        "高リスク": f"{(df['判定'] == '高').sum()} 件",
        "休日起票": f"{df['休日起票'].sum()} 件",
        "平均スコア": f"{df['異常スコア'].mean():.2f}",
    }



def get_chart_data(df: pd.DataFrame) -> dict[str, object]:
    """グラフ描画用のデータを返す。"""
    top = df.head(8)
    return {
        "kind": "barh",
        "labels": (top["伝票No"] + " " + top["起票者"]).tolist(),
        "values": top["異常スコア"].tolist(),
        "colors": ["#d9534f" if x >= 4 else "#f0ad4e" if x >= 2 else "#5cb85c" for x in top["異常スコア"]],
        "xlabel": "異常スコア",
        "title": "異常スコア上位の仕訳",
    }



def save_results(df: pd.DataFrame) -> Path:
    """結果を CSV に保存する。"""
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / RESULT_FILENAME
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    """サンプルデータの既定パスを返す。"""
    return DATA_DIR / "journal_entries.csv"
