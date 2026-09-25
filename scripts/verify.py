#!/usr/bin/env python3
"""Check generated archive counts, search exports, and local page links."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.ids = set()
        self.h1 = self.main = self.rows = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.h1 += tag == 'h1'
        self.main += tag == 'main' or attrs.get('role') == 'main'
        self.rows += 'post-row' in attrs.get('class', '').split()
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if key in attrs:
                self.links.append(attrs[key])


posts = json.loads((ROOT / 'archive.json').read_text())
files = {path: Page(path.read_text()) for path in ROOT.glob('*.html')}
errors = []
for name in ('index.html', 'search.html'):
    if ROOT / name not in files:
        errors.append(f'Missing {name}; build first')
for path, page in files.items():
    if page.h1 != 1 or page.main != 1:
        errors.append(f'{path.name}: expected one heading and main region')
    for link in page.links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        target = ROOT / unquote(url.path) if url.path else path
        if not target.exists():
            errors.append(f'{path.name}: missing {link}')
        elif url.fragment and target in files and unquote(url.fragment) not in files[target].ids:
            errors.append(f'{path.name}: missing anchor {link}')
if ROOT / 'index.html' in files and files[ROOT / 'index.html'].rows != len(posts):
    errors.append('Archive row count differs from archive.json')
rows = json.loads((ROOT / 'search.json').read_text())
if len(rows) != len(posts):
    errors.append('Search row count differs from archive.json')
for post in posts:
    for suffix in ('.scroll', '.html', '.txt'):
        if not (ROOT / (post['slug'] + suffix)).exists():
            errors.append(f"Missing {post['slug']}{suffix}")
if errors:
    raise SystemExit('\n'.join(errors))
print(f'{len(posts)} articles; {len(files)} pages; no issues.')
