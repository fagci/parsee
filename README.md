# Parsee

Sweet python tiny site parser.

## Examples

### Crawl first page links, get paragraph in each page next to heading contains text

```python
for page in parser / '.links a@':
    for p in page / 'h3:-soup-contains("Some title")+p':
        print(p.text)
```
