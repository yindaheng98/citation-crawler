import abc
import logging
import asyncio
from tqdm import tqdm
from typing import Any, Tuple, Optional, Iterable, AsyncIterable

from .items import Paper, Author


logger = logging.getLogger("graph")


class Crawler(metaclass=abc.ABCMeta):
    def __init__(self, paperId_list: list[str]) -> None:
        self._init_paper_list = paperId_list
        self.papers: dict[str, Paper] = {}
        self.checked = set()
        self.ref_idx: dict[str, set[str]] = {}
        self.inited = False

    @abc.abstractmethod
    async def get_init_paperIds(self) -> AsyncIterable[str]:
        """初始化"""
        return

    @abc.abstractmethod
    async def get_paper(self, paperId: str) -> Optional[Paper]:
        """获取某篇论文的详情"""
        return None

    @abc.abstractmethod
    async def get_references(self, paper: Paper) -> AsyncIterable[Paper]:
        """获取某篇论文的引文"""
        return

    @abc.abstractmethod
    async def get_citations(self, paper: Paper) -> AsyncIterable[Paper]:
        """获取引用某篇论文的论文"""
        return

    @abc.abstractmethod
    async def filter_papers(self, papers: AsyncIterable[Paper]) -> AsyncIterable[Paper]:
        """
        在收集信息时过滤`Paper`，不会对被此方法过滤掉的`Paper`进行信息收集
        等同于dblp-crawler里的filter_publications_at_crawler
        """
        async for paper in papers:
            yield paper

    @abc.abstractmethod
    async def match_authors(self, paper: Paper, authors: AsyncIterable[dict]) -> AsyncIterable[Tuple[dict, dict, bool]]:
        """
        This function will be called after Summarizer.get_corrlated_authors
        Return matched authors and the fields you want to write (in dict format)
        用于将数据库中的作者与爬到的作者进行匹配
        """
        async for author in authors:
            yield author, author

    async def init_paper(self, paperId) -> Tuple[int, int]:
        init, refs, cits = 0, 0, 0
        if paperId not in self.papers or not self.papers[paperId]:
            paper = await self.get_paper(paperId)
            if not paper:
                return init, refs, cits
            paperId = paper.paperId()
            init += 1
        else:
            paper = self.papers[paperId]
            paperId = paper.paperId()
        self.papers[paperId] = paper
        if paperId in self.checked:
            return init, refs, cits

        async for new_paper in self.filter_papers(self.get_references(paper)):
            if not new_paper:
                continue
            new_paperId = new_paper.paperId()
            if paperId not in self.ref_idx:
                self.ref_idx[paperId] = set()
            self.ref_idx[paperId].add(new_paperId)
            if new_paperId not in self.papers or not self.papers[new_paperId]:
                self.papers[new_paperId] = new_paper
                refs += 1

        async for new_paper in self.filter_papers(self.get_citations(paper)):
            if not new_paper:
                continue
            new_paperId = new_paper.paperId()
            if new_paperId not in self.ref_idx:
                self.ref_idx[new_paperId] = set()
            self.ref_idx[new_paperId].add(paperId)
            if new_paperId not in self.papers or not self.papers[new_paperId]:
                self.papers[new_paperId] = new_paper
                cits += 1

        self.checked.add(paperId)
        logger.info("There are %s refernces and %s citations in %s" % (refs, cits, paperId))
        return init, refs, cits

    async def bfs_once(self) -> int:
        tasks = [self.init_paper(paperId) for paperId in list(self.papers.keys())]
        if not self.inited:
            for paperId in self._init_paper_list:
                logger.info("Init paper: %s" % paperId)
                tasks.append(self.init_paper(paperId))
            async for paperId in self.get_init_paperIds():
                logger.info("Init paper: %s" % paperId)
                tasks.append(self.init_paper(paperId))
            self.inited = True
        total_init, total_refs, total_cits = 0, 0, 0
        for init, refs, cits in await asyncio.gather(*tasks):
            total_init += init
            total_refs += refs
            total_cits += cits
        logger.info("There are %d papers init in this loop" % total_init)
        logger.info("There are %d refernces and %d citations need init in next loop" % (total_refs, total_cits))
        return total_init, total_refs, total_cits


class Summarizer(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def filter_papers(self, papers: Iterable[Paper]) -> AsyncIterable[Paper]:
        """
        在输出时过滤`Paper`，被过滤掉的`Paper`将不会出现在输出中
        等同于dblp-crawler里的filter_publications_at_output
        """
        for paper in papers:
            yield paper

    @abc.abstractmethod
    async def write_paper(self, paper: Paper) -> None:
        pass

    @abc.abstractmethod
    async def write_reference(self, paper: Paper, reference: Paper) -> None:
        pass

    @abc.abstractmethod
    async def get_corrlated_authors(self, paper: Paper) -> AsyncIterable[dict]:
        """
        Return existing authors (in dict format) of a paper in database
        用于将数据库中的作者与爬到的作者进行匹配
        """
        async for author in paper.authors():
            yield author.__dict__()

    @abc.abstractmethod
    async def write_author(self, paper: Paper, author_kv: dict, write_fields: dict, division_kv: bool) -> None:
        pass

    async def write(self, crawler: Crawler) -> None:
        exist_papers = set()
        async for paper in self.filter_papers(tqdm(crawler.papers.values(), desc="Writing papers")):
            await self.write_paper(paper)
            async for author_kv, write_fields, division_kv in crawler.match_authors(paper, self.get_corrlated_authors(paper)):
                await self.write_author(paper, author_kv, write_fields, division_kv)
            exist_papers.add(paper.paperId())
        for paperId, refs_paperId in tqdm(crawler.ref_idx.items(), desc="Writing citations"):
            if paperId not in exist_papers:
                continue
            for ref_paperId in refs_paperId:
                if ref_paperId not in exist_papers:
                    continue
                await self.write_reference(crawler.papers[paperId], crawler.papers[ref_paperId])

    def __call__(self, crawler: Crawler) -> Any:
        return self.write(crawler)
