#!/usr/bin/env python3
"""Convert saved HTML to native Scroll. Requires beautifulsoup4 and html5lib.
Undated entries use 1900-01-01 only as an internal sort key; displays hide it.
"""
import html, json, re
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup, NavigableString, Comment
ROOT = Path(__file__).resolve().parent.parent

def clean(text): return re.sub(r'\s+', ' ', text).strip()
def esc(text): return html.escape(text, quote=False)

def inline(node, url, prefix=''):
    text = clean(node.get_text())
    if not text: return []
    lines = [prefix + esc(text), ' linkify false']
    if node.get('id'): lines.append(' id ' + node['id'])
    for tag in node.find_all(['a', 'b', 'strong', 'i', 'em']):
        label = clean(tag.get_text())
        if not label: continue
        if tag.name == 'a' and tag.get('href'):
            lines.append(' link ' + html.escape(urljoin(url, tag['href']), quote=True) + ' ' + esc(label))
        elif tag.name in ('b', 'strong', 'i', 'em') and not tag.find('a') and not tag.find_parent('a'):
            lines.append(' ' + ('bold' if tag.name in ('b','strong') else 'italics') + ' ' + esc(label))
    return lines

def convert(node, url, depth=0):
    blocks=[]
    for child in node.children:
        if isinstance(child, Comment): continue
        if isinstance(child, NavigableString):
            if clean(str(child)): blocks.append(esc(clean(str(child))))
            continue
        tag=child.name
        if tag in ('script','style'): continue
        if tag in ('ul','ol'):
            for li in child.find_all('li', recursive=False):
                nested=li.find_all(['ul','ol'], recursive=False)
                for sub in nested: sub.extract()
                lines=inline(li,url,'- ')
                if lines: blocks.append('\n'.join(' '*depth+l for l in lines))
                for sub in nested:
                    wrapper=BeautifulSoup('<div></div>','html5lib').div
                    wrapper.append(sub)
                    blocks.extend(convert(wrapper,url,depth+1))
        elif tag == 'img':
            if child.get('src'):
                lines=['image '+urljoin(url,child['src'])]
                if child.get('alt'): lines.append(' caption '+esc(clean(child['alt'])))
                blocks.append('\n'.join(lines))
        elif tag in ('div','section','article'):
            if child.get('id'): blocks.append('span\n id '+child['id'])
            blocks.extend(convert(child,url,depth))
        elif tag == 'br': continue
        else:
            # Preserve hard breaks as paragraph boundaries (including dispatch bullets).
            for br in child.find_all('br'): br.replace_with('\n\n')
            if '\n\n' in child.get_text() and tag == 'p':
                fragments=re.split(r'\n\s*\n', str(child))
                for frag in fragments:
                    part=BeautifulSoup(frag,'html5lib').body
                    lines=inline(part,url)
                    if lines: blocks.append('\n'.join(lines))
            else:
                prefix='#'*max(2,int(tag[1]))+' ' if re.fullmatch('h[1-6]',tag) else ''
                lines=inline(child,url,prefix)
                if lines: blocks.append('\n'.join(lines))
            for img in child.find_all('img'):
                if img.get('src'): blocks.append('image '+urljoin(url,img['src']))
    return blocks

posts=[]
for page in json.loads((ROOT/'originals/pages.json').read_text()):
    slug,url=page['slug'],page['url']
    if slug in ('home','dispatches'): continue # dispatches repeats all individual posts
    soup=BeautifulSoup((ROOT/'originals/html'/f'{slug}.html').read_text(),'html5lib')
    body=soup.select_one('#content')
    title=soup.title.get_text().split(' · ')[0]
    heading=body.find('h1')
    if heading:
        title=clean(heading.get_text())
        heading.decompose()
    byline=body.select_one('.byline')
    date=None
    if byline:
        match=re.search(r'\d{4}-\d{2}-\d{2}',byline.get_text())
        if match: date=match[0]
        byline.decompose()
    (ROOT/'originals'/f'{slug}.scroll').write_text(re.sub(r'\n\n(?= )', '\n', '\n\n'.join(convert(body,url)))+'\n')
    posts.append(dict(slug=slug,title=title,date=date or '1900-01-01',url=url,undated=date is None))
(ROOT/'archive.json').write_text(json.dumps(posts,indent=2,ensure_ascii=False)+'\n')
print(f'Converted {len(posts)} pages ({sum(p["undated"] for p in posts)} undated).')
