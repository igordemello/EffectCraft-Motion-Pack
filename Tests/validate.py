"""Structural checks + real 0.21.0 CPU integration and original fixture previews."""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import time

from build import CATEGORIES, TICKS, props, write_json
from ec import Engine, ROOT


def structure(doc, canonical):
    assert doc['effectcraftAnimationPreset'] == 2
    assert doc['properties'] == [] and doc['effects']
    animated = False
    for group in doc['effects']:
        identifier = group['kind']['effect']
        assert identifier in canonical, identifier
        allowed = dict(props(canonical[identifier]))
        actual = dict(props(group))
        assert actual.keys() == allowed.keys()
        for path, p in actual.items():
            assert p['value']['t'] == allowed[path]['value']['t'], path
            vals = [p['value']] + [k['value'] for k in p.get('keys', [])]
            for val in vals:
                assert val['t'] == p['value']['t']
                v = val['v']
                if val['t'] in ('Scalar', 'Enum'):
                    assert isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                    if val['t'] == 'Enum':
                        assert type(v) is int and 0 <= v < len(p['ui']['options'])
                elif val['t'] == 'Bool':
                    assert type(v) is bool
                elif val['t'] == 'Str':
                    assert isinstance(v,str)
                else:
                    dims = {'Vec2':2,'Vec3':3,'Color':4}[val['t']]
                    assert len(v) == dims and all(isinstance(x,(int,float)) and math.isfinite(x) for x in v)
            keys = p.get('keys', [])
            times = [k['time'] for k in keys]
            assert all(type(t) is int and 0 <= t <= 10*TICKS for t in times)
            assert times == sorted(set(times))
            for k in keys:
                assert k.get('in_interp','Linear') in ('Bezier','Linear','Hold')
                for side in ('in_ease','out_ease'):
                    assert all(0 < x['influence'] <= 1 and math.isfinite(x['speed']) for x in k.get(side,[]))
            if len(keys) >= 2 and len({json.dumps(k['value']) for k in keys}) > 1:
                animated = True
            if p.get('expr'):
                assert p['expr']['enabled'] and p['expr']['text'].strip()
                if 'key(1)' in p['expr']['text']:
                    assert keys
                animated |= 'time' in p['expr']['text']
    assert animated, 'Empty or static animation'


def signature(doc):
    effects = copy.deepcopy(doc['effects'])
    for group in effects:
        group.pop('uid',None)
        for _,p in props(group):
            p.pop('uid',None)
    return hashlib.sha256(json.dumps(effects,sort_keys=True).encode()).hexdigest()


def self_check(doc, canonical):
    for mutate in ('effect','path','type','empty'):
        bad=copy.deepcopy(doc)
        if mutate=='effect': bad['effects'][0]['kind']['effect']='ec.does.not.exist'
        elif mutate=='path': bad['effects'][0]['children'][0]['match']='nonexistent'
        elif mutate=='type': bad['effects'][0]['children'][0]['value']['t']='Bool'
        else:
            for group in bad['effects']:
                for _,p in props(group):
                    p.pop('keys',None);p.pop('expr',None)
        try:
            structure(bad,canonical)
        except (AssertionError,KeyError,TypeError):
            continue
        raise AssertionError(f'Validator failed to reject {mutate}')


def fixture():
    from PIL import Image, ImageDraw
    path=ROOT/'Previews/source.png'
    path.parent.mkdir(exist_ok=True)
    im=Image.new('RGBA',(240,136),(0,0,0,0))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((8,8,232,128),radius=15,fill='#17488f',outline='#64d4ff',width=3)
    for x,color in ((25,'#ff667f'),(80,'#78f5c7'),(135,'#fcd56b')):
        d.rectangle((x,28,x+35,56),fill=color)
    d.text((26,76),'EffectCraft',fill='white',font_size=24)
    d.line((26,110,210,110),fill='white',width=2)
    im.save(path)
    return path


