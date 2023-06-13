import abc
import asyncio
import logging
from itertools import combinations, chain
from aiostream import stream
from typing import Optional, Iterable


logger = logging.getLogger("graph")


class Crawler(metaclass=abc.ABCMeta):
    def __init__(self, paperId_list: list[str]) -> None:
        self.paperId_checked: dict[str, bool] = {paperId: False for paperId in paperId_list}

    @abc.abstractmethod
    async def get_references(self, paperId: str) -> Iterable[str]:
        """获取某篇论文的引文"""
        yield paperId

    @abc.abstractmethod
    def filter_papers(self, paperIds: Iterable[str]) -> Iterable[str]:
        """在收集信息时过滤`Paper`，不会对被此方法过滤掉的`Paper`进行信息收集"""
        for paperId in paperIds:
            yield paperId

    async def bfs_once(self) -> int:
        iters = []
        init_paper_count = 0
        for paperId, checked in list(self.paperId_checked.items()):
            if not checked:
                init_paper_count += 1
                iters.append(self.get_references(paperId))
                self.paperId_checked[paperId] = True
        logger.info("Initializing %s papers" % init_paper_count)
        new_paperIds = set()
        async with stream.merge(*iters).stream() as streamer:
            async for new_paperId in streamer:
                new_paperIds.add(new_paperId)

        new_paper_count = 0
        for paperId in self.filter_papers(new_paperIds):
            if paperId not in self.paperId_checked:
                self.paperId_checked[paperId] = False
                new_paper_count += 1
        logger.info("Added %s new papers" % new_paper_count)
        return new_paper_count


class Summarizer(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        pass

    @abc.abstractmethod
    def filter_papers(self, papers: Iterable[dict]) -> Iterable[dict]:
        """在输出时过滤`Paper`，被过滤掉的`Paper`将不会出现在输出中"""
        for paper in papers:
            yield paper
