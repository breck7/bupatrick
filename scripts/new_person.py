#!/usr/bin/env python3
"""Copy this empty template into a new sibling folder and configure its identity."""
import argparse
import json
import re
import shutil
from pathlib import Path
from configure import configure

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('folder', help='New sibling folder name, e.g. bubill')
parser.add_argument('author', help='Full author name')
parser.add_argument('url', help='Original website URL')
parser.add_argument('--base-url', default='', help='Optional published archive URL')
args = parser.parse_args()
if not re.fullmatch(r'[a-z][a-z0-9-]*', args.folder):
    parser.error('Use a lowercase folder name containing letters, digits, or hyphens.')
source = Path(__file__).resolve().parent.parent
destination = source.parent / args.folder
if destination.exists():
    parser.error(f'{destination} already exists; nothing was changed.')
if json.loads((source / 'archive.json').read_text()) or any(source.glob('*.txt')):
    parser.error('Run this command from the empty bunew template, not a populated archive.')
shutil.copytree(source, destination, ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__', '.DS_Store', '.venv'))
try:
    (destination / 'site.json').write_text(json.dumps(dict(name=args.folder, author=args.author, originalUrl=args.url, baseUrl=args.base_url), indent=2) + '\n')
    configure(destination)
    package = json.loads((destination / 'package.json').read_text())
    package.update(name=args.folder, description=f'{args.author} writing archive.')
    (destination / 'package.json').write_text(json.dumps(package, indent=2) + '\n')
    # Generated pages must be rebuilt with the new identity.
    for pattern in ('*.html', 'search.json', 'search.csv'):
        for path in destination.glob(pattern):
            path.unlink()
except Exception:
    shutil.rmtree(destination)
    raise
print(f'Created {destination}\nNext: port content, then run npm install && npm run build in that folder.')
