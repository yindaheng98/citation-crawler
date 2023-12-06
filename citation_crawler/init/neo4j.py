from neo4j import GraphDatabase
from urllib.parse import urlparse
import re


def match_papers(tx):
    papers = []
    for record in tx.run("MATCH (p:Publication) RETURN p.paperId, p.doi"):
        paperId, doi = record.values()
        if paperId is not None:
            papers.append(paperId)
        elif doi is not None:
            u = urlparse(doi)
            papers.append("DOI:" + re.sub(r"^/+", "", u.path))
    return papers


def papers_in_neo4j(uri, auth=None):
    with GraphDatabase.driver(uri, auth=auth) as driver:
        with driver.session() as session:
            return session.execute_read(match_papers)


def match_authors(tx):
    authors = []
    for record in tx.run("MATCH (p:Person) RETURN p.authorId"):
        for value in record.values():
            if value is not None:
                authors.append(value)
    return authors


def authors_in_neo4j(uri, auth=None):
    with GraphDatabase.driver(uri, auth=auth) as driver:
        with driver.session() as session:
            return session.execute_read(match_authors)
