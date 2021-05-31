# Parsee

Sweet python tiny site parser.

[new] Now with CloudFlare bypass

## Lang syntax

```config
<selector> [a@ <selector>] [% <python_code>]
```

Note: `python_code` relative to last tag. Use `.` (dot) to get attribute or call method.

## Requirements

Before use, install requirements:

```sh
pip3 install -r requirements.txt
```

## Examples

### Crawl first page links, get paragraph in each page next to heading contains text

```python
for page in parser / '.links a@':
    for p in page / 'h3:-soup-contains("Some title")+p':
        print(p.text)
```

### Get titles of subpages

```sh
./parser.py http://site.org 'a@a@title%.text'
```

### Get links at home page

```sh
./parser.py http://site.org 'a%.get("href")'
```
