import logging
from citation_crawler import Summarizer


import networkx as nx

'''Use with dblp-crawler'''

logger = logging.getLogger("graph")


class NetworkxSummarizer(Summarizer):
    def __init__(self, jsonpath: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = jsonpath
        self.graph: nx.MultiGraph = nx.MultiGraph()

    async def write_paper(self, paper) -> None:
        self.graph.add_node(paper.paperId(), paper=paper)

    async def write_reference(self, paper, reference) -> None:
        self.graph.add_node(paper.paperId(), paper=paper)
        self.graph.add_node(reference.paperId(), paper=reference)
        self.graph.add_edge(paper.paperId(), reference.paperId())

    async def post_written(self) -> None:
        print(self.graph)  # TODO: 写入self.path
