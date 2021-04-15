#!/usr/bin/env python3
"""Sweet sites parser"""
import logging
from typing import Iterable

from bs4 import BeautifulSoup
from bs4.element import Tag

logging.basicConfig()
logger = logging.getLogger('parsee')


class Result:
    __slots__ = ('source', 'result', 'initiator')

    def __init__(self, source, result, initiator=None):
        self.source = source
        self.result = result
        self.initiator = initiator

    def _select(self, selector):
        if isinstance(selector, str):
            result = (rr for r in self for rr in r._select(selector))
            return Result(self.source, result, selector)
        return list(self.result).__getitem__(selector)

    def __iter__(self):
        return iter(self.result)

    def __truediv__(self, selector):
        return self._select(selector)

    def __getitem__(self, selector):
        return self._select(selector)


class Parser(BeautifulSoup):
    __slots__ = ('debug', 'start_uri', 'scheme',
                 'start_path', 'base', 'host', '_session', 'elapsed')
    uris = set()

    def __init__(self, uri='', markup='', session=None, headers={'User-Agent': 'Mozilla/5.0'}, debug=False):
        logger.setLevel(logging.DEBUG if debug else logging.ERROR)

        self.debug = debug

        if not uri or uri in self.uris:
            super().__init__(markup, 'lxml')
            return

        self.uris.add(uri)

        from urllib.parse import ParseResult, urlparse
        from requests import Session
        from requests.exceptions import RequestException

        pu: ParseResult = urlparse(uri)

        self.start_uri = uri
        self.scheme = pu.scheme
        self.host = pu.hostname
        self.start_path = '?'.join((pu.path, pu.query))
        self.base = '%s://%s' % (pu.scheme, pu.netloc)
        self._session = session or Session()

        try:
            logger.debug('GET %s', uri)
            r = self._session.get(uri, timeout=10, headers=headers)
            if r.status_code >= 400:
                logger.error('%s %s\n', r.status_code, uri)
            markup = r.text
            self.elapsed = r.elapsed.total_seconds()
        except RequestException as e:
            logger.error('%s %s\n', type(e), uri)

        super().__init__(markup, 'lxml')

    def load(self, uri):
        if isinstance(uri, Tag) and uri.name == 'a':
            uri = uri.get('href')

        elif isinstance(uri, Iterable) and not isinstance(uri, str):
            logger.debug('Load iterable: %s', uri)
            return (self.load(r) for r in uri)

        # normalize uri
        if uri.startswith('//'):
            uri = '%s:%s' % (self.scheme, uri)
        elif uri.startswith('/'):
            uri = '%s%s' % (self.base, uri)
        elif not uri.startswith(('http://', 'https://')):
            # maybe wrong solution for paths: level1/level2.html
            uri = '%s/%s' % (self.base, uri)

        return Parser(uri, session=self._session, debug=self.debug)

    def _select(self, selector):
        selector, _, output_format = selector.partition('%')
        selector, has_load_link, next_page_selector = selector.partition('@')

        logger.debug('Select: %s', selector)
        results = self.select(selector)

        if has_load_link:
            results = self.load(results)

            if next_page_selector:
                logger.debug('Each page select: %s', next_page_selector)
                results = (r for p in results for r in p._select(
                    next_page_selector))

        return self.output(Result(self, results), output_format)

    def output(self, result: Result, fmt):
        if not fmt:
            return result

        import re
        fmt = re.sub(r'(^|[^")\]])\.', r'\1item.', fmt)
        logger.debug('Format: %s', fmt)

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
    try:
        Fire(_main)
    except KeyboardInterrupt:
        print('Interrupted by user.')
        exit(130)
