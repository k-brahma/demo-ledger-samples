"""固定資産 減価償却台帳ツール の分析ロジック。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

APP_TITLE = "固定資産 減価償却台帳ツール"
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
RESULT_FILENAME = "asset_depreciation_report.csv"
TODAY = pd.Timestamp(date.today())


def load_data(filepath: Path) -> pd.DataFrame:
    """CSV を読み込み、基本的な型変換を行う。"""
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df["取得日"] = pd.to_datetime(df["取得日"])
    for col in ["取得価額", "残存価額", "耐用年数"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df


def analyze(filepath: Path) -> pd.DataFrame:
    """CSV を分析して、画面表示向けの DataFrame を返す。"""
    df = load_data(filepath)
    result = df.copy()
    result["経過年数"] = ((TODAY - result["取得日"]).dt.days / 365).clip(lower=0)
    result["年間償却額"] = ((result["取得価額"] - result["残存価額"]) / result["耐用年数"]).round(0)
    result["累計償却額"] = (result["年間償却額"] * result["経過年数"]).clip(
        upper=(result["取得価額"] - result["残存価額"])
    ).round(0)
    result["期末簿価"] = (result["取得価額"] - result["累計償却額"]).clip(lower=result["残存価額"]).round(0)
    result["残存年数"] = (result["耐用年数"] - result["経過年数"]).clip(lower=0).round(2)
    result["状況"] = result["残存年数"].apply(lambda x: "更新検討" if x <= 1 else "運用中")
    result = result.sort_values("期末簿価", ascending=False)

    return result.reset_index(drop=True)


def get_summary(df: pd.DataFrame) -> dict[str, str]:
    """サマリー表示用の辞書を返す。"""
    return {
        "資産件数": f"{len(df)} 件",
        "取得総額": f"{df['取得価額'].sum():,.0f} 円",
        "期末簿価": f"{df['期末簿価'].sum():,.0f} 円",
        "更新検討": f"{(df['状況'] == '更新検討').sum()} 件",
    }



def get_chart_data(df: pd.DataFrame) -> dict[str, object]:
    """グラフ描画用のデータを返す。"""
    top = df.head(8)
    return {
        "kind": "barh",
        "labels": top["資産名"].tolist(),
        "values": top["期末簿価"].tolist(),
        "colors": ["#f0ad4e" if status == "更新検討" else "#5bc0de" for status in top["状況"]],
        "xlabel": "期末簿価（円）",
        "title": "簿価の大きい固定資産",
    }



def save_results(df: pd.DataFrame) -> Path:
    """結果を CSV に保存する。"""
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / RESULT_FILENAME
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    """サンプルデータの既定パスを返す。"""
    return DATA_DIR / "assets.csv"
