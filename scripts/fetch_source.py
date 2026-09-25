#!/usr/bin/env python3
"""Fetch Patrick's public site into originals/html. Requires beautifulsoup4, html5lib."""
import json, re, subprocess
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / 'originals' / 'html'
DEST.mkdir(exist_ok=True)
queue = ['https://patrickcollison.com/']
seen = set()
pages = []
while queue:
    url = queue.pop(0)
    if url in seen: continue
    seen.add(url)
    result = subprocess.run(['curl', '-fLsS', '--max-time', '30', url], capture_output=True)
    if result.returncode:
        print('Skipped', url, result.stderr.decode().strip(), flush=True)
        continue
    soup = BeautifulSoup(result.stdout, 'html5lib')
    content = soup.select_one('#content')
    if content is None: continue
    slug = urlsplit(url).path.strip('/').replace('/', '-') or 'home'
    (DEST / (slug + '.html')).write_bytes(result.stdout)
    pages.append(dict(slug=slug, url=url))
    print(slug, flush=True)
    for a in soup.select('#menu a[href], #content a[href]'):
        target = urlsplit(urljoin(url, a['href']))
        if target.hostname != 'patrickcollison.com' or target.query: continue
        if not re.fullmatch(r'/[a-zA-Z0-9/_-]*', target.path): continue
        link = 'https://patrickcollison.com' + target.path.rstrip('/')
        if link == 'https://patrickcollison.com': link += '/'
        if link not in seen and link not in queue: queue.append(link)
(ROOT / 'originals' / 'pages.json').write_text(json.dumps(pages, indent=2) + '\n')
