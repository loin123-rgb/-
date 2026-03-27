#!/usr/bin/env python3
"""
analyze_correlation.py - 商品/個股相關性分析工具

計算商品、期貨與個股之間的相關係數矩陣，識別強相關關係。

使用方式:
    python analyze_correlation.py                    # 分析 data/ 目錄中最新資料
    python analyze_correlation.py --period 6mo       # 重新抓取6個月資料後分析
    python analyze_correlation.py --min-corr 0.7     # 只顯示相關係數 > 0.7 的配對
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
    import yfinance as yf
except ImportError:
    print("缺少依賴套件，請執行: pip install yfinance pandas numpy")
    sys.exit(1)

# 預設分析標的（涵蓋商品、期貨、相關個股）
ANALYSIS_SYMBOLS = {
    # 商品/期貨
    "CL=F": "WTI原油",
    "GC=F": "黃金",
    "HG=F": "銅",
    "ZW=F": "小麥",
    "NG=F": "天然氣",
    # 商品股ETF
    "XLE": "能源股ETF",
    "GDX": "黃金礦商ETF",
    "COPX": "銅礦ETF",
    # 個股代表
    "XOM": "埃克森美孚",
    "FCX": "自由港(銅)",
    "NEM": "紐蒙特(金)",
    # 宏觀
    "DX-Y.NYB": "美元指數",
    "^TNX": "10Y美債殖利率",
    "^GSPC": "S&P500",
}


def load_or_fetch_prices(symbols: list[str], period: str, data_dir: Path) -> pd.DataFrame:
    """載入本地快取或重新抓取價格資料。"""
    latest_csv = data_dir / "prices_latest.csv"

    # 嘗試讀取本地最新資料
    if latest_csv.exists():
        try:
            prices = pd.read_csv(latest_csv, index_col=0, parse_dates=True)
            available = [s for s in symbols if s in prices.columns]
            if len(available) >= len(symbols) * 0.8:  # 80%以上標的有資料才用快取
                print(f"使用本地快取資料：{latest_csv}")
                return prices[available]
        except Exception:
            pass

    # 重新抓取
    print(f"從 Yahoo Finance 抓取資料（期間：{period}）...")
    data = yf.download(symbols, period=period, auto_adjust=True, progress=False)
    if data.empty:
        return pd.DataFrame()

    prices = data["Close"] if "Close" in data.columns else data
    # 儲存快取
    data_dir.mkdir(parents=True, exist_ok=True)
    prices.to_csv(data_dir / "prices_latest.csv")
    return prices


def compute_correlation_matrix(prices: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    """計算收益率的相關係數矩陣。"""
    returns = prices.pct_change().dropna()
    return returns.corr(method=method)


def find_strong_pairs(corr_matrix: pd.DataFrame, min_corr: float = 0.6) -> pd.DataFrame:
    """找出相關係數超過閾值的配對。"""
    pairs = []
    cols = corr_matrix.columns
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            c = corr_matrix.iloc[i, j]
            if abs(c) >= min_corr:
                pairs.append(
                    {
                        "標的A": cols[i],
                        "標的B": cols[j],
                        "相關係數": round(c, 4),
                        "關係": "正相關" if c > 0 else "負相關",
                        "強度": "強" if abs(c) >= 0.8 else "中",
                    }
                )
    df = pd.DataFrame(pairs)
    if not df.empty:
        df = df.sort_values("相關係數", key=abs, ascending=False)
    return df


def print_correlation_table(corr_matrix: pd.DataFrame, symbol_names: dict) -> None:
    """以易讀格式印出相關矩陣（使用友好名稱）。"""
    renamed = corr_matrix.rename(
        index=symbol_names, columns=symbol_names
    )
    # 格式化：相關係數顯示2位小數
    formatted = renamed.map(lambda x: f"{x:.2f}" if not pd.isna(x) else "N/A")
    print(formatted.to_string())


def rolling_correlation(
    prices: pd.DataFrame, sym_a: str, sym_b: str, window: int = 60
) -> pd.Series:
    """計算兩標的的滾動相關係數。"""
    returns = prices[[sym_a, sym_b]].pct_change().dropna()
    return returns[sym_a].rolling(window).corr(returns[sym_b])


def save_results(corr_matrix: pd.DataFrame, strong_pairs: pd.DataFrame, output_dir: Path) -> None:
    """儲存分析結果。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")

    # 相關矩陣 CSV
    corr_file = output_dir / f"correlation_matrix_{date_str}.csv"
    corr_matrix.to_csv(corr_file)
    print(f"\n已儲存相關矩陣：{corr_file}")

    # 強相關配對 JSON
    if not strong_pairs.empty:
        pairs_file = output_dir / f"strong_pairs_{date_str}.json"
        with open(pairs_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "分析時間": datetime.now().isoformat(),
                    "強相關配對": strong_pairs.to_dict(orient="records"),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"已儲存強相關配對：{pairs_file}")


def main():
    parser = argparse.ArgumentParser(description="商品/個股相關性分析")
    parser.add_argument("--period", default="6mo", choices=["3mo", "6mo", "1y", "2y"])
    parser.add_argument("--min-corr", type=float, default=0.6, help="最低相關係數閾值（預設 0.6）")
    parser.add_argument("--method", default="pearson", choices=["pearson", "spearman", "kendall"])
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    output_dir = Path(args.output_dir) if args.output_dir else data_dir

    symbols = list(ANALYSIS_SYMBOLS.keys())

    print(f"\n{'='*60}")
    print(f"  國際情勢投資框架 - 相關性分析")
    print(f"  分析時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  方法：{args.method} | 期間：{args.period}")
    print(f"{'='*60}\n")

    # 載入資料
    prices = load_or_fetch_prices(symbols, args.period, data_dir)
    if prices.empty:
        print("無法取得資料，程式結束。")
        sys.exit(1)

    # 只保留有資料的標的
    valid_symbols = [s for s in symbols if s in prices.columns]
    prices = prices[valid_symbols].dropna(axis=1, how="all")

    # 計算相關矩陣
    corr_matrix = compute_correlation_matrix(prices, method=args.method)

    # 印出相關矩陣
    print("📊 相關係數矩陣：")
    print_correlation_table(corr_matrix, ANALYSIS_SYMBOLS)

    # 找強相關配對
    strong_pairs = find_strong_pairs(corr_matrix, min_corr=args.min_corr)
    if not strong_pairs.empty:
        print(f"\n🔗 強相關配對（|相關係數| ≥ {args.min_corr}）：")
        print(strong_pairs.to_string(index=False))
    else:
        print(f"\n未發現相關係數 ≥ {args.min_corr} 的配對。")

    # 儲存結果
    save_results(corr_matrix, strong_pairs, output_dir)
    print(f"\n✅ 相關性分析完成")


if __name__ == "__main__":
    main()
