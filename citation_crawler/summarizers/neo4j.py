import logging
import re
from citation_crawler import Summarizer, Paper

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


class Neo4jSummarizer(Summarizer):
    def __init__(self, session: Session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    async def write_paper(self, paper) -> None:
        self.session.execute_write(add_paper, paper)

    async def write_reference(self, paper, reference) -> None:
        self.session.execute_write(add_reference, paper, reference)
