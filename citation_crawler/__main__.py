import asyncio
from citation_crawler.crawlers import search_by_title

async def main():
    r = await search_by_title("Understanding  the unstable convergence of gradient descent")
    print(r)

asyncio.run(main())