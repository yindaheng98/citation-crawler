import abc
from typing import Optional


class Author(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def name(self) -> Optional[str]:
        return None

    @abc.abstractmethod
    def dblp_pid(self) -> Optional[str]:
        return None


class Paper(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def dblp_key(self) -> Optional[str]:
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

    def __dict__(self) -> dict:
        d = {}
        if self.dblp_key():
            d['dblp_key'] = self.dblp_key()
        if self.title():
            d['title'] = self.title()
        if self.year():
            d['year'] = self.year()
        if self.doi():
            d['year'] = self.doi()
        return d
