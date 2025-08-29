from __future__ import annotations
import os
import pandas as pd
from typing import List, Tuple
from .config import OUTPUT_DIR

FILTER_CSV = "filter.csv"
COUNT_CSV = "count.csv"

def combine_all(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    """
    合併所有 DataFrame - 由於只保留需要的欄位，這裡變得很簡單
    """
    if not dfs:
        return pd.DataFrame()
    
    
    # enumerate 是 Python 的內建函式，用來 在迴圈中同時取得索引 (index) 和元素 (value)
    for i, df in enumerate(dfs):
        print(f"  DataFrame {i+1}: {df.shape}, 欄位: {list(df.columns)}")
   
    try:
        # 一次性合併：
        # 直接把 dfs (list of DataFrame) 丟進 pd.concat，效率高，但若其中一個 DataFrame 有問題可能整批失敗
        result = pd.concat(dfs, ignore_index=True, sort=False)
        print(f"  合併成功: {result.shape}")
        return result
    except Exception as e:
        print(f"  合併失敗: {e}")
        # 即使失敗，也嘗試逐一合併
        result = dfs[0].copy()
        for i in range(1, len(dfs)):
            try:
                # 逐步合併：
                # 每次只合併「目前結果 result」和「下一個 DataFrame」，雖然效率較低，但能配合 try/except 容錯
                result = pd.concat([result, dfs[i]], ignore_index=True, sort=False)
                print(f"  ✓ 成功合併 DataFrame {i+1}")
            except Exception as merge_err:
                print(f"  ✗ 跳過 DataFrame {i+1}: {merge_err}")
                continue
        return result

def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    篩選條件（簡化版 - 欄位保證存在）
    """
    if df.empty:
        return df
    
    
    # 條件1: 主要用途 = 住家用
    cond1 = (df["主要用途"] == "住家用")
    
    # 條件2: 建物型態包含「住宅大樓」
    cond2 = df["建物型態"].str.contains("住宅大樓", na=False)
    
    # 條件3: 總樓層數 >= 13
    cond3 = df["總樓層數_數值"] >= 13
    
    # 綜合條件
    final_condition = cond1 & cond2 & cond3
    
    return df[final_condition].copy()

def aggregate_counts(filtered: pd.DataFrame) -> pd.DataFrame:
    """
    統計資訊（簡化版）
    """
    if filtered.empty:
        return pd.DataFrame([{
            "總件數": 0,
            "總車位數": 0,
            "平均總價元": 0,
            "平均車位總價元": 0
        }])
    
    # 所有欄位都保證存在且型別正確
    total_count = len(filtered)
    total_parking = filtered["交易筆棟數"].sum()
    avg_total_price = filtered["總價元"].mean()
    avg_parking_price = filtered["車位總價元"].mean()

    result = pd.DataFrame([{
        "總件數": int(total_count),
        "總車位數": int(total_parking),
        "平均總價元": float(avg_total_price),
        "平均車位總價元": float(avg_parking_price)
    }])
    
    print(f"  統計結果: {result.iloc[0].to_dict()}")
    return result

def export_results(filtered: pd.DataFrame, counts: pd.DataFrame, out_dir: str = OUTPUT_DIR) -> Tuple[str, str]:
    """
    匯出結果
    """
    os.makedirs(out_dir, exist_ok=True)
    filter_path = os.path.join(out_dir, FILTER_CSV)
    count_path = os.path.join(out_dir, COUNT_CSV)
    
    # 用 utf-8-sig 方便 Excel 開啟
    filtered.to_csv(filter_path, index=False, encoding="utf-8-sig")
    counts.to_csv(count_path, index=False, encoding="utf-8-sig")
    
    print(f"  匯出 filter.csv: {filtered.shape[0]} 筆資料")
    print(f"  匯出 count.csv: 統計摘要")
    
    return filter_path, count_path