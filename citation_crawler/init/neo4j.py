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


def match_papers_keywords(tx, year, *arg_keywords):
    pwhere = 'WHERE p.year >= $year'
    values = dict(year=year)

    ki, k_or, v_or = 0, [], {}
    for keywords in arg_keywords:
        k_and, v_and = [], {}
        for k in keywords.split(" "):
            if not k:
                continue
            ki += 1
            k_and.append(f"toLower(p.title) CONTAINS $keyword{ki}")
            v_and[f"keyword{ki}"] = k
        k_or.append(f"({' and '.join(k_and)})")
        v_or = {**v_or, **v_and}
    if ki > 0:
        pwhere += " AND " + f"({' OR '.join(k_or)})"
        values = {**values, **v_or}

    papers = []
    for record in tx.run("MATCH (p:Publication)" + pwhere + " RETURN p.paperId, p.doi", **values):
        paperId, doi = record.values()
        if paperId is not None:
            papers.append(paperId)
        elif doi is not None:
            u = urlparse(doi)
            papers.append("DOI:" + re.sub(r"^/+", "", u.path))
    return papers


def papers_in_neo4j_keywords(uri, auth=None, year=2000, *keywords):
    with GraphDatabase.driver(uri, auth=auth) as driver:
        with driver.session() as session:
            return session.execute_read(match_papers_keywords, year, *keywords)
