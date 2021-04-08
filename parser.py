#!/usr/bin/env python3
import sys

from bs4 import BeautifulSoup
from bs4.element import ResultSet


class Result(ResultSet):
    def __init__(self, source, result):
        super().__init__(source, result=result)

    def __truediv__(self, v):
        if v == '@':
            return self.load()
        if isinstance(v, int):
            # TODO: make possible // for tag
            return super().__getitem__(v)
        raise NotImplementedError

    def __getitem__(self, i):
        return self.__truediv__(i)

    def __floordiv__(self, v):
        if isinstance(v, tuple) or isinstance(v, list):
            return [tuple(self.getprop(vv, r) for vv in v) for r in self]
        return [self.getprop(v, r) for r in self]

    def load(self):
        return (self.source.load(r.get('href')) for r in self)

    @staticmethod
    def getprop(prop, item):
        if prop == 'tag':
            return item.name
        if prop == 'text':
            return item.text
        return item.get(prop)


class Parser(BeautifulSoup):
    headers = {'User-Agent': 'Mozilla/5.0'}

    def __init__(self, uri='', markup='', session=None):
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

        if session:
            self._session = session
        else:
            self._session = Session()
            self._session.mount(self.base, HTTPAdapter(max_retries=3))

        if uri:
            try:
                r = self._session.get(uri, timeout=10, headers=self.headers)
                if r.status_code >= 400:
                    sys.stderr.write('err: %s %s\n' % (r.status_code, uri))
                super().__init__(r.text, 'lxml')
            except RequestException:
                super().__init__('', 'lxml')
        elif markup:
            super().__init__(markup, 'lxml')

    def load(self, uri):
        if uri.startswith('//'):
            uri = '%s:%s' % (self.scheme, uri)
        elif uri.startswith('/'):
            uri = '%s%s' % (self.base, uri)
        return Parser(uri, session=self._session)

    def __truediv__(self, v):
        if isinstance(v, int):
            return super().__getitem__(v)

        # parser / 'a@' -> load every link
        if v.endswith('@'):
            return Result(self, self.select(v[:-1])).load()

        return Result(self, self.select(v))

    def __repr__(self):
        return str(self.result)

    def __getitem__(self, i):
        return self.__truediv__(i)


if __name__ == '__main__':
    m = """
    <ul class="c1">
        <li class="sup">Item 1</li>
        <li>Item 2</li>
        <li class="sup">Item 3</li>
    </ul>
    <ul class="c2">
        <li class="sup"><a href="http://times.org">Times</a></li>
        <li>Item 2</li>
        <li class="sup">Item 3</li>
    </ul>
    """

    page = Parser(markup=m)

    for page in page['.c2 a@']:
        title = (page / 'title' / 0).text
        links = page / 'a'

        print(title)

        for text in links // 'text':
            print(text.strip())

        for src, ds, alt in page / 'img' // ('src', 'data-src', 'alt'):
            print(alt, ':', src or ds)

    # for href, text in page['.c2 a'] // ('href', 'text'):
    #     print(href, text)

    #     page = Parser(href)
    #     title = (page / 'title' / 0).text
    #     links = page / 'a'

    #     print(title)

    #     for text in links // 'text':
    #         print(text.strip())

    #     for src, ds, alt in page / 'img' // ('src', 'data-src', 'alt'):
    #         print(alt, ':', src or ds)
