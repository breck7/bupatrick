#!/usr/bin/env python3
"""Generate site identity and index files from site.json."""
import html
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent


def configure(root=ROOT):
    config = json.loads((root / 'site.json').read_text())
    for key in ('name', 'author', 'originalUrl', 'baseUrl'):
        if not isinstance(config.get(key), str) or '\n' in config[key] or '\r' in config[key]:
            raise ValueError(f'{key} must be a single-line string')
    for key in ('originalUrl', 'baseUrl'):
        value = config[key]
        if value and (urlparse(value).scheme not in ('https', 'http') or not urlparse(value).netloc):
            raise ValueError(f'{key} must be an absolute HTTP(S) URL')
    if not config['name'].strip() or not config['author'].strip() or not config['originalUrl']:
        raise ValueError('name, author, and originalUrl are required')
    name, author, original, base = (html.escape(config[k], quote=True) for k in ('name', 'author', 'originalUrl', 'baseUrl'))
    description = f'boo {author}. made by @breckyunits'
    (root / 'head.scroll').write_text(f'''importOnly
{('baseUrl ' + base) if base else ''}
blog.parsers
bu.scroll
replace BU_SITE_NAME {name}
replace BU_SITE_DESCRIPTION {description}
originalBlogUrl {original}
replace BU_ORIGINAL_LABEL Original blog ↗
replace BU_POST_DATE printDate

BU_HEAD
''')
    readme = root / 'readme.scroll'
    opening_comments = []
    if readme.exists():
        for line in readme.read_text().splitlines(keepends=True):
            if line.startswith('//') or line.startswith(' ') or not line.strip():
                opening_comments.append(line)
            else:
                break
    readme.write_text(''.join(opening_comments) + f'''title {name} — Archive
description {description}
permalink index.html
canonicalUrl {original}
buildHtml
head.scroll

container 1120px
 id main
 role main
 addClass archive

# All posts
 id archive-heading

BU_ARCHIVE
clearStack
homeFooter.scroll
site.js
''')
    (root / 'search.scroll').write_text(f'''title Search — {name}
description Search the full text of {author}'s writing.
permalink search.html
canonicalUrl search.html
buildHtml
buildJson
buildCsv
head.scroll

container 1120px
 tag main
 id main
 addClass search-page

h1 Search all writing
Search the full text of all posts.
posts Posts
 select title titleLink date text
  printTable

tableSearch
clearStack
homeFooter.scroll
''')


if __name__ == '__main__':
    configure()
