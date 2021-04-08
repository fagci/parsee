#!/usr/bin/env python3

from bs4 import BeautifulSoup
from bs4.element import ResultSet


class Result(ResultSet):
    def __init__(self, source, result):
        super().__init__(source, result=result)

    def __truediv__(self, v):
        if isinstance(v, int):
            return self[v]
        raise NotImplementedError

    def __floordiv__(self, v):
        if v == 'text':
            return [e.text for e in self]
        return [e.get(v) for e in self]


class Parser(BeautifulSoup):
    headers = {'User-Agent': 'Mozilla/5.0'}

    def __init__(self, uri='', markup=''):
        from urllib.parse import ParseResult, urlparse
        from requests import Session
        from requests.adapters import HTTPAdapter
        from requests.exceptions import RequestException

        self.start_uri = uri

        pu: ParseResult = urlparse(uri)

        self.host = pu.hostname
        self.start_path = '?'.join((pu.path, pu.query))
        self.base = '%s://%s' % (pu.scheme, pu.netloc)

        self._session = Session()
        self._session.mount(self.base, HTTPAdapter(max_retries=3))

        if uri:
            try:
                r = self._session.get(uri, timeout=10, headers=self.headers)
                super().__init__(r.text, 'lxml')
            except RequestException:
                super().__init__('', 'lxml')
        elif markup:
            super().__init__(markup, 'lxml')

    def __truediv__(self, v):
        if isinstance(v, int):
            return self[v]

        return Result(self, self.select(v))

    def __repr__(self):
        return str(self.result)

    def __getitem__(self, i):
        if isinstance(i, str):
            return Result(self, self.select(i))
        return self[i]


if __name__ == '__main__':
    m = """
    <ul class="c1">
    <li>Item 1</li>
    <li>Item 2</li>
    <li>Item 3</li>
    </ul>
    """
    p = Parser(markup=m)
    p1 = p['li'] // 'text'

    print(p1)
