import asyncio
from citation_crawler.crawlers import SemanticScholarCrawler
from citation_crawler.summarizers import Neo4jSummarizer


class DefaultSemanticScholarCrawler(SemanticScholarCrawler):
    def __init__(self, keywords, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.keywords = keywords

    async def filter_papers(self, papers):
        """在收集信息时过滤`Paper`，不会对被此方法过滤掉的`Paper`进行信息收集"""
        async for paper in papers:
            if not self.keywords or self.keywords.match_words(paper.title()):
                yield paper


class DefaultNeo4jSummarizer(Neo4jSummarizer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def filter_papers(self, papers):
        """在输出时过滤`Paper`，被过滤掉的`Paper`将不会出现在输出中"""
        async for paper in papers:
            yield paper


async def main():
    paperId = '63b5a719fa2687aa43531efc2ee784b5516c6864'
    crawler = DefaultSemanticScholarCrawler(None, [paperId])
    print(await crawler.bfs_once())
    print(await crawler.bfs_once())
    for paper in crawler.papers.values():
        async for author in paper.authors():
            print(author.__dict__())
    from neo4j import GraphDatabase
    with GraphDatabase.driver('neo4j://10.128.201.131:7687') as driver:
        with driver.session() as session:
            summarizer = DefaultNeo4jSummarizer(session)
            await summarizer(crawler)

# asyncio.run(main()) # Wrong!
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
