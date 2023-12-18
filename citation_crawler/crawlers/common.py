from typing import Optional, Dict, Callable
import os
from datetime import datetime, timedelta

import aiohttp
import logging
from aiofile import async_open
from asyncio import Semaphore

logger = logging.getLogger("common")


def getenv_int(key) -> int:
    cache_days = os.getenv(key)
    if cache_days is not None:
        try:
            return int(cache_days)
        except:
            pass
    return None


http_concorent = getenv_int('HTTP_CONCORRENT')
http_sem = Semaphore(http_concorent if http_concorent is not None else 8)
file_sem = Semaphore(512)


def get_cache_datetime(path) -> datetime:
    return datetime.fromtimestamp(os.path.getmtime(path))


async def download_item(url: str, path: str, cache_days: int, is_valid: Callable[[str], None]) -> Optional[Dict]:
    save_path = os.path.join("save", path)
    if os.path.isfile(save_path):
        if cache_days < 0 or datetime.now() < get_cache_datetime(save_path) + timedelta(days=cache_days):
            async with file_sem:
                try:
                    async with async_open(save_path, 'r') as f:
                        logger.debug("use cache: %s -> %s" % (path, url))
                        text = await f.read()
                    assert is_valid(text)
                    return text
                except:
                    logger.debug(" no cache: %s" % save_path)
                    if os.path.exists(save_path):
                        logger.info("err cache: %s" % save_path)
                        try:
                            os.remove(save_path)
                        except Exception as e:
                            logger.info(" rm cache: %s" % e)
        else:
            logger.info("old cache: %s" % save_path)

    async with http_sem:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                async with session.get(url,
                                       proxy=os.getenv("HTTP_PROXY"),
                                       timeout=os.getenv("HTTP_TIMEOUT") or 30) as response:
                    logger.debug(" download: %s <- %s" % (path, url))
                    text = await response.text()
                    assert is_valid(text)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    async with async_open(save_path, 'w') as f:
                        await f.write(text)
                    return text
        except Exception as e:
            logger.error(" down err: %s" % e)
    return None
