"""
manifest.py
-----------
產生「任務清單（manifest）」的工具模組。

本模組依據題目規則，組合季別、交易類型、城市等條件，
自動生成一份包含所有待處理檔案資訊的清單（list of dict）。

每筆任務包含：
    - season (str): 季別字串，例如 "106S1"
    - year (str): 年份，例如 "106"
    - quarter (int): 季度，例如 1
    - city_name (str): 城市中文名稱，例如 "臺北市"
    - city_code (str): 城市代碼，例如 "A"
    - trade_type_name (str): 交易類型中文名稱，例如 "不動產買賣"
    - trade_code (str): 交易代碼，例如 "A"
    - file_name (str): 對應的檔案名稱，例如 "A_lvr_land_A.csv"
    - df_name (str): 資料框名稱規則，例如 "106_1_A_A"

用途：
    - 作為下載、資料載入（pandas）、合併處理、上傳（ElasticSearch）等流程的唯一依據
    - 集中管理命名規則與條件，避免重複編碼與規則分散
    - 支援過濾（指定季別、城市、交易類型），方便測試與局部執行

主要函式：
    - generate_tasks(): 依輸入條件生成任務清單
    - season_to_year_quarter(): 解析季別字串為年份與季度
    - build_file_name(): 依城市代碼與交易代碼產生檔名
    - build_df_name(): 依年份、季度、代碼產生 df_name

"""

from __future__ import annotations

from typing import Iterable, List, Dict, Optional, Tuple

from . import config

CITIES_FOR_A = ["臺北市", "新北市", "高雄市"]
CITIES_FOR_B = ["桃園市", "臺中市"]

def season_to_year_quarter(season: str) ->Tuple[str, int]:
    """
    將 '106S1' -> ('106', 1)
    """
    if "S" not in season:
        raise ValueError(f"Invalid season: {season}")
    year, quarter = season.split("S", 1)
    return year, int(quarter)
