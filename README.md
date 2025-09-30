# real-estate-crawler

> 一個端到端的 ETL 流程，負責下載內政部不動產成交案件 CSV 檔案，進行清理與合併，並將結果寫入 Elasticsearch，最後透過 Kibana 做視覺化分析。

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#license) [![Tests](https://img.shields.io/badge/tests-pytest%20%2B%20coverage-brightgreen)](#tests)

## ✨ 功能特色

- 📥 **Fetcher**：可靠的 HTTP 下載（內建重試與退避）
- 🧹 **Parser/Cleaner**：取第二列作為欄名，數值標準化，加上 `df_name`
- 🧮 **Combiner**：合併季別 CSV，過濾與統計，輸出 `filter.csv` 與 `count.csv`
- 📦 **Sink**：批次寫入 **Elasticsearch**
- 🧭 **Runner**：一鍵執行整個流程
- 🧪 **Tests**：模組化的 pytest 測試，確保穩定性

---

## 📁 專案架構

```
real-estate-crawler/
├─ src/rec/                     
│  ├─ __init__.py
│  ├─ config.py                 # 常數、城市/交易類型對照、路徑、ES 連線
│  ├─ manifest.py               # 產生需抓取的檔案與季別清單（僅列 X_lvr_land_X）
│  ├─ fetcher.py                # 下載 CSV（requests + 重試）
│  ├─ parser_cleaner.py         # 讀取 CSV、清理資料、加上 df_name
│  ├─ combiner.py               # 合併、過濾、統計（輸出 filter.csv、count.csv）
│  ├─ sink_es.py                # 寫入 Elasticsearch（bulk）
│  ├─ runner.py                 # 串接整個流程
│  └─ docker-compose.yml        # 本地 ES + Kibana 環境
│
├─ tests/
│  ├─ test_manifest.py
├─ .env                         
└─ README.md
```

---

## 🗺️ 資料流程

```mermaid
flowchart LR
    A[manifest.py
產生季別任務] --> B[fetcher.py
下載 CSV]
    B --> C[parser_cleaner.py
清理欄位、格式化數值、加 df_name]
    C --> D[combiner.py
合併與統計]
    D -->|filter.csv| E[sink_es.py
批次寫入 Elasticsearch]
    E --> F[(Kibana Dashboard)]
```

---

## ✅ 先決條件

- Python **3.10+**
- **pip** / **virtualenv**
- **Docker Desktop**（本地 ES + Kibana）
- Git

---

## 🚀 快速開始

### 1) 下載專案並建立虛擬環境

```bash
git clone https://github.com/<your-username>/real-estate-crawler.git
cd real-estate-crawler

# Linux/macOS
python3 -m venv .venv && source .venv/bin/activate

# Windows PowerShell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

### 2) 安裝套件

```bash
pip install -U pip
pip install -r requirements.txt
# 或者
pip install requests pandas elasticsearch python-dotenv
```

### 3) 建立 `.env`

在專案根目錄新增 `.env`，或以 `.env.example` 為模板：

```ini
# ---- 檔案輸出 ----
DATA_DIR=data
OUTPUT_DIR=output

# ---- 下載來源 ----
BASE_URL=https://plvr.land.moi.gov.tw/DownloadSeason

```

### 4) 啟動 Elasticsearch + Kibana

```bash
cd src
docker compose -f docker-compose.yml up -d
```

- ES: http://localhost:9200  
- Kibana: http://localhost:5601  

### 5) 執行流程

```bash
python -m rec.runner
```

輸出結果：
- `src/rec/output/filter.csv`
- `src/rec/output/count.csv`
- Elasticsearch index（預設：`land_filter`）

---

## 🧪 測試

```bash
pytest -q
pytest --cov=src --cov-report=term-missing
```

---

## 📝 Commit 規範（Conventional Commits）

```
feat(manifest): 新增 generate_tasks 功能
fix(parser): 修正第二列缺失時的欄位處理
test(sink_es): 增加 bulk 失敗情境測試
docs(readme): 補充 Kibana 使用說明
```

---

