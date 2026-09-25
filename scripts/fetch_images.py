#!/usr/bin/env python3
"""Save article images locally; rerun after converting source pages."""
import hashlib, json, re, subprocess
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parent.parent
mapping={}
for path in (ROOT/'originals').glob('*.scroll'):
    text=path.read_text()
    for url in re.findall(r'^image (https?://\S+)',text,re.M):
        if url not in mapping:
            suffix=Path(urlsplit(url).path).suffix or '.jpg'
            asset='assets/'+hashlib.sha256(url.encode()).hexdigest()[:16]+suffix
            target=ROOT/asset
            if not target.exists():
                subprocess.run(['curl','-fLsS','--max-time','60',url,'-o',str(target)],check=True)
            mapping[url]=asset
        text=text.replace('image '+url,'image '+mapping[url])
    path.write_text(text)
(ROOT/'originals/images.json').write_text(json.dumps(mapping,indent=2)+'\n')
print(f'Saved {len(mapping)} local images.')
