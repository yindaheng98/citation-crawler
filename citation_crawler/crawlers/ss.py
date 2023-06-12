import logging
import re
import os

from .common import fetch_item, download_item, getenv_int

logger = logging.getLogger("semanticscholar")


async def search_by_title(title: str) -> str:
    title = re.sub(r'\s+', ' ', title.lower().strip())
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?limit=1&query={title}"
    data = await fetch_item(url)
    if not data or 'data' not in data:
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


fields_authors = "externalIds,name,affiliations"
root_authors = f"semanticscholar/authors--{fields_authors.replace(',', '-')}"


async def get_authors(paperId: str) -> dict:
    cache_days = getenv_int('CITATION_CRAWLER_MAX_CACHE_DAYS_AUTHORS')
    cache_days = cache_days if cache_days is not None else 300
    paperId = paperId.lower()
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paperId}/authors?fields={fields_authors}"
    data = await download_item(url, os.path.join(root_authors, f"{paperId}.json"), cache_days)
    if not data or 'data' not in data:
        return []
    data = data['data']
    return data


fields_references = f"title,year,authors,externalIds,publicationTypes,journal"
root_references = f"semanticscholar/references--{fields_references.replace(',', '-')}"


async def get_references(paperId: str) -> dict:
    cache_days = getenv_int('CITATION_CRAWLER_MAX_CACHE_DAYS_REFERENCES')
    cache_days = cache_days if cache_days is not None else 300
    paperId = paperId.lower()
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paperId}/references?fields={fields_references}"
    data = await download_item(url, os.path.join(root_references, f"{paperId}.json"), cache_days)
    if not data or 'data' not in data:
        return []
    data = data['data']
    return [d['citedPaper'] for d in data]


fields_authors_sub = ','.join([("authors." + f) for f in fields_authors.split(',')])
fields_paper = f"title,year,{fields_authors_sub},externalIds,publicationTypes,journal"
root_paper = f"semanticscholar/paper--{fields_paper.replace(',', '-')}"


async def get_paper(paperId: str) -> dict:
    cache_days = getenv_int('CITATION_CRAWLER_MAX_CACHE_DAYS_PAPER')
    cache_days = cache_days if cache_days is not None else 300
    paperId = paperId.lower()
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paperId}?fields={fields_paper}"
    data = await download_item(url, os.path.join(root_paper, f"{paperId}.json"), cache_days)
    if not data or 'paperId' not in data or data['paperId'].lower() != paperId:
        return None
    return data
