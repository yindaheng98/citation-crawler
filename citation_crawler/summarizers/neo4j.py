import logging
import re
import os
from typing import Optional
from citation_crawler import Summarizer, Paper

from neo4j import Session

'''Use with dblp-crawler'''

logger = logging.getLogger("graph")


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
    statement = (sta.format(n='a')) + (stb.format(n='b')) + "MERGE (a)-[:CITE]->(b)"
    tx.run(statement, a=vla, b=vlb)


class Neo4jSummarizer(Summarizer):
    def __init__(self, session: Session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    async def write_paper(self, paper) -> None:
        print(paper.__dict__())

    async def write_reference(self, paper, reference) -> None:
        self.session.execute_write(add_reference, paper, reference)
