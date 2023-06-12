from .common import *

async def search_by_title(title: str) -> dict:
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?limit=1&query={title.lower()}"
    return await fetch_item(url)
