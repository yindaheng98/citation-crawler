import logging
import re
from typing import AsyncIterable
from citation_crawler import Author, Summarizer, Paper

from neo4j import Session

'''Use with dblp-crawler'''

logger = logging.getLogger("graph")


def add_paper(tx, paper: Paper):
    n4jset = "MERGE (p:Publication {title_hash: $title_hash}) "\
        "SET p.title=$title, p.year=$year"
    if paper.doi():
        n4jset += ", p.doi=$doi"
    if paper.dblp_id():
        n4jset += ", p.dblp_key=$dblp_id"
    if paper.paperId():
        n4jset += ", p.paperId=$paperId"
    tx.run(n4jset,
           title_hash=paper.title_hash(),
           title=paper.title(),
           year=paper.year(),
           paperId=paper.paperId(),
           dblp_id=paper.dblp_id(),
           doi=paper.doi())


def add_reference(tx, a: Paper, b: Paper):
    tx.run("MERGE (a:Publication {title_hash: $a}) "
           "MERGE (b:Publication {title_hash: $b}) "
           "MERGE (a)-[:CITE]->(b)",
           a=a.title_hash(), b=b.title_hash())


def match_corrlated_authors(tx, paper: Paper):
    nodes = []
    for record in tx.run("MATCH (a:Person)-[:WRITE]->(p:Publication {title_hash: $title_hash}) return a",
                         title_hash=paper.title_hash()):
        for value in record.values():
            nodes.append(value)
    return nodes


def match_authors_kv(tx, k, v):
    nodes = []
    for record in tx.run("MATCH (a:Person {%s: $value}) RETURN a" % k,
                         value=v):
        for value in record.values():
            nodes.append(value)
    return nodes


class Neo4jSummarizer(Summarizer):
    def __init__(self, session: Session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    async def write_paper(self, paper) -> None:
        self.session.execute_write(add_paper, paper)

    async def write_reference(self, paper, reference) -> None:
        self.session.execute_write(add_reference, paper, reference)

    async def get_corrlated_authors(self, paper: Paper) -> AsyncIterable[Author]:
        authors = set()
        for author in self.session.execute_read(match_corrlated_authors, paper):
            if author["id"] not in authors:
                yield author
                authors.add(author["id"])
        async for k, v in paper.authors_kv():
            for author in self.session.execute_read(match_authors_kv, k, v):
                if author["id"] not in authors:
                    yield author
                    authors.add(author["id"])
