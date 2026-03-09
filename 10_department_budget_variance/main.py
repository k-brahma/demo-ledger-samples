"""部門別 予実差異分析ツール の分析ロジック。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

APP_TITLE = "部門別 予実差異分析ツール"
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
RESULT_FILENAME = "budget_variance_report.csv"
TODAY = pd.Timestamp(date.today())


def load_data(filepath: Path) -> pd.DataFrame:
    """CSV を読み込み、基本的な型変換を行う。"""
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    for col in ["予算", "実績", "前年差"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df


def analyze(filepath: Path) -> pd.DataFrame:
    """CSV を分析して、画面表示向けの DataFrame を返す。"""
    df = load_data(filepath)
    result = df.copy()
    result["差異額"] = result["実績"] - result["予算"]
    result["差異率(%)"] = (result["差異額"] / result["予算"].replace(0, 1) * 100).round(2)
    result["状況"] = result["差異率(%)"].abs().apply(
        lambda x: "要因確認" if x >= 20 else ("注意" if x >= 10 else "安定")
    )
    result = result.sort_values("差異額", key=lambda s: s.abs(), ascending=False)

    return result.reset_index(drop=True)


def get_summary(df: pd.DataFrame) -> dict[str, str]:
    """サマリー表示用の辞書を返す。"""
    return {
        "部門数": f"{df['部門'].nunique()} 部門",
        "予算合計": f"{df['予算'].sum():,.0f} 円",
        "差異額合計": f"{df['差異額'].sum():,.0f} 円",
        "要因確認": f"{(df['状況'] == '要因確認').sum()} 件",
    }



def get_chart_data(df: pd.DataFrame) -> dict[str, object]:
    """グラフ描画用のデータを返す。"""
    top = df.head(8)
    return {
        "kind": "grouped_barh",
        "labels": (top["部門"] + " / " + top["科目"]).tolist(),
        "series": [
            {
                "label": "予算",
                "values": top["予算"].tolist(),
                "color": "#5bc0de",
            },
            {
                "label": "実績",
                "values": top["実績"].tolist(),
                "color": "#f0ad4e",
            },
        ],
        "xlabel": "金額（円）",
        "title": "差異の大きい科目の予算 vs 実績",
    }



def save_results(df: pd.DataFrame) -> Path:
    """結果を CSV に保存する。"""
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / RESULT_FILENAME
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    """サンプルデータの既定パスを返す。"""
    return DATA_DIR / "budget_variance.csv"
