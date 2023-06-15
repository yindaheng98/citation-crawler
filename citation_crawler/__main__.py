import asyncio
from citation_crawler.crawlers.ss import search_by_title, get_references
from citation_crawler.crawlers import SemanticScholarCrawler


class DefaultSemanticScholarCrawler(SemanticScholarCrawler):
    def __init__(self, keywords, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.keywords = keywords

    async def filter_papers(self, papers):
        """在收集信息时过滤`Paper`，不会对被此方法过滤掉的`Paper`进行信息收集"""
        async for paper in papers:
            if not self.keywords or self.keywords.match_words(paper.title()):
                yield paper


async def main():
    paperId = '247086a46f289035a5c74d758c359890a568f596'
    crawler = DefaultSemanticScholarCrawler(None, [paperId])
    print(await crawler.bfs_once())
    print(await crawler.bfs_once())
    for paper in crawler.papers.values():
        async for author in paper.authors():
            print(author.__dict__())

# asyncio.run(main()) # Wrong!
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()