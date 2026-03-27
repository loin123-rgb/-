# 國際情勢投資分析框架

> 一套可持續更新的研究框架，將國際事件、供需變化、商品價格、期貨走勢與相關個股連結，作為投資報告與決策輔助。

---

## 目錄

- [框架目的](#框架目的)
- [框架架構](#框架架構)
- [使用流程](#使用流程)
- [目錄結構](#目錄結構)
- [快速開始](#快速開始)
- [分析模板](#分析模板)
- [腳本工具](#腳本工具)
- [更新與維護](#更新與維護)

---

## 框架目的

本框架旨在建立一套系統化、可持續更新的國際情勢投資研究方法，核心目標如下：

1. **事件追蹤**：即時記錄影響市場的地緣政治、經濟政策與產業事件
2. **供需分析**：分析關鍵商品（能源、金屬、農產品）的全球供需動態
3. **價格連結**：將商品現貨、期貨價格走勢與相關企業股票表現串聯
4. **投資決策**：輸出結構化報告，輔助投資組合配置與風險管理

---

## 框架架構

```
國際事件 ──► 供需影響評估 ──► 商品/期貨價格預測
                                        │
                                        ▼
                              相關個股篩選與評估
                                        │
                                        ▼
                              投資報告與建議
```

### 五大分析維度

| 維度 | 說明 | 對應模板 |
|------|------|----------|
| 🌏 國際事件 | 地緣政治、政策變動、重大事件 | `event_analysis.md` |
| 📦 供需動態 | 全球供需結構、庫存、產能 | `supply_demand.md` |
| 🛢️ 商品價格 | 能源、金屬、農產品現貨價格 | `commodity_price.md` |
| 📈 期貨走勢 | 期貨曲線、持倉結構、技術面 | `futures_trend.md` |
| 🏢 個股分析 | 受益/受損個股、財務、評價 | `stock_analysis.md` |

---

## 使用流程

```
步驟 1：事件捕捉
  └─► 填寫 templates/event_analysis.md

步驟 2：供需影響評估
  └─► 填寫 templates/supply_demand.md

步驟 3：商品與期貨分析
  ├─► 填寫 templates/commodity_price.md
  └─► 填寫 templates/futures_trend.md

步驟 4：個股篩選
  └─► 填寫 templates/stock_analysis.md

步驟 5：彙整報告
  └─► 執行 scripts/generate_report.py
      產出 reports/YYYY-MM-DD_report.md
```

---

## 目錄結構

```
.
├── README.md                        # 本文件：框架說明
├── framework/
│   ├── templates/                   # 分析模板
│   │   ├── event_analysis.md        # 國際事件分析模板
│   │   ├── supply_demand.md         # 供需動態分析模板
│   │   ├── commodity_price.md       # 商品價格分析模板
│   │   ├── futures_trend.md         # 期貨走勢分析模板
│   │   └── stock_analysis.md        # 個股分析模板
│   ├── scripts/                     # 分析工具腳本
│   │   ├── fetch_data.py            # 市場資料抓取
│   │   ├── analyze_correlation.py   # 相關性分析
│   │   └── generate_report.py       # 報告生成器
│   ├── data/                        # 資料存放區（本地快取）
│   │   └── .gitkeep
│   └── reports/                     # 輸出報告存放區
│       └── .gitkeep
└── docs/
    └── methodology.md               # 分析方法論說明
```

---

## 快速開始

### 環境需求

```bash
Python >= 3.9
pip install -r requirements.txt
```

### 安裝依賴

```bash
pip install yfinance pandas numpy requests python-dotenv tabulate
```

### 執行資料抓取

```bash
python framework/scripts/fetch_data.py
```

### 生成分析報告

```bash
python framework/scripts/generate_report.py --date 2024-01-15
```

---

## 分析模板

各模板位於 `framework/templates/`，依分析流程順序使用：

| 模板 | 用途 |
|------|------|
| [`event_analysis.md`](framework/templates/event_analysis.md) | 記錄國際事件並評估市場影響 |
| [`supply_demand.md`](framework/templates/supply_demand.md) | 分析商品供需結構變化 |
| [`commodity_price.md`](framework/templates/commodity_price.md) | 追蹤商品現貨價格走勢 |
| [`futures_trend.md`](framework/templates/futures_trend.md) | 分析期貨市場結構與信號 |
| [`stock_analysis.md`](framework/templates/stock_analysis.md) | 篩選並評估相關個股 |

---

## 腳本工具

| 腳本 | 功能 |
|------|------|
| `fetch_data.py` | 從 Yahoo Finance 抓取商品、期貨、個股資料 |
| `analyze_correlation.py` | 計算事件/商品/個股間的相關係數矩陣 |
| `generate_report.py` | 彙整所有分析，生成 Markdown 格式投資報告 |

---

## 更新與維護

- **每週更新**：供需動態、商品價格、期貨持倉
- **事件驅動**：發生重大國際事件時立即填寫事件模板
- **月度彙整**：每月底生成綜合投資報告
- **季度回顧**：每季評估框架準確度，調整分析參數

---

*框架版本：v1.0 | 建立日期：2024*
