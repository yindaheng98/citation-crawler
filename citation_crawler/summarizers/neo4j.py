import logging
import re
from citation_crawler import Summarizer, Paper

from neo4j import Session

'''Use with dblp-crawler'''

logger = logging.getLogger("graph")


def add_paper(tx, paper: Paper):
    dblp_id = paper.dblp_id()
    doi = paper.doi()
    if doi:
        if not re.match(r"^https*://doi.org/", doi):
            doi = "https://doi.org/" + doi
    if dblp_id and doi:
        tx.run("MERGE (p:Publication {key: $key}) "
               "ON CREATE SET p.title=$title, p.year=$year, p.doi=$doi",
               key=dblp_id,
               title=paper.title(),
               year=paper.year(),
               doi=doi)
    elif dblp_id:
        tx.run("MERGE (p:Publication {key: $key}) "
               "ON CREATE SET p.title=$title, p.year=$year",
               key=dblp_id,
               title=paper.title(),
               year=paper.year())
    elif doi:
        tx.run("MERGE (p:Publication {doi: $doi}) "
               "ON CREATE SET p.title=$title, p.year=$year",
               doi=doi,
               title=paper.title(),
               year=paper.year())


def match_statement(p: Paper):
    dblp_id = p.dblp_id()
    if dblp_id:
        return "MATCH ({n}:Publication {{key: ${n}}}) ", dblp_id
    doi = p.doi()
    if doi:
        if not re.match(r"^https*://doi.org/", doi):
            doi = "https://doi.org/" + doi
        return "MATCH ({n}:Publication {{doi: ${n}}}) ", doi
    return None, None


def add_reference(tx, a: Paper, b: Paper):
    sta, vla = match_statement(a)
    stb, vlb = match_statement(b)
    if sta is None or stb is None:
        return
    statement = sta.format(n='a') + stb.format(n='b') + "MERGE (a)-[:CITE]->(b)"
    tx.run(statement, a=vla, b=vlb)


class Neo4jSummarizer(Summarizer):
    def __init__(self, session: Session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    async def write_paper(self, paper) -> None:
        self.session.execute_write(add_paper, paper)

    async def write_reference(self, paper, reference) -> None:
        self.session.execute_write(add_reference, paper, reference)
