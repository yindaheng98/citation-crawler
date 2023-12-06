from neo4j import GraphDatabase


def match_papers(tx):
    papers = []
    for record in tx.run("MATCH (p:Publication) RETURN p.paperId"):
        for value in record.values():
            if value is not None:
                papers.append(value)
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
