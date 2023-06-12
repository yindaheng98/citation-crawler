from typing import Optional, Dict
import os
from datetime import datetime, timedelta
import json

import aiohttp
import logging
from aiofile import async_open
from asyncio import Semaphore

logger = logging.getLogger("common")

http_sem = Semaphore(8)
file_sem = Semaphore(512)


def getenv_int(key) -> int:
    cache_days = os.getenv(key)
    if cache_days is not None:
        try:
            return int(cache_days)
        except:
            pass
    return None


async def fetch_item(url: str) -> Optional[Dict]:
    async with http_sem:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                async with session.get(url) as response:
                    logger.info("fetch url: %s" % url)
                    text = await response.text()
                    try:
                        return json.loads(text)
                    except Exception as e:
                        logger.error(" json err: %s: %s" % (e, text))
        except Exception as e:
            logger.error("fetch err: %s" % e)
    return None


def get_cache_datetime(path) -> datetime:
    return datetime.fromtimestamp(os.path.getmtime(path))


async def download_item(url: str, path: str, cache_days: int) -> Optional[Dict]:
    save_path = os.path.join("save", path)
    if os.path.isfile(save_path):
        if datetime.now() < get_cache_datetime(save_path) + timedelta(days=cache_days):
            async with file_sem:
                try:
                    async with async_open(save_path, 'r') as f:
                        logger.info("use cache: %s -> %s" % (path, url))
                        text = await f.read()
                        return json.loads(text)
                except:
                    logger.debug(" no cache: %s" % save_path)
        else:
            logger.info("old cache: %s" % save_path)

    async with http_sem:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                async with session.get(url) as response:
                    logger.info(" download: %s <- %s" % (path, url))
                    text = await response.text()
                    data = json.loads(text)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    async with async_open(save_path, 'w') as f:
                        await f.write(text)
                    return data
        except Exception as e:
            logger.error(" down err: %s" % e)
    return None
