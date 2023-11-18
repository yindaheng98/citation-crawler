import abc
from typing import Optional, Iterable


class Author(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def authorId(self) -> str:
        return ''

    @abc.abstractmethod
    def name(self) -> Optional[str]:
        return None

    @abc.abstractmethod
    def dblp_pid(self) -> Optional[str]:
        return None

    def __dict__(self) -> dict:
        d = {}
        if self.authorId():
            d['authorId'] = self.authorId()
        if self.name():
            d['name'] = self.name()
        if self.dblp_pid():
            d['dblp_pid'] = self.dblp_pid()
        return d


class Paper(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def paperId(self) -> str:
        return ''

    @abc.abstractmethod
    def dblp_id(self) -> Optional[str]:
        return None

    @abc.abstractmethod
    def title(self) -> Optional[str]:
        return None

    @abc.abstractmethod
    def year(self) -> Optional[int]:
        return None

    @abc.abstractmethod
    def doi(self) -> Optional[str]:
        return None

    @abc.abstractmethod
    async def authors(self) -> Iterable[Author]:
        return

    async def __dict__(self) -> dict:
        d = {}
        if self.paperId():
            d['paperId'] = self.paperId()
        if self.dblp_id():
            d['dblp_id'] = self.dblp_id()
        if self.title():
            d['title'] = self.title()
        if self.year():
            d['year'] = self.year()
        if self.doi():
            d['doi'] = self.doi()
        d['authors'] = []
        async for author in self.authors():
            d['authors'].append(author.__dict__())
        return d
