"""Build a native ScriptUI extension from the already validated native recipes."""
import copy
import json
from pathlib import Path
from PIL import Image

from build import CATEGORIES,props,write_json
from ec import ROOT


def main():
    canonical=json.loads((ROOT/'Documentation/native_effects.json').read_text(encoding='utf-8'))
    catalog=json.loads((ROOT/'Documentation/catalog.json').read_text(encoding='utf-8'))
    items=[]
    frames=ROOT/'Plugin/Frames'
    for meta in catalog:
        if not meta['implemented']: continue
        doc=json.loads((ROOT/meta['path']).read_text(encoding='utf-8'))
        effects=[]
        for g in doc['effects']:
            identifier=g['kind']['effect'];base=dict(props(canonical[identifier]));changes={}
            for path,p in props(g):
                if p['value']!=base[path]['value'] or p.get('keys') or p.get('expr'):
                    changes[path]={k:copy.deepcopy(p[k]) for k in ('value','keys','expr') if k in p}
            effects.append({'id':identifier,'changes':changes})
        items.append({'id':meta['id'],'name':meta['name'],'category':CATEGORIES.index(meta['category']),
                      'duration':meta['duration'],'effects':effects})
        gif=Image.open(ROOT/'Previews'/f"{meta['id']:03d} - {meta['name']}.gif")
        folder=frames/f"{meta['id']:03d}"
        folder.mkdir(parents=True,exist_ok=True)
        # GIF frames were rendered by EffectCraft; decode them into the UI's supported PNGs.
        for index in range(13):
            gif.seek(min(index,gif.n_frames-1))
            gif.convert('RGB').crop((0,0,320,180)).save(folder/f'{index:02d}.png',optimize=True)
    data={'groups':canonical,'items':items}
    template=(ROOT/'Plugin/Browser.template.jsx').read_text(encoding='utf-8')
    source=template.replace('__IGPACK_DATA__',json.dumps(data,ensure_ascii=True,separators=(',',':')))
    panel=ROOT/'Plugin/IGPACK Motion Browser.jsx'
    panel.write_text(source,encoding='utf-8')
    hashes={}
    import hashlib
    for path in [panel,*sorted(frames.rglob('*.png'))]:
        hashes[path.relative_to(ROOT/'Plugin').as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    assert len(items)==98 and len(hashes)==1275
    write_json(ROOT/'Plugin/manifest.json',{'version':'2.0.0','engine':'0.21.0','files':hashes})
    print(f'Built native panel: {len(items)} recipes, 1274 PNG frames, {panel.stat().st_size:,} bytes JSX')


if __name__=='__main__':main()
