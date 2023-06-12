import asyncio
from citation_crawler.crawlers.ss import search_by_title
from citation_crawler.crawlers import SemanticScholarCrawler


async def main():
    paperId = await search_by_title("Understanding  the unstable convergence of gradient descent")
    print(paperId)
    crawler = SemanticScholarCrawler([paperId])
    print(await crawler.bfs_once())

asyncio.run(main())
