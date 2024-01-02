import logging
from typing import AsyncIterable
from citation_crawler import Summarizer, Paper

import dateutil.parser
from neo4j import AsyncSession
import neo4j.time

'''Use with dblp-crawler'''

logger = logging.getLogger("graph")


async def add_paper(tx, paper: Paper):
    n4jset = "MERGE (p:Publication {title_hash: $title_hash}) "\
        "SET p.title=$title, p.year=$year"
    if paper.doi():
        n4jset += ", p.doi=$doi"
    if paper.dblp_id():
        n4jset += ", p.dblp_key=$dblp_id"
    if paper.paperId():
        n4jset += ", p.paperId=$paperId"
    date = None
    if paper.date():
        try:
            _date = dateutil.parser.parse(paper.date())
            date = neo4j.time.Date(
                year=_date.year,
                month=_date.month,
                day=_date.day,
            )
            n4jset += ", p.date=$date"
        except Exception as e:
            logger.error(f"Cannot parse date {paper.date()}: {e}")
    await tx.run(n4jset,
                 title_hash=paper.title_hash(),
                 title=paper.title(),
                 year=paper.year(),
                 paperId=paper.paperId(),
                 dblp_id=paper.dblp_id(),
                 doi=paper.doi(),
                 date=date)


async def add_reference(tx, a: Paper, b: Paper):
    await tx.run("MERGE (a:Publication {title_hash: $a}) "
                 "MERGE (b:Publication {title_hash: $b}) "
                 "MERGE (a)-[:CITE]->(b)",
                 a=a.title_hash(), b=b.title_hash())


async def match_corrlated_authors(tx, paper: Paper):
    nodes = []
    for record in await (await tx.run("MATCH (a:Person)-[:WRITE]->(p:Publication {title_hash: $title_hash}) return a",
                                      title_hash=paper.title_hash())).values():
        nodes.append({**dict(record[0]), "element_id": record[0].element_id})
    return nodes


async def match_authors_kv(tx, k, v):
    nodes = []
    for record in await (await tx.run("MATCH (a:Person {%s: $value}) RETURN a" % k,
                                      value=v)).values():
        nodes.append({**dict(record[0]), "element_id": record[0].element_id})
    return nodes


async def link_author(tx, paper: Paper, author_kv, write_fields):
    await tx.run("MERGE (p:Publication {title_hash: $title_hash}) " +
                 ('MERGE (a:Person {%s}) ' % (",".join([f'{k}: ${k}' for k in author_kv]))) +
                 (f'SET {",".join([f"a.{k}=${k}" for k in write_fields])}' if len(write_fields) > 0 else "") +
                 " MERGE (a)-[:WRITE]->(p)",
                 title_hash=paper.title_hash(), **author_kv, **write_fields)


async def divide_author(tx, paper: Paper, author_kv, write_fields, division_kv):
    author_c = (await (await tx.run("MATCH (c:Person {%s}) RETURN c" % (",".join([f'{k}: ${k}' for k in division_kv])),
                                    **division_kv)).values())[0][0]._properties
    await tx.run("MATCH (c:Person {%s})-[r:WRITE]->(p:Publication {title_hash: $title_hash}) "
                 "DELETE r" % (",".join([f'{k}: ${k}' for k in division_kv])),
                 title_hash=paper.title_hash(), **division_kv)
    write_fields = {**author_c, **write_fields, **author_kv}
    await tx.run("MERGE (p:Publication {title_hash: $title_hash}) " +
                 ('MERGE (a:Person {%s}) ' % (",".join([f'{k}: ${k}' for k in author_kv]))) +
                 (f'SET {",".join([f"a.{k}=${k}" for k in write_fields])}' if len(write_fields) > 0 else "") +
                 " MERGE (a)-[:WRITE]->(p)",
                 title_hash=paper.title_hash(), **write_fields)


async def _add_references(tx, paper: Paper):
    title_hash_exists = set([
        title_hash for (title_hash,) in
        await (await tx.run("MATCH (a:Publication)-[:CITE]->(p:Publication {title_hash: $title_hash}) RETURN a.title_hash",
               title_hash=paper.title_hash())).values()
    ])
    async for ref in paper.get_references():
        if ref.title_hash() in title_hash_exists:
            continue
        await add_paper(tx, ref)
        await add_reference(tx, paper, ref)


async def _add_citations(tx, paper: Paper):
    title_hash_exists = set([
        title_hash for (title_hash,) in
        await (await tx.run("MATCH (p:Publication {title_hash: $title_hash})-[:CITE]->(a:Publication) RETURN a.title_hash",
               title_hash=paper.title_hash())).values()
    ])
    async for cit in paper.get_references():
        if cit.title_hash() in title_hash_exists:
            continue
        await add_paper(tx, cit)
        await add_reference(tx, cit, paper)


class Neo4jSummarizer(Summarizer):
    def __init__(self, session: AsyncSession, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    async def write_paper(self, paper) -> None:
        await self.session.execute_write(add_paper, paper)
        await self.session.execute_write(_add_references, paper)
        await self.session.execute_write(_add_citations, paper)

    async def write_reference(self, paper, reference) -> None:
        await self.session.execute_write(add_reference, paper, reference)

    async def get_corrlated_authors(self, paper: Paper) -> AsyncIterable[dict]:
        authors = set()
        for author in await self.session.execute_read(match_corrlated_authors, paper):
            if author["element_id"] not in authors:
                yield author
                authors.add(author["element_id"])
        async for k, v in paper.authors_kv():
            for author in await self.session.execute_read(match_authors_kv, k, v):
                if author["element_id"] not in authors:
                    yield author
                    authors.add(author["element_id"])

    async def write_author(self, paper: Paper, author_kv, write_fields, division_kv) -> None:
        if division_kv:
            await self.session.execute_write(divide_author, paper, author_kv, write_fields, division_kv)
        await self.session.execute_write(link_author, paper, author_kv, write_fields)
