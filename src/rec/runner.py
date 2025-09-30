from __future__ import annotations
import asyncio
import os
import time
from typing import List
import pandas as pd

from . import config
from .manifest import generate_tasks
from .fetcher import download_tasks
from .parser_cleaner import read_csv_file
from .combiner import combine_all, apply_filters, aggregate_counts, export_results
from .sink_es import push_dataframe_to_es

async def run(all_seasons: bool = True) -> None:
    """
    主流程：
      1) 產生任務清單（只含 X_lvr_land_X 主檔）
      2) 下載 CSV 至 {DATA_DIR}/{season}/
      3) 讀取每個 CSV：用第二列英文為欄位名 + 加 df_name + 數值清理
      4) 合併、篩選、輸出 filter.csv / count.csv
      5) （可選）寫入 Elasticsearch（若 .env 設定了 ES_HOST）
    """
    config.ensure_directories()

    seasons = config.SEASONS if all_seasons else config.SEASONS[:1] 
    print(f"測試季度：{seasons}")
    
    tasks = generate_tasks(seasons=seasons)
    print(f"產生 {len(tasks)} 個任務")

    # 2) 下載
    t0 = time.perf_counter()
    paths = await download_tasks(tasks, base_dir=config.DATA_DIR)
    print(f"整個 fetcher.py 總耗時: {time.perf_counter() - t0:.2f} 秒")

    # 建 df_name 查表： (season, file_name) -> df_name
    dfname_map = {(t["season"], t["file_name"]): t["df_name"] for t in tasks}

    # 3) 讀取與清理 - 加入除錯
    dfs: List[pd.DataFrame] = []
    for i, p in enumerate(paths):
        try:
            print(f"處理檔案 {i+1}/{len(paths)}: {p}")
            
            # 檢查檔案大小
            file_size = os.path.getsize(p)
            print(f"  檔案大小: {file_size} bytes")
            
            
            file_name = os.path.basename(p)
            season = os.path.basename(os.path.dirname(p))
            df_name = dfname_map.get((season, file_name), None) or "UNKNOWN"
            
            df = read_csv_file(p, df_name=df_name)
            
            
            # 檢查是否有重複的欄位名稱
            duplicated_cols = df.columns.duplicated()
            if duplicated_cols.any():
                # 處理重複欄位：加上後綴
                df.columns = [f"{col}_{i}" if dup else col for i, (col, dup) in enumerate(zip(df.columns, duplicated_cols))]
            
            dfs.append(df)
            
        except Exception as e:
            # 檢查檔案內容的前幾行
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    first_lines = [f.readline() for _ in range(3)]
                print(f"  檔案前3行內容: {first_lines}")
            except Exception as read_err:
                print(f"  無法讀取檔案內容: {read_err}")
            continue

    if not dfs:
        print("錯誤：沒有成功讀取任何檔案")
        return

    print(f"成功讀取 {len(dfs)} 個 DataFrame")
    
    # 在合併前再次檢查每個 DataFrame
    for i, df in enumerate(dfs):
        print(f"DataFrame {i}: shape={df.shape}, columns={len(df.columns)}")
        if df.columns.duplicated().any():
            print(f"  仍有重複欄位: {df.columns[df.columns.duplicated()].tolist()}")

    # 4) 合併 / 篩選 / 輸出 CSV
    try:
        print("開始合併 DataFrame...")
        combined = combine_all(dfs)
        print(f"合併成功：{combined.shape}")
        
        filtered = apply_filters(combined)
        print(f"篩選後：{filtered.shape}")
        
        counts = aggregate_counts(filtered)
        filter_path, count_path = export_results(filtered, counts, out_dir=config.OUTPUT_DIR)
        print(f"[OK] 輸出: {filter_path}")
        print(f"[OK] 輸出: {count_path}")

        # 5) 寫入 ES 
        es_host = os.getenv("ES_HOST", "http://localhost:9200").strip()
        es_index = os.getenv("ES_INDEX", "land_filter").strip()

        if es_host:
            try:
                ok = push_dataframe_to_es(filtered, index=es_index, es_host=es_host)
                print(f"[OK] 已寫入 Elasticsearch：{ok} 筆（index={es_index}）")
            except Exception as e:
                print(f"[WARN] 寫入 ES 失敗：{e}")
                
    except Exception as e:
        print(f"合併失敗: {e}")
        return

if __name__ == "__main__":
    asyncio.run(run(all_seasons=True))