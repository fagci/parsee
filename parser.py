#!/usr/bin/env python3
import logging
import sys

from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag

logging.basicConfig()
logger = logging.getLogger('parsee')


class Result(ResultSet):
    def __init__(self, source, result):
        super().__init__(source, result=result)

    def load(self):
        return Result(self, (self.source.load(r) for r in self))

    def _select(self, selector):
        if isinstance(selector, int) or isinstance(selector, slice):
            return super().__getitem__(selector)
        if selector == '@':
            return self.load()
        return Result(self, (r.select(selector) for r in self))

    def __truediv__(self, selector):
        return self._select(selector)

    def __getitem__(self, selector):
        return self._select(selector)


class Parser(BeautifulSoup):
    headers = {'User-Agent': 'Mozilla/5.0'}

    def __init__(self, uri='', markup='', session=None, initiator=None, debug=False):
        from urllib.parse import ParseResult, urlparse
        from requests import Session
        from requests.exceptions import RequestException

        self.start_uri = uri
        self.debug = debug
        logger.setLevel(logging.DEBUG if debug else logging.ERROR)

        pu: ParseResult = urlparse(uri)

        self.scheme = pu.scheme
        self.host = pu.hostname
        self.start_path = '?'.join((pu.path, pu.query))
        self.base = '%s://%s' % (pu.scheme, pu.netloc)
        self.initiator = initiator

        self._session = session or Session()

        if uri:
            try:
                logger.debug('GET %s', uri)
                r = self._session.get(uri, timeout=10, headers=self.headers)
                if r.status_code >= 400:
                    sys.stderr.write('err: %s %s\n' % (r.status_code, uri))
                markup = r.text
            except RequestException as e:
                sys.stderr.write('err: %s %s\n' % (e, uri))
                markup = ''

        super().__init__(markup, 'lxml')

    def load(self, uri):
        initiator = self
        if isinstance(uri, Tag) and uri.name == 'a':
            initiator = uri
            uri = uri.get('href')

        # normalize uri
        if uri.startswith('//'):
            uri = '%s:%s' % (self.scheme, uri)
        elif uri.startswith('/'):
            uri = '%s%s' % (self.base, uri)
        elif not uri.startswith(('http://', 'https://')):
            # maybe wrong solution for paths: level1/level2.html
            uri = '%s/%s' % (self.base, uri)

        return Parser(uri, session=self._session, initiator=initiator, debug=self.debug)

    def _select(self, selector):
        logger.debug('Initial Select: %s', selector)

        rest = None
        output_format = None

        # @ -> load every link
        # % -> output format

        if '%' in selector:
            selector, _, output_format = selector.rpartition('%')

        need_load = '@' in selector

        if need_load:
            selector, _, rest = selector.partition('@')

        logger.debug('Select: %s', selector)
        results = self.select(selector)

        if need_load:
            results = Result(self, results).load()

            # @ in selector, need to process rest selectors on result
            if rest:
                logger.debug('Each page select: %s', rest)
                results = (r for p in results for r in p._select(rest))

        return self.output(Result(self, results), output_format)

    def output(self, result: Result, fmt):
        if not fmt:
            return result

        import re
        fmt = re.sub(r'(\W|^)\.', '\\1item.', fmt)

        return (eval(fmt, {'item': r, 'result': result}) for r in result)

    def __repr__(self):
        return str(self.result)

    def __truediv__(self, selector):
        return self._select(selector)

    def __getitem__(self, selector):
        return self._select(selector)


def _main(start_uri, selector, d=False):
    for t in Parser(start_uri, debug=d) / selector:
        print(t)


if __name__ == '__main__':
    from fire import Fire
    Fire(_main)
