from __future__ import annotations
from typing import Iterable, Dict, Any, Optional
import math

def push_dataframe_to_es(df, *, index: str, es_host: str,
                         username: Optional[str] = None,
                         password: Optional[str] = None,
                         verify_certs: bool = False,
                         batch_size: int = 1000) -> int:
    """
    將 DataFrame 批次寫入 Elasticsearch。
    - 欄位可含中文（ES 支援），Kibana 可直接讀取。
    - 返回成功寫入的文件數。
    """
    try:
        from elasticsearch import Elasticsearch, helpers
    except Exception as e:
        raise RuntimeError("請先安裝 elasticsearch 套件：pip install elasticsearch") from e
    
    if username and password:
        es = Elasticsearch(es_host, basic_auth=(username, password), verify_certs=verify_certs)
    else:
        es = Elasticsearch(es_host, verify_certs=verify_certs)

    # 將 DataFrame 轉換為「list of dict」，每一列資料對應一個 dict
    records = df.to_dict(orient="records")
    total = len(records)
    success = 0

    for start in range(0, total, batch_size):
        # list[start:end:step]
        chunk = records[start:start + batch_size]
        # _index → Elasticsearch 裡要存到哪個 index（就像資料庫的「表名」）
        # _source → 這筆資料的實際內容
        actions = ({"_index": index, "_source": rec} for rec in chunk)
        # 呼叫 Elasticsearch 的 bulk API，一次寫入多筆文件
        # - actions: 包含每筆文件的 "_index" 與 "_source"
        # - ok: 成功寫入的文件數
        # - _: 錯誤資訊 (這裡忽略不用，所以用 "_" 命名)
        # - raise_on_error=False: 即使有寫入失敗的文件，也不中斷程式
        ok, _ = helpers.bulk(es, actions, raise_on_error=False)
        success += ok
    return success