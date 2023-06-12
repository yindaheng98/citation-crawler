import abc
import asyncio
import logging
from itertools import combinations
from typing import Optional, Iterable


logger = logging.getLogger("graph")


class Crawler(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        pass


class Summarizer(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        pass


class Graph:
    def __init__(self, crawler: Crawler, summarizer: Summarizer) -> None:
        pass
