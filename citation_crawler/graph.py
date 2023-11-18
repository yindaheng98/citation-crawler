import abc
import logging
import asyncio
from typing import Any, Tuple, Optional, Iterable, AsyncIterable

from .items import Paper


logger = logging.getLogger("graph")


class Crawler(metaclass=abc.ABCMeta):
    def __init__(self, paperId_list: list[str]) -> None:
        self.papers: dict[str, Paper] = {paperId: None for paperId in paperId_list}
        self.checked = set()
        self.ref_idx: dict[str, set[str]] = {}

    @abc.abstractmethod
    async def get_paper(self, paperId: str) -> Optional[Paper]:
        """获取某篇论文的详情"""
        return None

    @abc.abstractmethod
    async def get_references(self, paper: Paper) -> AsyncIterable[Paper]:
        """获取某篇论文的引文"""
        return

    @abc.abstractmethod
    async def filter_papers(self, papers: AsyncIterable[Paper]) -> AsyncIterable[Paper]:
        """
        在收集信息时过滤`Paper`，不会对被此方法过滤掉的`Paper`进行信息收集
        等同于dblp-crawler里的filter_publications_at_crawler
        """
        async for paper in papers:
            yield paper

    async def init_paper(self, paperId) -> Tuple[int, int]:
        init, refs = 0, 0
        if paperId not in self.papers or not self.papers[paperId]:
            paper = await self.get_paper(paperId)
            if not paper:
                return init, refs
            paperId = paper.paperId()
            init += 1
        else:
            paper = self.papers[paperId]
            paperId = paper.paperId()
        self.papers[paperId] = paper
        if paperId in self.checked:
            return init, refs
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
        self.checked.add(paperId)
        return init, refs

    async def bfs_once(self) -> int:
        tasks = [self.init_paper(paperId) for paperId in list(self.papers.keys())]
        total_init, total_refs = 0, 0
        for init, refs in await asyncio.gather(*tasks):
            total_init += init
            total_refs += refs
        logger.info("Initializing %s papers and %s refernces" % (total_init, total_refs))
        return total_init, total_refs


class Summarizer(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def filter_papers(self, papers: AsyncIterable[Paper]) -> AsyncIterable[Paper]:
        """
        在输出时过滤`Paper`，被过滤掉的`Paper`将不会出现在输出中
        等同于dblp-crawler里的filter_publications_at_output
        """
        async for paper in papers:
            yield paper

    @abc.abstractmethod
    async def write_paper(self, paper: Paper) -> None:
        pass

    @abc.abstractmethod
    async def write_reference(self, paper: Paper, reference: Paper) -> None:
        pass

    async def write(self, crawler: Crawler) -> None:
        exist_papers = set()
        async def wrapper(iter: Iterable[Paper]):
            for i in iter:
                yield i
        async for paper in self.filter_papers(wrapper(crawler.papers.values())):
            await self.write_paper(paper)
            exist_papers.add(paper.paperId())
        for paperId, refs_paperId in crawler.ref_idx.items():
            if paperId not in exist_papers:
                continue
            for ref_paperId in refs_paperId:
                if refs_paperId not in exist_papers:
                    continue
                await self.write_reference(crawler.papers[paperId], crawler.papers[ref_paperId])

    def __call__(self, crawler: Crawler) -> Any:
        return self.write(crawler)