def scene(e,w=320,h=180,fps=30,text=False,source=None):
    e.tool('open_project',{'new':True})
    e.cmd('comp.new',name='Motion Pack test',width=w,height=h,frameRate=fps,duration=7)
    if text:
        lid=e.cmd('layer.newText',text='EffectCraft',position=[w*.5,h*.54],size=w*.1,fill='#ffffff')['layer']
    elif source:
        imported=e.cmd('file.import',paths=[str(source)])
        # file.import returns its imported item ids.
        items=imported.get('items', imported.get('imported',[]))
        if not items:
            summary=e.cmd('project.summary')
            items=[i['id'] for i in summary['items'] if i['type']=='Footage']
        first=items[0]
        if isinstance(first,dict): first=first['id']
        lid=e.cmd('layer.addItem',item=first)['layer']
        scale=w/320*100
        e.cmd('prop.set',layer=lid,path='transform/scale',value=[scale,scale,100])
    else:
        lid=e.cmd('layer.newSolid',name='Integration fixture',color='#67b5ec',width=w//2,height=h//2)['layer']
    return lid


def integration(e,lid,doc,meta,at=.5):
    originals={p:e.cmd('prop.get',layer=lid,path='transform/'+p)['value'] for p in ('position','scale','rotation','opacity')}
    e.cmd('time.set',time=at)
    result=e.cmd('anim.applyPreset',layers=[lid],path=str(ROOT/meta['path']))
    assert result['skipped']==[] and result['applied']==len(doc['effects']),result
    records=[]
    for index,g in enumerate(doc['effects'],1):
        for path,p in props(g):
            if not p.get('expr') and not p.get('keys'): continue
            values=[]
            samples=sorted(set([0,meta['duration']*.23,meta['duration']*.57,meta['duration'],meta['duration']+.1]))
            for dt in samples:
                q=e.cmd('prop.get',layer=lid,path=f'effects/#{index}/{path}',time=at+dt)
                assert 'expressionError' not in q,q
                val=q.get('evaluated',q['value'])
                for x in val if isinstance(val,list) else [val]:
                    assert isinstance(x,(int,float)) and math.isfinite(x),q
                values.append(val)
            if p.get('keys'):
                assert abs(e.cmd('prop.get',layer=lid,path=f'effects/#{index}/{path}')['keys'][0]['time']-at)<1e-5
            records.append({'path':f'effects/#{index}/{path}','samples':values})
    for p,val in originals.items():
        assert e.cmd('prop.get',layer=lid,path='transform/'+p)['value']==val
    return records


def render_preview(e,meta):
    from PIL import Image,ImageDraw,ImageChops
    folder=ROOT/'Previews'/f"{meta['id']:03d}"
    folder.mkdir(parents=True,exist_ok=True)
    frames=[]
    duration=meta['duration']
    for i in range(13):
        t=.5+duration*i/12
        path=folder/f'{i:02d}.png'
        e.tool('render_frame',{'time':t,'max_side':320,'path':str(path),'inline':False,'transparent':False})
        im=Image.open(path).convert('RGB')
        canvas=Image.new('RGB',(320,210),'#0c1424')
        canvas.paste(im,(0,0))
        draw=ImageDraw.Draw(canvas)
        draw.text((8,184),f"{meta['id']:03d} {meta['name']}",fill='white')
        draw.text((8,198),f'{duration:g}s | CPU EffectCraft 0.21.0',fill='#a4bad5')
        frames.append(canvas)
    changed=any(ImageChops.difference(frames[0].crop((0,0,320,180)),im.crop((0,0,320,180))).getbbox() for im in frames[1:])
    assert changed, f"No rendered change: {meta['id']} {meta['name']}"
    gif=ROOT/'Previews'/f"{meta['id']:03d} - {meta['name']}.gif"
    delay=max(20,round(duration*1000/12/10)*10)
    frames[0].save(gif,save_all=True,append_images=frames[1:]+[frames[-1]]*3,duration=delay,loop=0)
    # Keep the four sampled frames for visual audit, discard other generated intermediates.
    for i in range(13):
        if i not in (0,3,7,12): (folder/f'{i:02d}.png').unlink()
    return {'changed':True,'gif':gif.relative_to(ROOT).as_posix(),'frames':13}


def main():
    started=time.time()
    poc='--poc' in sys.argv
    catalog=json.loads((ROOT/('Tests/poc_catalog.json' if poc else 'Documentation/catalog.json')).read_text(encoding='utf-8'))
    canonical=json.loads((ROOT/'Documentation/native_effects.json').read_text(encoding='utf-8'))
    if not poc:
        expected={str((ROOT/m['path']).resolve()) for m in catalog if m['implemented']}
        actual={str(p.resolve()) for p in ROOT.glob('*/*.ecpreset')}
        assert actual==expected, 'Missing or unexpected preset files'
    seen={};results=[];failed=[]
    source=fixture()
    with Engine() as e:
        for meta in catalog:
            if not meta['implemented']: continue
            try:
                path=ROOT/meta['path'];doc=json.loads(path.read_text(encoding='utf-8'))
                assert path.parent.name in CATEGORIES
                structure(doc,canonical)
                sig=signature(doc)
                assert sig not in seen, f"Duplicate of {seen.get(sig)}"
                seen[sig]=meta['id']
                if len(seen)==1:self_check(doc,canonical)
                matrices=[]
                if not poc:
                    for w,h in ((1920,1080),(1080,1920)):
                        for fps in (24,30,60):
                            lid=scene(e,w,h,fps,text=meta['category']=='04_Text_Animations')
                            integration(e,lid,doc,meta)
                            matrices.append(f'{w}x{h}@{fps}')
                lid=scene(e,text=meta['category']=='04_Text_Animations',source=source)
                samples=integration(e,lid,doc,meta)
                visual=render_preview(e,meta)
                results.append({'id':meta['id'],'name':meta['name'],'structural':True,
                                'engine_integration':True,'matrix':matrices,'sampled_parameters':samples,
                                'rendered_cpu':visual,'visually_reviewed_in_app':False})
                print(f"PASS {meta['id']:03d} {meta['name']}",flush=True)
            except Exception as error:
                failed.append({'id':meta['id'],'error':str(error)})
                print(f"FAIL {meta['id']:03d}: {error}",flush=True)
    report={'passed':not failed,'engine_version':'0.21.0','renderer':'CPU/headless',
            'upstream_commit':'7870b5916ae0749d497d880989683bf2946d6c8b',
            'elapsed_seconds':round(time.time()-started,1),'loaded_from_files':True,'results':results,'failures':failed,
            'not_tested':['GPU','visual playback in the desktop application','commercial footage','all frames at all FPS']}
    write_json(ROOT/('Tests/poc_report.json' if poc else 'Tests/compatibility_report.json'),report)
    assert not failed,f'{len(failed)} presets failed; inspect report'


if __name__=='__main__':main()
