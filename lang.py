#!/usr/bin/env python3
"""Development version of parser config processor"""

from yaml import load, Loader
from fire import Fire
from parser import Parser


def process(cfg, debug):
    ctx = {}
    ctx['start'] = Parser(cfg.get('start'), debug=debug)

    for k, v in cfg.items():
        if isinstance(v, dict):
            src = v.get('in')
            if src:
                select = v.get('select')
                src_data = ctx.get(src)
                ctx[k] = src_data._select(select) if select else src_data
    for result in ctx.get('output'):
        print(result)


def main(file, d=False):
    with open(file) as f:
        process(load(f, Loader=Loader), d)


if __name__ == '__main__':
    Fire(main)
