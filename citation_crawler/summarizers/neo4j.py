import logging
from typing import AsyncIterable
from citation_crawler import Summarizer, Paper

import dateutil.parser
from neo4j import Session
import neo4j.time

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
    tx.run(n4jset,
           title_hash=paper.title_hash(),
           title=paper.title(),
           year=paper.year(),
           paperId=paper.paperId(),
           dblp_id=paper.dblp_id(),
           doi=paper.doi(),
           date=date)


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
            nodes.append({**dict(value), "element_id": value.element_id})
    return nodes


def match_authors_kv(tx, k, v):
    nodes = []
    for record in tx.run("MATCH (a:Person {%s: $value}) RETURN a" % k,
                         value=v):
        for value in record.values():
            nodes.append({**dict(value), "element_id": value.element_id})
    return nodes


def link_author(tx, paper: Paper, author_kv, write_fields):
    tx.run("MERGE (p:Publication {title_hash: $title_hash}) " +
           ('MERGE (a:Person {%s}) ' % (",".join([f'{k}: ${k}' for k in author_kv]))) +
           (f'SET {",".join([f"a.{k}=${k}" for k in write_fields])}' if len(write_fields) > 0 else "") +
           " MERGE (a)-[:WRITE]->(p)",
           title_hash=paper.title_hash(), **author_kv, **write_fields)


def divide_author(tx, paper: Paper, author_kv, write_fields, division_kv):
    author_c = tx.run("MATCH (c:Person {%s}) RETURN c" % (",".join([f'{k}: ${k}' for k in division_kv])),
                      **division_kv).values()[0][0]._properties
    tx.run("MATCH (c:Person {%s})-[r:WRITE]->(p:Publication {title_hash: $title_hash}) "
           "DELETE r" % (",".join([f'{k}: ${k}' for k in division_kv])),
           title_hash=paper.title_hash(), **division_kv)
    write_fields = {**author_c, **write_fields, **author_kv}
    tx.run("MERGE (p:Publication {title_hash: $title_hash}) " +
           ('MERGE (a:Person {%s}) ' % (",".join([f'{k}: ${k}' for k in author_kv]))) +
           (f'SET {",".join([f"a.{k}=${k}" for k in write_fields])}' if len(write_fields) > 0 else "") +
           " MERGE (a)-[:WRITE]->(p)",
           title_hash=paper.title_hash(), **write_fields)


class Neo4jSummarizer(Summarizer):
    def __init__(self, session: Session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    async def write_paper(self, paper) -> None:
        self.session.execute_write(add_paper, paper)

    async def write_reference(self, paper, reference) -> None:
        self.session.execute_write(add_reference, paper, reference)

    async def get_corrlated_authors(self, paper: Paper) -> AsyncIterable[dict]:
        authors = set()
        for author in self.session.execute_read(match_corrlated_authors, paper):
            if author["element_id"] not in authors:
                yield author
                authors.add(author["element_id"])
        async for k, v in paper.authors_kv():
            for author in self.session.execute_read(match_authors_kv, k, v):
                if author["element_id"] not in authors:
                    yield author
                    authors.add(author["element_id"])

    async def write_author(self, paper: Paper, author_kv, write_fields, division_kv) -> None:
        if division_kv:
            self.session.execute_write(divide_author, paper, author_kv, write_fields, division_kv)
        self.session.execute_write(link_author, paper, author_kv, write_fields)
