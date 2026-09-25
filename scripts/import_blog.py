#!/usr/bin/env python3
"""Build post sources from archive.json metadata and originals/<slug>.scroll bodies.

Convert the source site's articles to native Scroll bodies first. This deliberately
uses no person-specific scraper or HTML selector.
"""
import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
posts = json.loads((ROOT / 'archive.json').read_text())
reserved = {p.stem for p in ROOT.glob('*.scroll') if p.name in (
    'bu.scroll', 'head.scroll', 'readme.scroll', 'search.scroll', 'site.scroll',
    'style.scroll', 'footer.scroll', 'homeFooter.scroll', 'post-header.scroll')}
reserved.update(('index', 'blog', 'favicon'))
outputs = {}
for post in posts:
    slug = post['slug']
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug) or slug in reserved or slug in outputs:
        raise ValueError(f'Invalid, reserved, or duplicate slug: {slug}')
    for key in ('title', 'date', 'url'):
        if not isinstance(post[key], str) or not post[key].strip() or '\n' in post[key] or '\r' in post[key]:
            raise ValueError(f'{slug}: {key} must be a nonempty single line')
    date.fromisoformat(post['date'])
    if urlparse(post['url']).scheme not in ('http', 'https') or not urlparse(post['url']).netloc:
        raise ValueError(f'{slug}: invalid original URL')
    body = (ROOT / 'originals' / (slug + '.scroll')).read_text().strip()
    if not body:
        raise ValueError(f'{slug}: empty body')
    title = html.escape(post['title'], quote=True)
    url = html.escape(post['url'], quote=True)
    label = "// publicationLabel Date not stated\n" if post.get("undated") else ""
    outputs[slug] = label + f"title {title}\ndate {post['date']}\ncanonicalUrl {url}\n\npost-header.scroll\n\n{body}\n\nfooter.scroll\n"
# Validate all inputs before writing any posts. Existing unrelated files are untouched.
for slug, text in outputs.items():
    (ROOT / (slug + '.scroll')).write_text(text)
print(f'Imported {len(outputs)} articles.')
