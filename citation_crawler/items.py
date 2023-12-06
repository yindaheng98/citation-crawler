import abc
import re
from typing import Optional, Iterable, Tuple


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
    def title(self) -> str:
        return None

    def title_hash(self) -> str:
        return re.sub(r"[^0-9a-z]", "", self.title().lower())

    @abc.abstractmethod
    def year(self) -> Optional[int]:
        return None

    @abc.abstractmethod
    def date(self) -> Optional[str]:
        return None

    @abc.abstractmethod
    def doi(self) -> Optional[str]:
        return None

    @abc.abstractmethod
    async def authors(self) -> Iterable[Author]:
        return

    @abc.abstractmethod
    async def authors_kv(self) -> Iterable[Tuple[str, str]]:
        """key and correlated value to match authors"""
        return

    async def __dict__(self) -> dict:
        d = {}
        if self.paperId():
            d['paperId'] = self.paperId()
        if self.dblp_id():
            d['dblp_key'] = self.dblp_id()
        if self.title():
            d['title'] = self.title()
        if self.title_hash():
            d['title_hash'] = self.title_hash()
        if self.year():
            d['year'] = self.year()
        if self.date():
            d['date'] = self.date()
        if self.doi():
            d['doi'] = self.doi()
        d['authors'] = []
        async for author in self.authors():
            d['authors'].append(author.__dict__())
        return d
