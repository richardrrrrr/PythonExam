import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ========== 基本路徑設定 ==========
# 資料下載存放資料夾
DATA_DIR: str = os.getenv("DATA_DIR", "data")
# 處理後輸出的資料夾
OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")

BASE_URL: str = os.getenv(
    "BASE_URL",
    "https://plvr.land.moi.gov.tw/DownloadOpenData"
)

CITIES: dict[str, str] = {
    "臺北市": "A",  
    "新北市": "F",
    "高雄市": "E",
    "桃園市": "H",
    "臺中市": "B",
}

TRADE_TYPE: dict[str, str] = {
    "不動產買賣": "A",
    "預售屋買賣": "B",
}

SEASONS: list[str] = []
# pyton的迴圈是左閉右開
for year in range(103,109):
    if year == 108:
        seasons_in_year = [1, 2]
    else:
        seasons_in_year = [1, 2, 3, 4]
    for s in seasons_in_year:
        SEASONS.append(f"{year}S{s}")

def ensure_directories() -> None:
    """
    確保 DATA_DIR 和 OUTPUT_DIR 資料夾存在
    """
    # 將 DATA_DIR 字串轉為 Path 物件，方便用物件方法操作路徑
    # 使用 pathlib.Path 物件的內建 mkdir() 方法建立資料夾
    #   parents=True  → 若上層資料夾不存在，會自動建立（類似 mkdir -p）
    #   exist_ok=True → 若資料夾已存在，不會報錯
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    # 測試 config 是否正確
    print("DATA_DIR:", DATA_DIR)
    print("OUTPUT_DIR:", OUTPUT_DIR)
    print("BASE_URL:", BASE_URL)
    print("CITY_CODES:", CITIES)
    print("TRADE_TYPE_CODES:", TRADE_TYPE)
    print("SEASONS:", SEASONS)
    ensure_directories()