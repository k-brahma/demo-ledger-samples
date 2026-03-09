"""売掛金 滞留年齢表ツール の分析ロジック。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

APP_TITLE = "売掛金 滞留年齢表ツール"
DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
RESULT_FILENAME = "receivable_aging_report.csv"
TODAY = pd.Timestamp(date.today())


def load_data(filepath: Path) -> pd.DataFrame:
    """CSV を読み込み、基本的な型変換を行う。"""
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    df["請求日"] = pd.to_datetime(df["請求日"])
    df["支払期日"] = pd.to_datetime(df["支払期日"])
    for col in ["請求額", "回収額"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df


def analyze(filepath: Path) -> pd.DataFrame:
    """CSV を分析して、画面表示向けの DataFrame を返す。"""
    df = load_data(filepath)
    result = df.copy()
    result["未回収残高"] = (result["請求額"] - result["回収額"]).clip(lower=0)
    result["滞留日数"] = result.apply(
        lambda row: max((TODAY - row["支払期日"]).days, 0) if row["未回収残高"] > 0 else 0,
        axis=1,
    )

    def bucket(row: pd.Series) -> str:
        if row["未回収残高"] == 0:
            return "回収済"
        if row["滞留日数"] >= 90:
            return "90日超"
        if row["滞留日数"] >= 60:
            return "60日超"
        if row["滞留日数"] >= 30:
            return "30日超"
        return "期日前後"

    result["年齢区分"] = result.apply(bucket, axis=1)
    order = {"90日超": 0, "60日超": 1, "30日超": 2, "期日前後": 3, "回収済": 4}
    result = result.sort_values("年齢区分", key=lambda s: s.map(order))

    return result.reset_index(drop=True)


def get_summary(df: pd.DataFrame) -> dict[str, str]:
    """サマリー表示用の辞書を返す。"""
    return {
        "請求件数": f"{len(df)} 件",
        "未回収残高": f"{df['未回収残高'].sum():,.0f} 円",
        "60日超": f"{df['年齢区分'].isin(['60日超', '90日超']).sum()} 件",
        "回収済": f"{(df['年齢区分'] == '回収済').sum()} 件",
    }



def get_chart_data(df: pd.DataFrame) -> dict[str, object]:
    """グラフ描画用のデータを返す。"""
    top = (
        df.groupby("得意先", as_index=False)["未回収残高"]
        .sum()
        .sort_values("未回収残高", ascending=False)
        .head(8)
    )
    return {
        "kind": "barh",
        "labels": top["得意先"].tolist(),
        "values": top["未回収残高"].tolist(),
        "colors": ["#d9534f" if value > 200000 else "#f0ad4e" for value in top["未回収残高"]],
        "xlabel": "未回収残高（円）",
        "title": "得意先別 未回収残高",
    }



def save_results(df: pd.DataFrame) -> Path:
    """結果を CSV に保存する。"""
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / RESULT_FILENAME
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def default_data_path() -> Path:
    """サンプルデータの既定パスを返す。"""
    return DATA_DIR / "receivables.csv"
