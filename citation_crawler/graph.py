import abc
import logging
import asyncio
from tqdm.asyncio import tqdm
from typing import Any, Tuple, Optional, Iterable, AsyncIterable
import random
from dblp_crawler.gather import gather
from .items import Paper


logger = logging.getLogger("graph")


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


class Crawler(metaclass=abc.ABCMeta):
    def __init__(self, summarizer: Summarizer, paperId_list: list[str]) -> None:
        self.summarizer = summarizer
        self._init_paper_list = paperId_list
        self.papers: dict[str, Paper] = {}
        self.fetched = set()
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

    async def init_paper(self, paperId) -> Tuple[Optional[Paper], int]:
        # fetch论文
        if paperId not in self.papers:  # init时self.papers里肯定没有数据
            paper = await self.get_paper(paperId)
            if not isinstance(paper, Paper):
                return None, 0
            paperId = paper.paperId()
        else:  # init之后的文章肯定作为references或citations已经下载过了
            paper = self.papers[paperId]
            paperId = paper.paperId()
        self.papers[paperId] = paper

        # fetch references
        refs, cits = 0, 0
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

        # fetch citations
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

        logger.info("There are %s refernces and %s citations in %s" % (refs, cits, paperId))
        return paper, refs + cits

    async def _init_papers(self):
        tasks = []
        for paperId in self._init_paper_list:
            if paperId in self.fetched:
                continue
            self.fetched.add(paperId)
            logger.info("Init paper: %s" % paperId)
            tasks.append(self.init_paper(paperId))
        async for paperId in self.get_init_paperIds():
            if paperId in self.fetched:
                continue
            self.fetched.add(paperId)
            logger.info("Init paper: %s" % paperId)
            tasks.append(self.init_paper(paperId))
        random.shuffle(tasks)
        async for paper, news in tqdm(gather(*tasks), desc="Writing init papers", total=len(tasks)):
            yield paper, news

    async def _bfs_once(self) -> int:
        # 初始化
        if not self.inited:
            async for paper, news in self._init_papers():
                if isinstance(paper, Paper):
                    yield paper, news
            self.inited = True

        # 构造待fetch论文列表
        paperIds = []
        for paperId in list(self.papers.keys()):
            if paperId in self.fetched:
                continue
            self.fetched.add(paperId)
            paperIds.append(paperId)
            logger.info("Fetch paper: %s" % paperId)

        # 执行fetch论文
        tasks = [self.init_paper(paperId) for paperId in paperIds]
        random.shuffle(tasks)
        async for paper, news in tqdm(gather(*tasks), desc="Writing papers", total=len(tasks)):
            if isinstance(paper, Paper):
                yield paper, news

    async def bfs_once(self) -> None:
        total, total_news = 0, 0
        async for paper, news in self.summarizer.filter_papers(self._bfs_once()):
            total += 1
            total_news += news
            await self.summarizer.write_paper(paper)  # _bfs_once里面出来的每个paper都是新的，所以直接写入
            async for author_kv, write_fields, division_kv in self.match_authors(paper, self.summarizer.get_corrlated_authors(paper)):
                # _bfs_once里面出来的每个paper都是新的，所以直接写入
                await self.summarizer.write_author(paper, author_kv, write_fields, division_kv)
            for paperId, refs_paperId in list(self.ref_idx.items()):
                # _bfs_once里面出来的paper不能保证引文全部已获取到
                for ref_paperId in list(refs_paperId):
                    if not (paperId == paper.paperId() or ref_paperId == paper.paperId()):
                        continue  # 只写入相关的论文引文
                    if not (paperId in self.papers and ref_paperId in self.papers):
                        continue  # 只写入已入库的论文引文
                    await self.summarizer.write_reference(self.papers[paperId], self.papers[ref_paperId])
                    refs_paperId.remove(ref_paperId)  # 删除已入库的论文引文
                    if len(refs_paperId) <= 0:
                        del self.ref_idx[paperId]  # 删除已入库的论文引文
        logger.info("Fetched %d papers from %d papers" % (total_news, total))
        return total_news
