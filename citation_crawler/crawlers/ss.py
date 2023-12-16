import logging
import re
import os
import json
from typing import AsyncIterable, Iterable, Optional, Tuple, Dict, List
from urllib.parse import urlparse

from citation_crawler import Crawler, Author, Paper
from .common import download_item, getenv_int

logger = logging.getLogger("semanticscholar")


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

    def dblp_name(self) -> Optional[List[str]]:
        if 'externalIds' in self.data and self.data['externalIds'] and 'DBLP' in self.data['externalIds']:
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


async def download_list(url: str, path: str, cache_days: int):
    def list_data_is_valid(text):
        data = json.loads(text)
        if 'data' in data:
            return True
        raise ValueError(f"Invalid list data: {text}")
    text = await download_item(url, path, cache_days, list_data_is_valid)
    if not text:
        return
    return json.loads(text)


fields_authors = "externalIds,name,affiliations"
root_authors = f"semanticscholar/authors--{fields_authors.replace(',', '-')}"


async def get_authors(paperId: str) -> Iterable[Author]:
    cache_days = getenv_int('CITATION_CRAWLER_MAX_CACHE_DAYS_AUTHORS')
    cache_days = cache_days if cache_days is not None else -1
    paperId = paperId.lower()
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paperId}/authors?fields={fields_authors}"
    data = await download_list(url, os.path.join(root_authors, f"{paperId}.json"), cache_days)
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

    def date(self) -> Optional[int]:
        if 'publicationDate' in self.data:
            return self.data['publicationDate']

    def doi(self) -> Optional[str]:
        if 'externalIds' in self.data and 'DOI' in self.data['externalIds']:
            doi = self.data['externalIds']['DOI']
            u = urlparse(doi)
            doi = re.sub(r"^/+", "", u.path)
            return doi

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

    async def authors_kv(self) -> Iterable[Tuple[str, str]]:
        async for author in self.authors():
            if author.dblp_pid():
                yield "dblp_pid", author.dblp_pid()
            if author.authorId():
                yield "authorId", author.authorId()


fields_references = f"title,year,authors,externalIds,publicationTypes,journal"
root_references = f"semanticscholar/references--{fields_references.replace(',', '-')}"
root_citations = f"semanticscholar/citations--{fields_references.replace(',', '-')}"


async def get_references(paperId: str) -> Iterable[SSPaper]:
    cache_days = getenv_int('CITATION_CRAWLER_MAX_CACHE_DAYS_REFERENCES')
    cache_days = cache_days if cache_days is not None else -1
    paperId = paperId.lower()
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paperId}/references?fields={fields_references}"
    data = await download_list(url, os.path.join(root_references, f"{paperId}.json"), cache_days)
    if not data or 'data' not in data:
        return
    data = data['data']
    for d in data:
        if 'citedPaper' in d and 'paperId' in d['citedPaper'] and d['citedPaper']['paperId']:
            yield SSPaper(d['citedPaper'])


async def get_citations(paperId: str) -> Iterable[SSPaper]:
    cache_days = getenv_int('CITATION_CRAWLER_MAX_CACHE_DAYS_CITATIONS')
    cache_days = cache_days if cache_days is not None else 7
    paperId = paperId.lower()
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paperId}/citations?fields={fields_references}"
    data = await download_list(url, os.path.join(root_citations, f"{paperId}.json"), cache_days)
    if not data or 'data' not in data:
        return
    data = data['data']
    for d in data:
        if 'citingPaper' in d and 'paperId' in d['citingPaper'] and d['citingPaper']['paperId']:
            yield SSPaper(d['citingPaper'])


async def download_paper(url: str, path: str, cache_days: int):
    def paper_is_valid(text):
        data = json.loads(text)
        if 'paperId' in data:
            return True
        raise ValueError(f"Invalid paper data: {text}")
    text = await download_item(url, path, cache_days, paper_is_valid)
    if not text:
        return
    return json.loads(text)


fields_authors_sub = ','.join([("authors." + f) for f in fields_authors.split(',')])
fields_paper = f"title,year,publicationDate,{fields_authors_sub},externalIds,publicationTypes,journal"
root_paper = f"semanticscholar/paper--{fields_paper.replace(',', '-')}"


async def get_paper(paperId: str) -> Optional[SSPaper]:
    def paperId2path(paperId):
        return paperId.replace(":", "/")
    cache_days = getenv_int('CITATION_CRAWLER_MAX_CACHE_DAYS_PAPER')
    cache_days = cache_days if cache_days is not None else -1
    paperId = paperId.lower()
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paperId}?fields={fields_paper}"
    data = await download_paper(url, os.path.join(root_paper, f"{paperId2path(paperId)}.json"), cache_days)
    if not data or 'paperId' not in data or data['paperId'].lower() != paperId:
        return None
    return SSPaper(data)


fields_author = "paperId,title"
root_author = f"semanticscholar/author--{fields_author.replace(',', '-')}"


async def get_paperIds_by_authorId(authorId: str) -> List[str]:
    cache_days = getenv_int('CITATION_CRAWLER_MAX_CACHE_DAYS_INIT_AUTHOR')
    cache_days = cache_days if cache_days is not None else 7
    authorId = authorId.lower()
    url = f"https://api.semanticscholar.org/graph/v1/author/{authorId}/papers?fields={fields_author}&limit=100"
    data = await download_list(url, os.path.join(root_author, f"{authorId}.json"), cache_days)
    if not data or 'data' not in data:
        return
    for paper in data['data']:
        yield paper['paperId'].lower()


class SemanticScholarCrawler(Crawler):

    def __init__(self, authorId_list: list[str], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.authors = authorId_list

    async def get_init_paperIds(self):
        for author in self.authors:
            async for paperId in get_paperIds_by_authorId(author):
                yield paperId

    async def get_paper(self, paperId):
        return await get_paper(paperId)

    async def get_references(self, paper):
        async for paper in get_references(paper.paperId()):
            yield paper

    async def get_citations(self, paper):
        async for paper in get_citations(paper.paperId()):
            yield paper

    async def match_authors(self, paper: SSPaper, authors: AsyncIterable[Dict]) -> AsyncIterable[Tuple[Dict, Dict, bool]]:
        dblp_names, authorIds = {}, {}
        async for author in paper.authors():
            if author.dblp_name():
                for name in author.dblp_name():
                    dblp_names[name] = author
            if author.authorId():
                authorIds[author.authorId()] = author
        async for author in authors:
            if 'authorId' in author:
                if author['authorId'] in authorIds:
                    write_fields = {}
                    author_kv = {"authorId": author['authorId']}
                    yield author_kv, write_fields, None
                else:  # if there is an author in database but is not really an author
                    # should unlink the author
                    division_kv = {"authorId": author['authorId']}
                    if 'name' in author and author['name'] in dblp_names:
                        ss_author = dblp_names[author['name']]
                        author_kv = {"authorId": ss_author.authorId()}
                        yield author_kv, {}, division_kv
            elif 'name' in author and author['name'] in dblp_names:
                ss_author = dblp_names[author['name']]
                write_fields = {"authorId": ss_author.authorId()}
                author_kv = {"dblp_pid": author["dblp_pid"]}
                yield author_kv, write_fields, None
