#!/usr/bin/env python3
"""Development version of parser config processor"""

from yaml import load, Loader
from fire import Fire
from parser import Parser


def process(cfg):
    ctx = {}
    ctx['start'] = Parser(cfg.get('start'))

    for k, v in cfg.items():
        if isinstance(v, dict):
            src = v.get('in')
            if src:
                select = v.get('select')
                print(k, '=', src, select)
                ctx[k] = ctx.get(src) / select
                print(k, '=', ctx.get(k))


def main(file):
    with open(file) as f:
        process(load(f, Loader=Loader))


if __name__ == '__main__':
    Fire(main)
