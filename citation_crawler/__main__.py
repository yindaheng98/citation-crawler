import asyncio
from citation_crawler.crawlers.ss import search_by_title, get_authors
from citation_crawler.crawlers import SemanticScholarCrawler


class DefaultSemanticScholarCrawler(SemanticScholarCrawler):
    def __init__(self, keywords, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.keywords = keywords

    def filter_papers(self, paperIds):
        """在收集信息时过滤`Paper`，不会对被此方法过滤掉的`Paper`进行信息收集"""
        for paperId in paperIds:
            if not self.keywords or self.keywords.match_words(self.papers[paperId]['title']):
                yield paperId


async def main():
    paperId = await search_by_title("Understanding  the unstable convergence of gradient descent")
    print(paperId)
    async for author in get_authors(paperId):
        print(author.__dict__())
    crawler = DefaultSemanticScholarCrawler(None, [paperId])
    print(await crawler.bfs_once())

asyncio.run(main())
