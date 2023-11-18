import argparse
import asyncio
import logging

from dblp_crawler.keyword.arg import add_argument as add_argument_kw, parse_args as parse_args_kw
from citation_crawler.arg import add_argument_pid, parse_args_pid
from citation_crawler.crawlers import SemanticScholarCrawler
from citation_crawler.summarizers import NetworkxSummarizer, Neo4jSummarizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('citation_crawler')

parser = argparse.ArgumentParser()

parser.add_argument("-y", "--year", type=int, help="Only crawl the paper after the specified year.", default=2000)
add_argument_kw(parser)
add_argument_pid(parser)


def func_parser(parser):
    args = parser.parse_args()
    year = args.year
    keywords = parse_args_kw(parser)
    pid_list = parse_args_pid(parser)
    logger.info(f"Specified keyword rules: {keywords.rules}")
    logger.info(f"Specified paperId list for init: {pid_list}")
    return year, keywords, pid_list


async def filter_papers(papers, year, keywords):
    async for paper in papers:
        if paper.year() >= year and keywords.match(paper.title()):
            yield paper


async def bfs_to_end(graph, limit: int = 0):
    while min(*(await graph.bfs_once())) > 0 and (limit != 0):
        logger.info("Still running......")
        limit -= 1


subparsers = parser.add_subparsers(help='sub-command help')


# --------- for SemanticScholarCrawler ---------

class DefaultSemanticScholarCrawler(SemanticScholarCrawler):
    def __init__(self, year, keywords, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.year = year
        self.keywords = keywords

    async def filter_papers(self, papers):
        """在收集信息时过滤`Paper`，不会对被此方法过滤掉的`Paper`进行信息收集"""
        async for paper in filter_papers(papers, self.year, self.keywords):
            yield paper


# --------- for NetworkxGraph ---------


class DefaultNetworkxSummarizer(NetworkxSummarizer):
    def __init__(self, year, keywords, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.year = year
        self.keywords = keywords

    async def filter_papers(self, papers):
        """在输出时过滤`Paper`，被过滤掉的`Paper`将不会出现在输出中"""
        async for paper in filter_papers(papers, self.year, self.keywords):
            yield paper

# --------- for Neo4jGraph ---------


class DefaultNeo4jSummarizer(Neo4jSummarizer):
    def __init__(self, year, keywords, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.year = year
        self.keywords = keywords

    def filter_papers(self, papers):
        """在输出时过滤`Paper`，被过滤掉的`Paper`将不会出现在输出中"""
        yield from filter_papers(papers, self.year, self.keywords)


async def main():
    from dblp_crawler.keyword import Keywords
    keywords = Keywords()
    keywords.add_rule(".*")
    paperId = '63b5a719fa2687aa43531efc2ee784b5516c6864'
    crawler = DefaultSemanticScholarCrawler(2020, keywords, [paperId])
    print(await crawler.bfs_once())
    print(await crawler.bfs_once())
    for paper in crawler.papers.values():
        async for author in paper.authors():
            print(author.__dict__())
    summarizer = DefaultNetworkxSummarizer(2020, keywords, "summary.json")
    await summarizer(crawler)

# asyncio.run(main()) # Wrong!
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
