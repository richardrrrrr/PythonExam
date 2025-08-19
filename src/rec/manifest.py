"""
manifest.py
-----------
產生「任務清單（manifest）」的工具模組。

本模組依據組合季別、交易類型、城市等條件，
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

def season_to_year_quarter(season: str) -> tuple[str, int]:
    """
    將 '106S1' -> ('106', 1)
    """
    if "S" not in season:
        raise ValueError(f"Invalid season: {season}")

    year_str, quarter_str = season.split("S", 1)

    year = int(year_str)
    quarter = int(quarter_str)

    if not (103 <= year <= 108):
        raise ValueError(f"Invalid year: {year}")
    if not (1 <= quarter <= 4):
        raise ValueError(f"Invalid quarter: {quarter}")
    if year == 108 and quarter not in (1, 2):
        raise ValueError(f"Invalid quarter {quarter} for year 108")

    return str(year), quarter


def build_file_name(city: str, trade_type: str) -> str:
    if not isinstance(city, str):
        raise TypeError(f"city must be a str, got {type(city).__name__}")
    if not isinstance(trade_type, str):
        raise TypeError(f"trade_type must be a str, got {type(trade_type).__name__}")
    
    return f"{city}_lvr_land_{trade_type}"

def build_df_name(year: str, quarter: int, city: str, trade_type: str) -> str:
    if not isinstance(year, str):
        raise TypeError(f"year must be a str, got {type(year).__name__}")
    if not isinstance(quarter, int):
        raise TypeError(f"quarter must be a int, got {type(quarter).__name__}")
    if not isinstance(city, str):
        raise TypeError(f"city must be a str, got {type(city).__name__}")
    if not isinstance(trade_type, str):
        raise TypeError(f"trade_type must be a str, got {type(trade_type).__name__}")
    
    return f"{year}_{quarter}_{city}_{trade_type}"

def _cities_for_trade(trade_type: str) -> List[str]:
    if not isinstance(trade_type, str):
        raise TypeError(f"trade_type must be a str, got {type(trade_type).__name__}")
    
    if trade_type == "不動產買賣":
        return CITIES_FOR_A
    if trade_type == "預售屋買賣":
        return CITIES_FOR_B
    
def generate_tasks(
    seasons: Optional[Iterable[str]] = None,
    include_cities: Optional[Iterable[str]] = None,
    include_trade_types: Optional[Iterable[str]] = None,
) -> List[Dict]:
    """
    依題目需求，產生要下載的目標清單（只列 X_lvr_land_X 主檔）。
    每筆包含：
      - season, year, quarter
      - city_name, city_code
      - trade_type_name, trade_code
      - file_name (X_lvr_land_X.csv)
      - df_name   (年_季_市碼_類別碼)
    """
    seasons = list(seasons) if seasons is not None else list(config.SEASONS)


    
    trade_types = ["不動產買賣", "預售屋買賣"]
    if include_trade_types:
        # 交集過濾
        #[表達式 for 變數 in 可迭代物件 if 條件]
        trade_types = [t for t in trade_types if t in set(include_trade_types)]
        if not trade_types:
            raise ValueError(f"[Warning] Invalid trade type: {trade_types}")

    tasks: List[Dict] = []

    for season in seasons:
        year, quarter = season_to_year_quarter(season)

        for trade_type_name in trade_types:
            trade_code = config.TRADE_TYPE[trade_type_name]
            # 依類型選城市
            candidate_cities = _cities_for_trade(trade_type_name)

            if include_cities:
                city_set = set(include_cities)
                candidate_cities = [c for c in candidate_cities if c in city_set]
                if not candidate_cities:
                    raise ValueError(f"No valid cities found for trade type: {include_cities}")

            for city_name in candidate_cities:
                city_code = config.CITIES[city_name]
                file_name = build_file_name(city_code, trade_code)
                df_name = build_df_name(year, quarter, city_code, trade_code)

                tasks.append({
                    "season": season,
                    "year": year,
                    "quarter": quarter,
                    "city_name": city_name,
                    "city_code": city_code,
                    "trade_type_name": trade_type_name,
                    "trade_code": trade_code,
                    "file_name": file_name,
                    "df_name": df_name,
                })
    tasks.sort(key=lambda t: (t["season"], t["trade_code"], t["city_code"]))
    return tasks