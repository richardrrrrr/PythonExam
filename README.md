一個端到端的 ETL 流程，負責下載內政部不動產成交案件 CSV 檔案，進行清理與合併，並將結果寫入 Elasticsearch，最後透過 Kibana 做視覺化分析。

✨ 功能特色
📥 Fetcher：可靠的 HTTP 下載（內建重試與退避）
🧹 Parser/Cleaner：取第二列作為欄名，數值標準化，加上 df_name
🧮 Combiner：合併季別 CSV，過濾與統計，輸出 filter.csv 與 count.csv
📦 Sink：批次寫入 Elasticsearch
🧭 Runner：一鍵執行整個流程
🧪 Tests：模組化的 pytest 測試，確保穩定性

📁 專案架構
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
│  ├─ test_parser_cleaner.py
│  ├─ test_combiner.py
│  ├─ test_fetcher.py
│  └─ test_sink_es.py
├─ .env                         
└─ README.md

🗺️ 資料流程
flowchart LR
    A[manifest.py\n產生季別任務] --> B[fetcher.py\n下載 CSV]
    B --> C[parser_cleaner.py\n清理欄位、格式化數值、加 df_name]
    C --> D[combiner.py\n合併與統計]
    D -->|filter.csv| E[sink_es.py\n批次寫入 Elasticsearch]
    E --> F[(Kibana Dashboard)]

✅ 先決條件

Python 3.10+
pip / virtualenv
Docker Desktop（本地 ES + Kibana）
Git

🚀 快速開始
1) 下載專案並建立虛擬環境
git clone https://github.com/<your-username>/real-estate-crawler.git
cd real-estate-crawler

# Linux/macOS
python3 -m venv .venv && source .venv/bin/activate

# Windows PowerShell
python -m venv .venv; .\.venv\Scripts\Activate.ps1

2) 安裝套件
pip install -U pip
pip install -r requirements.txt
# 或者
pip install requests pandas elasticsearch python-dotenv

3) 建立 .env

在專案根目錄新增 .env，範例如下：

BASE_URL=https://plvr.land.moi.gov.tw
DATA_DIR=src/rec/data
OUTPUT_DIR=src/rec/output
SEASONS=114S1,114S2
CITIES=A,B,E,F
TRADE_TYPES=A,B

4) 啟動 Elasticsearch + Kibana
cd src/rec
docker compose -f docker-compose.yml up -d
ES: http://localhost:9200
Kibana: http://localhost:5601

5) 執行流程
python -m rec.runner

輸出結果：
src/rec/output/filter.csv
src/rec/output/count.csv
Elasticsearch index (預設：land_filter)
