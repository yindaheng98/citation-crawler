import logging
import re
import os
from typing import Iterable, Optional

from citation_crawler import Crawler, Author, Paper
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


class SSAuthor(Author):
    def __init__(self, data) -> None:
        super().__init__()
        self.data = data

    def authorId(self) -> str:
        if 'authorId' in self.data:
            return self.data['authorId']

    def name(self) -> Optional[str]:
        if 'name' in self.data:
            return self.data['name']

    def dblp_pid(self) -> Optional[str]:
        return None

    def dblp_name(self) -> Optional[str]:
        if 'externalIds' in self.data and 'DBLP' in self.data['externalIds']:
            return self.data['externalIds']['DBLP']

    def __dict__(self) -> dict:
        d = {}
        if self.authorId():
            d['authorId'] = self.authorId()
        if self.name():
            d['name'] = self.name()
        if self.dblp_name():
            d['dblp_name'] = self.dblp_name()
        return d


fields_authors = "externalIds,name,affiliations"
root_authors = f"semanticscholar/authors--{fields_authors.replace(',', '-')}"


async def get_authors(paperId: str) -> Iterable[Author]:
    cache_days = getenv_int('CITATION_CRAWLER_MAX_CACHE_DAYS_AUTHORS')
    cache_days = cache_days if cache_days is not None else 300
    paperId = paperId.lower()
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paperId}/authors?fields={fields_authors}"
    data = await download_item(url, os.path.join(root_authors, f"{paperId}.json"), cache_days)
    if not data or 'data' not in data:
        return
    for a in data['data']:
        yield SSAuthor(a)


class SSPaper(Paper):
    def __init__(self, data) -> None:
        super().__init__()
        self.data = data

    def paperId(self) -> str:
        return self.data['paperId']

    def dblp_id(self) -> Optional[str]:
        if 'externalIds' in self.data and 'DBLP' in self.data['externalIds']:
            return self.data['externalIds']['DBLP']

    def title(self) -> Optional[str]:
        if 'title' in self.data:
            return self.data['title']

    def year(self) -> Optional[int]:
        if 'year' in self.data:
            return self.data['year']

    def doi(self) -> Optional[str]:
        if 'externalIds' in self.data and 'DOI' in self.data['externalIds']:
            return self.data['externalIds']['DOI']


fields_references = f"title,year,authors,externalIds,publicationTypes,journal"
root_references = f"semanticscholar/references--{fields_references.replace(',', '-')}"


async def get_references(paperId: str) -> Iterable[SSPaper]:
    cache_days = getenv_int('CITATION_CRAWLER_MAX_CACHE_DAYS_REFERENCES')
    cache_days = cache_days if cache_days is not None else 300
    paperId = paperId.lower()
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paperId}/references?fields={fields_references}"
    data = await download_item(url, os.path.join(root_references, f"{paperId}.json"), cache_days)
    if not data or 'data' not in data:
        return
    data = data['data']
    for d in data:
        yield SSPaper(d['citedPaper'])


fields_authors_sub = ','.join([("authors." + f) for f in fields_authors.split(',')])
fields_paper = f"title,year,{fields_authors_sub},externalIds,publicationTypes,journal"
root_paper = f"semanticscholar/paper--{fields_paper.replace(',', '-')}"


async def get_paper(paperId: str) -> Optional[SSPaper]:
    cache_days = getenv_int('CITATION_CRAWLER_MAX_CACHE_DAYS_PAPER')
    cache_days = cache_days if cache_days is not None else 300
    paperId = paperId.lower()
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paperId}?fields={fields_paper}"
    data = await download_item(url, os.path.join(root_paper, f"{paperId}.json"), cache_days)
    if not data or 'paperId' not in data or data['paperId'].lower() != paperId:
        return None
    return SSPaper(data)


class SemanticScholarCrawler(Crawler):
    def __init__(self, paperId_list: list[str]) -> None:
        super().__init__(paperId_list)
        self.papers = {}

    async def get_references(self, paperId):
        if paperId not in self.papers:
            self.papers[paperId] = await get_paper(paperId)
        async for paper in get_references(paperId):
            self.papers[paper.paperId()] = paper
            yield paper.paperId()
