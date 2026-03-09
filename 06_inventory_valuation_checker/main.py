"""在庫評価・滞留チェックツール の分析ロジック。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

APP_TITLE = "在庫評価・滞留チェックツール"
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
RESULT_FILENAME = "inventory_valuation_report.csv"
TODAY = pd.Timestamp(date.today())


def load_data(filepath: Path) -> pd.DataFrame:
    """CSV を読み込み、基本的な型変換を行う。"""
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df["最終出庫日"] = pd.to_datetime(df["最終出庫日"])
    for col in ["数量", "単価"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df


def analyze(filepath: Path) -> pd.DataFrame:
    """CSV を分析して、画面表示向けの DataFrame を返す。"""
    df = load_data(filepath)
    result = df.copy()
    result["在庫金額"] = (result["数量"] * result["単価"]).round(0)
    result["滞留日数"] = (TODAY - result["最終出庫日"]).dt.days

    def judge(days: float) -> str:
        if days >= 180:
            return "評価減候補"
        if days >= 90:
            return "滞留"
        return "適正在庫"

    result["状況"] = result["滞留日数"].apply(judge)
    result = result.sort_values("在庫金額", ascending=False)

    return result.reset_index(drop=True)


def get_summary(df: pd.DataFrame) -> dict[str, str]:
    """サマリー表示用の辞書を返す。"""
    return {
        "在庫件数": f"{len(df)} 件",
        "在庫総額": f"{df['在庫金額'].sum():,.0f} 円",
        "滞留/評価減": f"{df['状況'].isin(['滞留', '評価減候補']).sum()} 件",
        "最長滞留": f"{df['滞留日数'].max():,.0f} 日",
    }



def get_chart_data(df: pd.DataFrame) -> dict[str, object]:
    """グラフ描画用のデータを返す。"""
    top = df.head(8)
    color_map = {"適正在庫": "#5cb85c", "滞留": "#f0ad4e", "評価減候補": "#d9534f"}
    return {
        "kind": "barh",
        "labels": top["商品名"].tolist(),
        "values": top["在庫金額"].tolist(),
        "colors": top["状況"].map(color_map).tolist(),
        "xlabel": "在庫金額（円）",
        "title": "金額の大きい在庫",
    }



def save_results(df: pd.DataFrame) -> Path:
    """結果を CSV に保存する。"""
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / RESULT_FILENAME
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    """サンプルデータの既定パスを返す。"""
    return DATA_DIR / "inventory.csv"
