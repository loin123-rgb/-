#!/usr/bin/env python3
"""
fetch_data.py - 市場資料抓取工具

從 Yahoo Finance 抓取商品、期貨、個股的價格資料並儲存至 data/ 目錄。

使用方式:
    python fetch_data.py                      # 抓取所有預設標的
    python fetch_data.py --symbols CL=F GC=F  # 指定標的
    python fetch_data.py --period 3mo         # 指定時間範圍 (1mo/3mo/6mo/1y/2y/5y)
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print("缺少依賴套件，請執行: pip install yfinance pandas")
    sys.exit(1)

# ── 預設追蹤標的清單 ────────────────────────────────────────────────────────
DEFAULT_SYMBOLS = {
    "能源": {
        "CL=F": "WTI原油期貨",
        "BZ=F": "Brent原油期貨",
        "NG=F": "天然氣期貨",
    },
    "貴金屬": {
        "GC=F": "黃金期貨",
        "SI=F": "白銀期貨",
        "PL=F": "鉑金期貨",
    },
    "工業金屬": {
        "HG=F": "銅期貨",
        "ALI=F": "鋁期貨",
    },
    "農產品": {
        "ZW=F": "小麥期貨",
        "ZC=F": "玉米期貨",
        "ZS=F": "大豆期貨",
    },
    "商品指數": {
        "DJP": "iPath Bloomberg商品指數ETF",
        "GSG": "iShares GSCI商品指數ETF",
        "DBC": "Invesco DB商品追蹤ETF",
    },
    "相關個股_能源": {
        "XOM": "ExxonMobil",
        "CVX": "Chevron",
        "SLB": "Schlumberger",
        "COP": "ConocoPhillips",
    },
    "相關個股_金屬": {
        "FCX": "Freeport-McMoRan (銅)",
        "NEM": "Newmont (黃金)",
        "AA": "Alcoa (鋁)",
        "RIO": "Rio Tinto",
    },
    "宏觀指標": {
        "DX-Y.NYB": "美元指數",
        "^TNX": "10年期美債殖利率",
        "^VIX": "VIX恐慌指數",
        "^GSPC": "S&P 500",
    },
}


def fetch_prices(symbols: list[str], period: str = "3mo") -> pd.DataFrame:
    """抓取多個標的的收盤價資料。"""
    print(f"正在抓取 {len(symbols)} 個標的的資料（期間：{period}）...")
    data = yf.download(symbols, period=period, auto_adjust=True, progress=False)

    if data.empty:
        print("警告：未抓到任何資料，請確認網路連線或標的代碼是否正確。")
        return pd.DataFrame()

    # 取收盤價
    if "Close" in data.columns:
        prices = data["Close"]
    else:
        prices = data

    return prices


def compute_summary(prices: pd.DataFrame) -> pd.DataFrame:
    """計算摘要統計（最新價、漲跌幅、52週高低）。"""
    if prices.empty:
        return pd.DataFrame()

    summary_rows = []
    for symbol in prices.columns:
        series = prices[symbol].dropna()
        if series.empty:
            continue

        latest = series.iloc[-1]
        prev_week = series.iloc[-6] if len(series) >= 6 else series.iloc[0]
        prev_month = series.iloc[-22] if len(series) >= 22 else series.iloc[0]
        high_52w = series.tail(252).max()
        low_52w = series.tail(252).min()

        summary_rows.append(
            {
                "代碼": symbol,
                "最新價": round(latest, 4),
                "週漲跌%": round((latest / prev_week - 1) * 100, 2),
                "月漲跌%": round((latest / prev_month - 1) * 100, 2),
                "52週高": round(high_52w, 4),
                "52週低": round(low_52w, 4),
                "距高點%": round((latest / high_52w - 1) * 100, 2),
                "更新時間": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        )

    return pd.DataFrame(summary_rows)


def save_to_csv(df: pd.DataFrame, filepath: Path) -> None:
    """儲存 DataFrame 至 CSV 檔案。"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=True, encoding="utf-8-sig")
    print(f"  已儲存：{filepath}")


def save_summary_json(summary: pd.DataFrame, filepath: Path) -> None:
    """儲存摘要至 JSON 檔案（方便其他腳本讀取）。"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    records = summary.to_dict(orient="records")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            {"更新時間": datetime.now().isoformat(), "資料": records},
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"  已儲存：{filepath}")


def main():
    parser = argparse.ArgumentParser(description="抓取市場價格資料")
    parser.add_argument(
        "--symbols",
        nargs="*",
        default=None,
        help="指定要抓取的標的代碼（空白分隔），預設抓取所有預設標的",
    )
    parser.add_argument(
        "--period",
        default="3mo",
        choices=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        help="資料期間（預設：3mo）",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="輸出目錄（預設：framework/data/）",
    )
    args = parser.parse_args()

    # 決定輸出目錄
    script_dir = Path(__file__).parent
    output_dir = Path(args.output_dir) if args.output_dir else script_dir.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 決定要抓取的標的
    if args.symbols:
        symbols_to_fetch = args.symbols
        symbol_map = {s: s for s in symbols_to_fetch}
    else:
        symbols_to_fetch = []
        symbol_map = {}
        for category, items in DEFAULT_SYMBOLS.items():
            for code, name in items.items():
                symbols_to_fetch.append(code)
                symbol_map[code] = f"{name} ({code})"

    print(f"\n{'='*60}")
    print(f"  國際情勢投資框架 - 市場資料抓取")
    print(f"  抓取時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # 抓取資料
    prices = fetch_prices(symbols_to_fetch, period=args.period)
    if prices.empty:
        print("無法取得資料，程式結束。")
        sys.exit(1)

    # 儲存原始收盤價
    date_str = datetime.now().strftime("%Y%m%d")
    prices_file = output_dir / f"prices_{date_str}.csv"
    save_to_csv(prices, prices_file)

    # 計算並儲存摘要
    summary = compute_summary(prices)
    if not summary.empty:
        summary_csv = output_dir / "latest_summary.csv"
        summary_json = output_dir / "latest_summary.json"
        save_to_csv(summary, summary_csv)
        save_summary_json(summary, summary_json)

        print(f"\n{'='*60}")
        print("  最新市場摘要")
        print(f"{'='*60}")
        print(summary.to_string(index=False))

    print(f"\n✅ 資料抓取完成，結果儲存於：{output_dir}")


if __name__ == "__main__":
    main()
