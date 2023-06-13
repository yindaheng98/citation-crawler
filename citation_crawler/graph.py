import abc
import logging
import asyncio
from typing import Iterable, Tuple, Optional

from .items import Paper, Author


logger = logging.getLogger("graph")


class Crawler(metaclass=abc.ABCMeta):
    def __init__(self, paperId_list: list[str]) -> None:
        self.papers: dict[str, Paper] = {paperId: None for paperId in paperId_list}
        self.checked = set()

    @abc.abstractmethod
    async def get_paper(self, paperId: str) -> Optional[Paper]:
        """获取某篇论文的详情"""
        return None

    @abc.abstractmethod
    async def get_references(self, paper: Paper) -> Iterable[Paper]:
        """获取某篇论文的引文"""
        return

    @abc.abstractmethod
    def filter_papers(self, papers: Iterable[Paper]) -> Iterable[Paper]:
        """在收集信息时过滤`Paper`，不会对被此方法过滤掉的`Paper`进行信息收集"""
        for paper in papers:
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
        async for new_paper in self.get_references(paper):
            if not new_paper:
                continue
            new_paperId = new_paper.paperId()
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
        return total_init + total_refs


class Summarizer(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        pass

    @abc.abstractmethod
    def filter_papers(self, papers: Iterable[dict]) -> Iterable[dict]:
        """在输出时过滤`Paper`，被过滤掉的`Paper`将不会出现在输出中"""
        for paper in papers:
            yield paper
