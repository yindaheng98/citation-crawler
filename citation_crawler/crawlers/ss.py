import logging
import re
import os

from .common import fetch_item, download_item, getenv_int

logger = logging.getLogger("semanticscholar")


async def search_by_title(title: str) -> str:
    title = re.sub(r'\s+', ' ', title.lower().strip())
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?limit=1&query={title}"
    data = await fetch_item(url)
    if 'data' not in data:
        return None
    data = data['data']
    if len(data) <= 0:
        return None
    data = data[0]
    if 'paperId'not in data or 'title'not in data:
        return None
    paperId = data['paperId']
    data['title'] = re.sub(r'\s+', ' ', data['title'].lower().strip())
    if data['title'] != title:
        logger.info(f'"{data["title"]}" is not "{title}"')
        return None
    return paperId


root_references = "semanticscholar/references"


async def get_references(paperId: str) -> str:
    cache_days = getenv_int('DBLP_CRAWLER_MAX_CACHE_DAYS_JOURNAL')
    cache_days = cache_days if cache_days is not None else 300
    paperId = paperId.lower()
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paperId}/references"
    data = await download_item(url, os.path.join(root_references, f"{paperId}.json"), cache_days)
    if 'data' not in data:
        return []
    data = data['data']
    return [d['citedPaper']['paperId'] for d in data]
