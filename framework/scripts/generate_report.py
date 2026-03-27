#!/usr/bin/env python3
"""
generate_report.py - 投資分析報告生成器

彙整市場資料、相關性分析與人工填寫的模板，自動生成 Markdown 格式投資報告。

使用方式:
    python generate_report.py                      # 生成當日報告
    python generate_report.py --date 2024-01-15   # 生成指定日期報告
    python generate_report.py --period 1mo        # 資料期間
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import pandas as pd
    import yfinance as yf
except ImportError:
    print("缺少依賴套件，請執行: pip install yfinance pandas")
    sys.exit(1)

# 報告用標的（按類別）
REPORT_SYMBOLS = {
    "能源": {"CL=F": "WTI原油", "BZ=F": "Brent原油", "NG=F": "天然氣"},
    "貴金屬": {"GC=F": "黃金", "SI=F": "白銀"},
    "工業金屬": {"HG=F": "銅", "ALI=F": "鋁"},
    "農產品": {"ZW=F": "小麥", "ZC=F": "玉米", "ZS=F": "大豆"},
    "宏觀指標": {"DX-Y.NYB": "美元指數", "^TNX": "10Y美債殖利率", "^VIX": "VIX"},
    "能源股": {"XOM": "埃克森美孚", "CVX": "雪佛龍", "COP": "康菲石油"},
    "礦業股": {"FCX": "自由港(銅)", "NEM": "紐蒙特(金)", "RIO": "力拓"},
}

DIRECTION_EMOJI = {"up": "📈", "down": "📉", "flat": "➡️"}


def fetch_market_data(period: str = "1mo") -> dict:
    """抓取所有報告標的的市場資料。"""
    all_symbols = []
    for category_symbols in REPORT_SYMBOLS.values():
        all_symbols.extend(category_symbols.keys())

    print(f"正在抓取市場資料（{len(all_symbols)} 個標的）...")
    data = yf.download(all_symbols, period=period, auto_adjust=True, progress=False)
    if data.empty:
        return {}

    prices = data["Close"] if "Close" in data.columns else data
    return prices


def get_price_change(prices: pd.DataFrame, symbol: str) -> dict:
    """取得標的的價格變化資訊。"""
    if symbol not in prices.columns:
        return {}

    series = prices[symbol].dropna()
    if len(series) < 2:
        return {}

    latest = series.iloc[-1]
    prev_day = series.iloc[-2]
    prev_week = series.iloc[-6] if len(series) >= 6 else series.iloc[0]
    prev_month = series.iloc[-22] if len(series) >= 22 else series.iloc[0]

    day_chg = (latest / prev_day - 1) * 100
    week_chg = (latest / prev_week - 1) * 100
    month_chg = (latest / prev_month - 1) * 100

    direction = "up" if month_chg > 0.5 else ("down" if month_chg < -0.5 else "flat")

    return {
        "latest": latest,
        "day_chg": day_chg,
        "week_chg": week_chg,
        "month_chg": month_chg,
        "direction": direction,
    }


def format_change(value: float, decimals: int = 2) -> str:
    """格式化漲跌幅（帶+/-號）。"""
    if value > 0:
        return f"+{value:.{decimals}f}%"
    return f"{value:.{decimals}f}%"


def build_market_table(prices: pd.DataFrame, category: str, symbols: dict) -> str:
    """生成單一類別的市場資料表格。"""
    lines = [
        f"### {category}",
        "",
        "| 標的 | 最新價 | 日漲跌 | 週漲跌 | 月漲跌 | 趨勢 |",
        "|------|--------|--------|--------|--------|------|",
    ]
    for symbol, name in symbols.items():
        info = get_price_change(prices, symbol)
        if not info:
            lines.append(f"| {name} ({symbol}) | N/A | — | — | — | — |")
            continue
        emoji = DIRECTION_EMOJI[info["direction"]]
        lines.append(
            f"| {name} ({symbol}) "
            f"| {info['latest']:.4g} "
            f"| {format_change(info['day_chg'])} "
            f"| {format_change(info['week_chg'])} "
            f"| {format_change(info['month_chg'])} "
            f"| {emoji} |"
        )
    lines.append("")
    return "\n".join(lines)


def load_latest_correlations(data_dir: Path) -> str:
    """載入最新相關性分析結果（若有）。"""
    # 找最新的 strong_pairs JSON
    json_files = sorted(data_dir.glob("strong_pairs_*.json"), reverse=True)
    if not json_files:
        return "_尚未執行相關性分析，請執行 `analyze_correlation.py`_\n"

    with open(json_files[0], encoding="utf-8") as f:
        data = json.load(f)

    pairs = data.get("強相關配對", [])
    if not pairs:
        return "_本期未發現顯著強相關配對_\n"

    lines = [
        "| 標的A | 標的B | 相關係數 | 關係 | 強度 |",
        "|-------|-------|----------|------|------|",
    ]
    for p in pairs[:10]:  # 最多顯示前10組
        lines.append(
            f"| {p['標的A']} | {p['標的B']} "
            f"| {p['相關係數']} | {p['關係']} | {p['強度']} |"
        )
    return "\n".join(lines) + "\n"


def generate_report(report_date: str, period: str, output_dir: Path, data_dir: Path) -> Path:
    """生成完整投資分析報告。"""
    prices = fetch_market_data(period=period)

    lines = []

    # ── 報告標題 ────────────────────────────────────────────────────────────
    lines += [
        f"# 國際情勢投資分析報告",
        f"",
        f"> **報告日期**：{report_date}　｜　**資料期間**：{period}　｜　**自動生成**",
        f"",
        "---",
        "",
    ]

    # ── 執行摘要 ────────────────────────────────────────────────────────────
    lines += [
        "## 執行摘要（Executive Summary）",
        "",
        "> 🔔 **本節為人工填寫區域** - 請在執行分析後補充以下重點：",
        "",
        "### 本週/本月關鍵事件",
        "<!-- 填寫影響市場的重大國際事件 -->",
        "1. ",
        "2. ",
        "3. ",
        "",
        "### 市場整體判斷",
        "<!-- 商品市場整體多空傾向 -->",
        "- **能源**：□ 偏多　□ 中性　□ 偏空　→ 理由：",
        "- **金屬**：□ 偏多　□ 中性　□ 偏空　→ 理由：",
        "- **農產品**：□ 偏多　□ 中性　□ 偏空　→ 理由：",
        "",
        "### 本期最佳機會",
        "| 標的 | 方向 | 理由 | 時間框架 |",
        "|------|------|------|----------|",
        "| | | | |",
        "",
        "---",
        "",
    ]

    # ── 市場價格總覽 ────────────────────────────────────────────────────────
    lines += [
        "## 市場價格總覽",
        "",
        f"_資料截止：{datetime.now().strftime('%Y-%m-%d %H:%M')} UTC_",
        "",
    ]

    if not isinstance(prices, pd.DataFrame) or prices.empty:
        lines.append("_無法取得市場資料_\n")
    else:
        for category, symbols in REPORT_SYMBOLS.items():
            lines.append(build_market_table(prices, category, symbols))

    lines += ["---", ""]

    # ── 供需動態摘要 ────────────────────────────────────────────────────────
    lines += [
        "## 供需動態摘要",
        "",
        "> 🔔 **本節為人工填寫區域** - 請參考 `templates/supply_demand.md` 更新",
        "",
        "### 原油供需",
        "- **OPEC+ 產量**：",
        "- **美國庫存**：□ 增加　□ 減少　變化量：___",
        "- **全球需求預估**：",
        "- **供需判斷**：□ 短缺　□ 平衡　□ 過剩",
        "",
        "### 金屬供需",
        "- **銅 LME 庫存**：□ 增加　□ 減少",
        "- **中國需求信號**：",
        "",
        "### 農產品供需",
        "- **主要產區氣候**：",
        "- **USDA 報告摘要**：",
        "",
        "---",
        "",
    ]

    # ── 期貨市場結構 ────────────────────────────────────────────────────────
    lines += [
        "## 期貨市場結構",
        "",
        "> 🔔 **本節為人工填寫區域** - 請參考 `templates/futures_trend.md` 更新",
        "",
        "| 商品 | 期貨結構 | COT淨多頭百分位 | 信號 |",
        "|------|----------|----------------|------|",
        "| WTI原油 | □ Contango　□ Backwardation | ___% | |",
        "| 黃金 | □ Contango　□ Backwardation | ___% | |",
        "| 銅 | □ Contango　□ Backwardation | ___% | |",
        "| 小麥 | □ Contango　□ Backwardation | ___% | |",
        "",
        "---",
        "",
    ]

    # ── 相關性分析 ────────────────────────────────────────────────────────
    lines += [
        "## 商品/個股相關性分析",
        "",
        load_latest_correlations(data_dir),
        "",
        "---",
        "",
    ]

    # ── 個股機會清單 ────────────────────────────────────────────────────────
    lines += [
        "## 個股機會清單",
        "",
        "> 🔔 **本節為人工填寫區域** - 請參考 `templates/stock_analysis.md` 更新",
        "",
        "### 受益個股（多頭機會）",
        "",
        "| 代碼 | 公司 | 關聯商品 | 評級 | 目標價 | 停損 |",
        "|------|------|----------|------|--------|------|",
        "| | | | | | |",
        "",
        "### 受損個股（空頭機會或迴避）",
        "",
        "| 代碼 | 公司 | 關聯商品 | 評級 | 備註 |",
        "|------|------|----------|------|------|",
        "| | | | | |",
        "",
        "---",
        "",
    ]

    # ── 風險監控 ────────────────────────────────────────────────────────────
    lines += [
        "## 風險監控清單",
        "",
        "### 未來2週需追蹤事件",
        "",
        "| 日期 | 事件 | 影響商品 | 預期影響 |",
        "|------|------|----------|----------|",
        "| | OPEC+ 會議 | 原油 | |",
        "| | USDA 月度供需報告 | 農產品 | |",
        "| | 美國CPI數據 | 黃金/美元 | |",
        "| | 中國貿易數據 | 銅/鐵礦石 | |",
        "",
        "### 尾部風險警示",
        "- [ ] 地緣政治升溫：",
        "- [ ] 重要央行政策：",
        "- [ ] 氣候/災害風險：",
        "",
        "---",
        "",
    ]

    # ── 報告附錄 ────────────────────────────────────────────────────────────
    lines += [
        "## 附錄：分析工具與資源",
        "",
        "| 資源 | 用途 | 連結 |",
        "|------|------|------|",
        "| EIA 石油週報 | 原油供需庫存 | https://www.eia.gov/petroleum/ |",
        "| IEA 月度石油報告 | 全球石油市場 | https://www.iea.org/reports |",
        "| USDA WASDE | 農產品供需 | https://www.usda.gov/oce/commodity |",
        "| LME 金屬庫存 | 工業金屬庫存 | https://www.lme.com/Market-data |",
        "| CFTC COT 報告 | 期貨持倉結構 | https://www.cftc.gov/MarketReports |",
        "| CME FedWatch | 利率預期 | https://www.cmegroup.com/markets/interest-rates |",
        "",
        "---",
        "",
        f"_報告生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC_",
        f"_使用框架：國際情勢投資分析框架 v1.0_",
    ]

    # 寫出報告
    report_content = "\n".join(lines)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / f"{report_date}_investment_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    return report_file


def main():
    parser = argparse.ArgumentParser(description="生成投資分析報告")
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="報告日期（YYYY-MM-DD），預設為今日",
    )
    parser.add_argument(
        "--period",
        default="1mo",
        choices=["1mo", "3mo", "6mo"],
        help="價格資料期間（預設：1mo）",
    )
    parser.add_argument("--output-dir", default=None, help="報告輸出目錄")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    output_dir = Path(args.output_dir) if args.output_dir else script_dir.parent / "reports"

    print(f"\n{'='*60}")
    print(f"  國際情勢投資框架 - 報告生成器")
    print(f"  報告日期：{args.date}")
    print(f"{'='*60}\n")

    report_file = generate_report(
        report_date=args.date,
        period=args.period,
        output_dir=output_dir,
        data_dir=data_dir,
    )

    print(f"\n✅ 報告已生成：{report_file}")
    print(f"\n💡 提示：請開啟報告並填寫標記「🔔 本節為人工填寫區域」的部分")


if __name__ == "__main__":
    main()
