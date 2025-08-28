from __future__ import annotations
import os, io, re
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np

# 只定義真正需要的欄位
REQUIRED_FIELDS = {
    "主要用途": "str",      # 篩選條件
    "建物型態": "str",      # 篩選條件  
    "總樓層數": "str",      # 需要轉換為數值
    "總價元": "float",      # 統計用
    "車位總價元": "float",  # 統計用
    "交易筆棟數": "float"   # 統計用
}

def _read_csv_with_utf8(path: str) -> pd.DataFrame:
    """讀取 CSV（固定使用 UTF-8 編碼）"""
    return pd.read_csv(path, header=None, dtype=str, encoding="utf-8")

def _zh_en_mapping(df_raw: pd.DataFrame) -> Dict[str, str]:
    """
    由第一列(中文)與第二列(英文)建立對應：中文 -> 英文欄位名
    """
    zh = df_raw.iloc[0].fillna('').tolist()
    en = df_raw.iloc[1].fillna('').tolist()
    
    mapping = {}
    for z, e in zip(zh, en):
        z_clean = str(z).strip()
        e_clean = str(e).strip()
        if z_clean and e_clean and z_clean != 'nan' and e_clean != 'nan':
            mapping[z_clean] = e_clean
    return mapping

def _cn_numeral_to_int(s: str) -> int:
    """轉中文數字為整數，失敗則回傳0"""
    if not isinstance(s, str) or not s.strip():
        return 0
    
    s = str(s).strip()
    
    # 處理中文數字
    cn_num = {"零":0,"一":1,"二":2,"兩":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10}
    
    # 移除「層」字
    s = s.replace("層", "")
    
    # 在 dict 上使用 in：檢查 s 是否為 dict 的「完整 key」
    # → 只有當 s 完全等於某個 key 時才會成立
    if s in cn_num:
        return cn_num[s]
    
    if s.startswith("十") and len(s) == 2:
        return 10 + cn_num.get(s[1], 0)
    
    # 處理「X十」或「X十X」格式
    # 在 str 上使用 in：檢查子字串是否存在於 s 之中
    # → 只要 "十" 出現在 s 的任意位置就會成立（部分比對）
    if "十" in s:
        parts = s.split("十")
        if len(parts) == 2:
            # "十五" → ["", "五"]
            # "二十" → ["二", ""]
            # "二十三" → ["二", "三"]
            left = cn_num.get(parts[0], 0) if parts[0] else 1
            right = cn_num.get(parts[1], 0) if parts[1] else 0
            return left * 10 + right
    
    return 0

def read_csv_file(path: str, df_name: str) -> pd.DataFrame:
    """
    讀取 MOI CSV，只保留需要的欄位
    """
    raw = _read_csv_with_utf8(path)
    
    if raw is None or raw.shape[0] < 2:
        raise ValueError(f"CSV 結構異常：{path}")
    
    zh2en = _zh_en_mapping(raw)
    
    # 取出資料部分（跳過前兩列標題）
    data_df = raw.iloc[2:].reset_index(drop=True)
    
    # 設定英文標題為欄位名（處理空值和無效值）
    en_header_raw = raw.iloc[1].tolist()
    en_header = []
    for i, col in enumerate(en_header_raw):
        #pd.isna(col) 檢查這個值是不是 缺失值
        if pd.isna(col) or str(col).strip() == '' or str(col).strip() == 'nan':
            en_header.append(f'col_{i}')
        else:
            en_header.append(str(col).strip())
    
    seen = {}
    unique_header = []
    for col in en_header:
        if col in seen:
            seen[col] += 1
            unique_header.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            unique_header.append(col)
    
    # 加上 [:len(data_df.columns)] 是為了避免欄位數超過實際 DataFrame 的欄數。
    data_df.columns = unique_header[:len(data_df.columns)]
    
    # **關鍵優化：只保留需要的欄位**
    result_data = {"df_name": df_name}
    
    for cn_field, field_type in REQUIRED_FIELDS.items():
        en_field = zh2en.get(cn_field)
        
        if en_field and en_field in data_df.columns:
            # .fillna('')把這欄裡的缺失值（NaN / None）填補成空字串 ''
            raw_data = data_df[en_field].fillna('').astype(str)
            
            if field_type == "float":
                
                cleaned_data = raw_data.str.replace(',', '', regex=False)
                cleaned_data = cleaned_data.replace(['', 'nan', 'None'], '0')
                # errors="coerce" → 若遇到非法值（如 "abc", "N/A"），不丟出錯誤，而是轉成 NaN
                result_data[cn_field] = pd.to_numeric(cleaned_data, errors='coerce').fillna(0.0)
            else:
                result_data[cn_field] = raw_data.replace(['nan', 'None'], '')
        else:
            # 如果原始資料中，REQUIRED_FIELDS欄位不存在，設定預設值
            row_count = len(data_df)
            if field_type == "float":
                result_data[cn_field] = [0.0] * row_count
            else:
                result_data[cn_field] = [''] * row_count
    
    # 建立新的 DataFrame（只包含需要的欄位）
    result_df = pd.DataFrame(result_data)
    
    # 處理樓層數轉換
    if "總樓層數" in result_df.columns:
        result_df["總樓層數_數值"] = result_df["總樓層數"].apply(_cn_numeral_to_int)
    else:
        result_df["總樓層數_數值"] = 0
    
    return result_df