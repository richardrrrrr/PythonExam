from __future__ import annotations
import os, io, re
from typing import List, Dict, Tuple
import pandas as pd

NEEDED_CN = ["主要用途", "建物型態", "總樓層數", "總價元", "車位總價元", "交易筆棟數"]

def _read_csv_with_utf8(path: str) -> pd.DataFrame:
    """讀取 CSV（固定使用 UTF-8 編碼）"""
    # 讀取 CSV 檔案並轉換成 DataFrame
    # - header=None ：不把第一列當作欄位名稱（因為第1列中文，第2列英文，要自行處理）
    # - dtype=str   ：所有資料先讀成字串，避免中文數字/混合格式造成型別錯誤
    # - encoding="utf-8" ：確保中文能正確解碼，不會出現亂碼
    return pd.read_csv(path, header=None, dtype=str, encoding="utf-8")

def _zh_en_mapping(df_raw: pd.DataFrame) -> Dict[str, str]:
    """
    由第一列(中文)與第二列(英文)建立對應：中文 -> 英文欄位名
    """
    # 取出第 0 列 (中文欄位名稱) 與第 1 列 (英文欄位名稱)，轉成 list
    zh = df_raw.iloc[0].tolist()
    en = df_raw.iloc[1].tolist()
    mapping = {}
    for z, e in zip(zh, en):
        # z.strip()：去掉頭尾的空白字元，避免 ' 總價元 ' 這種情況
        # 在 if 條件中，strip() 也能用來檢查字串是否非空（空字串會變 False）
        if isinstance(z, str) and isinstance(e, str) and z.strip() and e.strip():
            # 雖然 zip(zh, en) 會把兩個 list 配對成 tuple，但 tuple 只能靠 index 查詢，不方便使用，因此改成 dict (mapping)，讓我們能用 key 直接查 value
            mapping[z.strip()] = e.strip()
    return mapping

_CN_NUM = {"零":0,"〇":0,"○":0,"一":1,"二":2,"兩":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}
_CN_UNIT = {"十":10}

def _cn_numeral_to_int(s: str) -> int | None:
    """
    轉中文數字（常見格式：十三層、二十層、三十一層）為 int。
    """
    if not isinstance(s, str):
        return None
    
    # 將輸入字串清理成「純中文數字」：
    # re.sub(r"[^\u4e00-\u9fff]", "", s)：移除所有非中文字元（只保留中文）
    # .replace("層", "")：去掉「層」
    t = re.sub(r"[^\u4e00-\u9fff]", "", s).replace("層","")
    if not t:
        return None

    total = 0
    num = 0
    unit_found = False
    saw_any_valid = False   # 是否看過任何合法數字/單位
    for ch in t:
        if ch in _CN_NUM:
            num = _CN_NUM[ch]
            saw_any_valid = True
        elif ch in _CN_UNIT:
            unit_found = True
            saw_any_valid = True
            unit = _CN_UNIT[ch]
            if num == 0:
                total += unit
            else:
                total += num * unit
            num = 0
        else:
            # 未知字，忽略
            pass
    total += num

    # 若整串沒有任何合法字元，回 None；否則回 total
    return total if saw_any_valid else None

def read_csv_file(path: str,df_name: str) -> pd.DataFrame:
    """
    讀取 MOI CSV：第一列中文、第二列英文；以「第二列英文」設為欄位名。
    並複製出題目需要的中文欄位（以便第 3 點用中文名過濾），加上 df_name，
    並產生「總樓層數_數值」欄位（中文數字轉整數）。
    """
    raw = _read_csv_with_utf8(path)
    #shape: 看 DataFrame 的結構大小，回傳tuple(rows, cols)，shape[0]是列數，shape[1]是欄數
    if raw is None or raw.shape[0] < 2:
        raise ValueError(f"CSV 結構異常：{path}")
    
    zh2en = _zh_en_mapping(raw)
    #iloc: 根據位置取出資料，回傳DataFrame / Series / 值
    en_header = raw.iloc[1].tolist()
    df = raw.iloc[2:].copy()
    # 這裡把第 2 列取出的英文標題 (en_header) 指定為真正的欄位名稱
    df.columns = en_header

    for c in df.columns:
        df[c] = df[c].astype(str)

    # 在 DataFrame 裡加一個新的欄位，名字叫做 "df_name"，裡面的值全部都填入變數 df_name
    df["df_name"] = df_name

    for cn in NEEDED_CN:
        en = zh2en.get(cn)
        if en and en in df.columns: 
        # DataFrame 用 df["欄位名"] 存取欄位，不是列
        # 這裡 cn 是中文欄位名（原本不存在 → 新增）
        # en 是英文欄位名（已存在 → 資料來源）
        # 效果：新增一個中文欄位，內容與英文欄位相同

            df[cn] = df[en] 
        else:
            # 找不到就建空欄位，避免 KeyError
            df[cn] = None

    for col in ["總價元", "車位總價元", "交易筆棟數"]:
        if col in df.columns:
            # str.replace 預設 regex=True → 把模式當正則表達式解析
            # 這裡加 regex=False 是明確指定「單純字串替換」，避免 "." "*" 等符號被誤解
            # 最後用 pd.to_numeric 嘗試轉換為數值，(errors="coerce")代表轉換失敗則回傳 NaN 
            df[col] = pd.to_numeric(df[col].str.replace(",", "", regex=False), errors="coerce")

    # 樓層數字化
    if "總樓層數" in df.columns:
        # .apply(func) 會對 Series 中的每個元素執行指定函式，回傳新 Series
        df["總樓層數_數值"] = df["總樓層數"].apply(_cn_numeral_to_int)
    else:
        df["總樓層數_數值"] = None

    return df