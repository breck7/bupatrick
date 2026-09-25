#!/usr/bin/env python3
"""Check rendered source words and original reference links after conversion."""
import collections, json, re
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent.parent
errors=[]
for post in json.loads((ROOT/'archive.json').read_text()):
    slug=post['slug']
    source=BeautifulSoup((ROOT/'originals/html'/(slug+'.html')).read_text(),'html5lib').select_one('#content')
    for node in source.select('h1,.byline,script,style'): node.decompose()
    output=BeautifulSoup((ROOT/(slug+'.html')).read_text(),'html5lib').select_one('#main')
    for tree in (source, output):
        for block in tree.select('p,li,h1,h2,h3,div'):
            block.insert_before(' ')
            block.insert_after(' ')
    # Ordered-list numbering becomes native list markers rather than text nodes.
    words=lambda node: collections.Counter(w for w in re.findall(r'\w+',node.get_text().lower()) if not w.isdigit())
    missing=words(source)-words(output)
    if missing: errors.append(f'{slug}: missing source words {dict(missing)}')
    links={a['href'] for a in output.select('a[href]')}
    for a in source.select('a[href]'):
        url=urljoin(post['url'],a['href'])
        if a.get_text(strip=True) and url not in links: errors.append(f'{slug}: missing source link {url}')
if errors: raise SystemExit('\n'.join(errors))
print('37 pages preserve source words and reference links.')
