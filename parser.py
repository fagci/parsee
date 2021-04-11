#!/usr/bin/env python3
import sys

from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag


class Result(ResultSet):
    def __init__(self, source, result):
        super().__init__(source, result=result)

    def __truediv__(self, v):
        if v == '@':
            return self.load()
        if isinstance(v, int):
            return super().__getitem__(v)
        raise NotImplementedError

    def __getitem__(self, i):
        return self.__truediv__(i)

    def __floordiv__(self, v):
        if isinstance(v, tuple) or isinstance(v, list):
            return [tuple(self.getprop(vv, r) for vv in v) for r in self]
        return [self.getprop(v, r) for r in self]

    def load(self):
        return (self.source.load(r) for r in self)

    @staticmethod
    def getprop(prop, item):
        if prop == 'tag':
            return item.name
        if prop == 'text':
            return item.text
        return item.get(prop)


class Parser(BeautifulSoup):
    headers = {'User-Agent': 'Mozilla/5.0'}

    def __init__(self, uri='', markup='', session=None, initiator=None):
        from urllib.parse import ParseResult, urlparse
        from requests import Session
        from requests.adapters import HTTPAdapter
        from requests.exceptions import RequestException

        self.start_uri = uri

        pu: ParseResult = urlparse(uri)

        self.scheme = pu.scheme
        self.host = pu.hostname
        self.start_path = '?'.join((pu.path, pu.query))
        self.base = '%s://%s' % (pu.scheme, pu.netloc)
        self.initiator = initiator

        if session:
            self._session = session
        else:
            self._session = Session()
            self._session.mount(self.base, HTTPAdapter(max_retries=3))

        if uri:
            try:
                # print('GET', uri)
                r = self._session.get(uri, timeout=10, headers=self.headers)
                if r.status_code >= 400:
                    sys.stderr.write('err: %s %s\n' % (r.status_code, uri))
                super().__init__(r.text, 'lxml')
            except RequestException:
                super().__init__('', 'lxml')
        elif markup:
            super().__init__(markup, 'lxml')

    def load(self, uri):
        initiator = self
        if isinstance(uri, Tag) and uri.name == 'a':
            initiator = uri
            uri = uri.get('href')
        if uri.startswith('//'):
            uri = '%s:%s' % (self.scheme, uri)
        elif uri.startswith('/'):
            uri = '%s%s' % (self.base, uri)
        elif not uri.startswith(('http://', 'https://')):
            # maybe wrong solution for paths: level1/level2.html
            uri = '%s/%s' % (self.base, uri)
        return Parser(uri, session=self._session, initiator=initiator)

    def __truediv__(self, v):
        if isinstance(v, int):
            return super().__getitem__(v)

        # parser / 'a@' -> load every link
        if '@' in v:
            selector, _, rest = v.partition('@')
            result = Result(self, self.select(selector)).load()
            if rest:
                return (r / rest for r in result)
            return result

        return Result(self, self.select(v))

    def __repr__(self):
        return str(self.result)

    def __getitem__(self, i):
        return self.__truediv__(i)


def _main(start_uri, selector):
    for t in Parser(start_uri) / selector:
        print(str(t))


if __name__ == '__main__':
    from fire import Fire
    Fire(_main)
