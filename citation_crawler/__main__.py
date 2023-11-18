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


async def filter_papers_at_crawler(papers, year, keywords):
    async for paper in papers:
        if (paper.year() is None or paper.year() >= year) and keywords.match_words(paper.title()):
            yield paper


async def filter_papers_at_output(papers, year, keywords):
    async for paper in papers:
        if (paper.year() is None or paper.year() >= year) and keywords.match(paper.title()):
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
        async for paper in filter_papers_at_crawler(papers, self.year, self.keywords):
            yield paper


# --------- for NetworkxGraph ---------

class DefaultNetworkxSummarizer(NetworkxSummarizer):
    def __init__(self, year, keywords, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.year = year
        self.keywords = keywords

    async def filter_papers(self, papers):
        """在输出时过滤`Paper`，被过滤掉的`Paper`将不会出现在输出中"""
        async for paper in filter_papers_at_output(papers, self.year, self.keywords):
            yield paper


parser_nx = subparsers.add_parser('networkx', help='Write results to a json file.')
parser_nx.add_argument("--dest", type=str, required=True, help=f'Path to write results.')


def func_parser_nx(parser):
    year, keywords, pid_list = func_parser(parser)
    args = parser.parse_args()
    dest = args.dest
    logger.info(f"Specified dest: {dest}")
    crawler = DefaultSemanticScholarCrawler(year, keywords, pid_list)
    asyncio.get_event_loop().run_until_complete(bfs_to_end(crawler))
    summarizer = DefaultNetworkxSummarizer(year, keywords)
    asyncio.get_event_loop().run_until_complete(summarizer(crawler))
    asyncio.get_event_loop().run_until_complete(summarizer.save(dest))


parser_nx.set_defaults(func=func_parser_nx)


# --------- for Neo4jGraph ---------


class DefaultNeo4jSummarizer(Neo4jSummarizer):
    def __init__(self, year, keywords, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.year = year
        self.keywords = keywords

    async def filter_papers(self, papers):
        """在输出时过滤`Paper`，被过滤掉的`Paper`将不会出现在输出中"""
        async for paper in filter_papers_at_output(papers, self.year, self.keywords):
            yield paper


# --------- Run ---------
args = parser.parse_args()
args.func(parser)
