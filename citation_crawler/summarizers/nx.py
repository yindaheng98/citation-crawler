import logging
import json
from citation_crawler import Summarizer


import networkx as nx

'''Use with dblp-crawler'''

logger = logging.getLogger("graph")


class NetworkxSummarizer(Summarizer):
    def __init__(self: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.graph: nx.Graph = nx.Graph()

    async def write_paper(self, paper) -> None:
        self.graph.add_node(paper.paperId(), paper=paper)

    async def write_reference(self, paper, reference) -> None:
        self.graph.add_node(paper.paperId(), paper=paper)
        self.graph.add_node(reference.paperId(), paper=reference)
        self.graph.add_edge(paper.paperId(), reference.paperId())

    async def save(self, jsonpath) -> None:
        nodes = {}
        for k, d in self.graph.nodes(data=True):
            if k not in nodes:
                nodes[k] = await d["paper"].__dict__()
            else:
                nodes[k] = {**nodes[k], **await d["paper"].__dict__()}
        edges = [(u, v) for u, v in self.graph.edges()]
        with open(jsonpath, 'w', encoding="utf8") as f:
            json.dump(dict(nodes=nodes, edges=edges), f, indent=2)
