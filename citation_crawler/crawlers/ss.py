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
        assert 'authorId' in self.data and self.data['authorId']

    def authorId(self) -> str:
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
        if 'authorId' in a and a['authorId']:
            yield SSAuthor(a)


class SSPaper(Paper):
    def __init__(self, data) -> None:
        super().__init__()
        self.data = data
        self.author_data = None
        assert 'paperId' in self.data and self.data['paperId']

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

    async def _get_authors_from_author_data(self) -> Iterable[Author]:
        if not self.author_data:
            authors = []
            async for author in get_authors(self.paperId()):
                authors.append(author)
            self.author_data = authors
        for author in self.author_data:
            yield author

    async def authors(self) -> Iterable[Author]:
        if 'authors' in self.data and len(self.data['authors']) >= 0:
            for a in self.data['authors']:
                if 'authorId' not in a or 'externalIds' not in a or not a['externalIds']:
                    async for author in self._get_authors_from_author_data():
                        yield author
                    return
            for a in self.data['authors']:
                yield SSAuthor(a)
        else:
            async for author in self._get_authors_from_author_data():
                yield author


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
        if 'citedPaper' in d and 'paperId' in d['citedPaper'] and d['citedPaper']['paperId' ]:
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

    async def get_paper(self, paperId):
        return await get_paper(paperId)

    async def get_references(self, paper):
        async for paper in get_references(paper.paperId()):
            yield paper
