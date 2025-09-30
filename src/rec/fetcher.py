import os
import time
import requests
import aiohttp
from typing import Iterable, Dict, List
from .config import BASE_URL, DATA_DIR, ensure_directories

DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 1.6 #指數退回

def build_download_url(season: str, file_name: str) -> str:
    """組下載連結：/DownloadSeason?season=YYYYSN&fileName=X_lvr_land_X.csv"""
    return f"{BASE_URL}?season={season}&fileName={file_name}"

def _write_bytes(path: str, content: bytes) -> None:
    # dirname:取出路徑中的「資料夾部分」，不包含檔案或最後一段名稱
    # "data/106S1/file.csv" -> "data/106S1"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)

async def download_file(url: str, dest_path: str,
                  *, timeout: int = DEFAULT_TIMEOUT,
                  max_retries: int = DEFAULT_RETRIES,
                  backoff: float = DEFAULT_BACKOFF) -> str:
    """下載單一檔案，含重試與回退。返回存檔路徑。"""
    last_err = None
    for attempt in range(max_retries):
        
            async with aiohttp.ClientSession() as session:
            # stream=True 表示回應的內容（Response body）不會一次性全部下載進記憶體，而是邊接收邊讀取。
                async with session.get(url,ssl=False, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"}) as resp:
                    try:    
                        resp.raise_for_status()
                        content = await resp.read()
                        _write_bytes(dest_path, content)
                        return dest_path
                    except Exception as e:
                        last_err = e
                        if attempt == max_retries - 1:
                            raise
                        time.sleep(backoff ** attempt)

async def download_tasks(tasks: Iterable[Dict], base_dir: str = DATA_DIR) -> List[str]:
    """
    依 manifest 產生的 tasks 逐一下載到：
      {DATA_DIR}/{season}/{file_name}
    下載存在就略過。
    回傳所有檔案的本地完整路徑清單。
    """
    
    ensure_directories()
    saved: List[str] = []
    for t in tasks:
        season = t["season"]
        file_name = t["file_name"]
        url = build_download_url(season, file_name)
        dest = os.path.join(base_dir, season, file_name)
        if not os.path.exists(dest):
            await download_file(url, dest)
        saved.append(dest)
    return saved
# 🧪 測試入口
if __name__ == "__main__":
    print(">>> Running fetcher test...")
    # ⚠️ 這裡請換成實際存在的季別和檔案名稱
    test_tasks = [
        {"season": "106S1", "file_name": "A_lvr_land_A.csv"},
    ]
    try:
        results = download_tasks(test_tasks)
        print("下載成功，檔案儲存位置：")
        for path in results:
            print(" -", path)
    except Exception as e:
        print("下載失敗:", e)