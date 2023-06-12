import asyncio
from citation_crawler.crawlers import search_by_title, get_authors as test


async def main():
    paperId = await search_by_title("Understanding  the unstable convergence of gradient descent")
    print(paperId)
    data = await test(paperId)
    print(data)

asyncio.run(main())
