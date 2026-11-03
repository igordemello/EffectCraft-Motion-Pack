"""Exercise actual native ScriptUI callbacks, layers and rendering, not a mock UI."""
import json
from pathlib import Path
import subprocess
import tempfile
import time
from PIL import Image,ImageChops

from ec import ROOT,Engine,find_cli
from build import write_json,props
from validate import scene,fixture


def widget(e,name):
    def walk(n):
        if n.get('name')==name:return n
        for c in n.get('children',[]):
            found=walk(c)
            if found:return found
    result=walk(e.cmd('scriptui.get')['root'])
    assert result is not None,name
    return result


def select(e,name):
    e.cmd('scriptui.set',widget='search',value=name)
    catalog=json.loads((ROOT/'Documentation/catalog.json').read_text(encoding='utf-8'))
    identifier=next(m['id'] for m in catalog if m['name']==name)
    e.cmd('scriptui.set',widget='library',value=f'{identifier:03d}  {name}')
    assert widget(e,'selectedName')['text']==name


def install(mode,config):
    return subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
                           str(ROOT/'Scripts/Manage-Plugin.ps1'),'-Mode',mode,'-ConfigDir',str(config),
                           '-CliPath',find_cli()],capture_output=True,text=True,errors='replace')


def main():
    runtime=ROOT/'Tests/.runtime'
    runtime.mkdir(exist_ok=True)
    report={'engine':'0.21.0','passed':False,'cases':[],'desktop_ui':False}
    with tempfile.TemporaryDirectory(prefix='native-plugin-',dir=runtime) as temp:
        config=Path(temp)/'Config'
        r=install('Install',config)
        assert r.returncode==0,r.stderr
        panel=config/'Scripts/ScriptUI Panels/IGPACK/Motion Browser.jsx'
        assert panel.exists() and len(list((config/'IGPACK Motion Browser/Frames').rglob('*.png')))==1274
        assert '__IGPACK_ASSET_ROOT__' not in panel.read_text(encoding='utf-8')
        assert install('Install',config).returncode!=0
        report['cases'].append('Native installer: panel + 1274 frames, absolute asset paths, duplicate install refused')
        with Engine(config_dir=config) as e:
            e.cmd('comp.new',name='Browser integration',width=320,height=180,frameRate=30,duration=8)
            wrapped='(function () {\n'+panel.read_text(encoding='utf-8')+'\n}).call(this);'
            opened=e.cmd('script.run',code=wrapped,name=str(panel))
            assert opened['ok'],opened
            assert e.cmd('scriptui.list')[0]['kind']=='palette'
            assert len(widget(e,'library')['items'])==98
            path0=widget(e,'preview')['image']['src']
            time.sleep(.15)
            e.cmd('script.runTasks')
            path1=widget(e,'preview')['image']['src']
            assert path0!=path1 and Path(path1).exists(),(path0,path1)
            e.cmd('scriptui.click',widget='play')
            paused=widget(e,'preview')['image']['src']
            time.sleep(.1);e.cmd('script.runTasks')
            assert widget(e,'preview')['image']['src']==paused
            e.cmd('scriptui.click',widget='play')
            e.cmd('scriptui.resize',size=[300,900])
            button=widget(e,'apply')['bounds'];message=widget(e,'status')['bounds']
            assert button[0]+button[2]<=300 and message[1]>=button[1]+button[3]
            e.cmd('scriptui.resize',size=[660,720])
            report['cases'].append('Narrow 300px panel keeps Apply visible and status below controls; pause holds the preview frame')
            report['cases'].append('Installed ScriptUI source opened as palette in isolated headless session; preview PNG advances through scheduled task')
            e.cmd('scriptui.set',widget='search',value='no-such-effect')
            assert not widget(e,'apply')['enabled']
            e.cmd('scriptui.set',widget='search',value='')
            e.cmd('scriptui.set',widget='category',value=4)
            assert len(widget(e,'library')['items'])==15
            e.cmd('scriptui.set',widget='category',value=0)
            report['cases'].append('Search, empty search result, disabled Apply and category filtering')
            catalog=json.loads((ROOT/'Documentation/catalog.json').read_text(encoding='utf-8'))
            source=fixture()
            results=[]
            for meta in catalog:
                if not meta['implemented']:continue
                text=meta['category']=='04_Text_Animations'
                lid=scene(e,text=text,source=source)
                assert e.cmd('scriptui.list'), 'Panel must survive project replacement'
                e.cmd('time.set',time=.5)
                select(e,meta['name'])
                mode=1 if meta['category'] in ('04_Text_Animations','05_Pop_Bounce_Scale') else 0
                e.cmd('scriptui.set',widget='mode',value=mode)
                d=max(1,round(meta['duration']*1.5*30))/30
                e.cmd('scriptui.set',widget='duration',value=str(d))
                e.cmd('scriptui.set',widget='strength',value='75')
                before=e.cmd('project.summary')
                e.cmd('scriptui.click',widget='apply')
                message=widget(e,'status')['text']
                assert message.startswith('Adicionado:'),(meta['id'],message)
                summary=e.cmd('project.summary')
                new=summary['selectedLayers'][0]
                tree=e.cmd('layer.tree',layer=new,depth=5)
                assert tree['type']=='Composition',tree['type']
                assert tree['switches']['adjustment']==(mode==0)
                assert tree['index']==1
                if mode==0:
                    assert abs(tree['in']-.5)<1e-6 and abs(tree['out']-(.5+d))<1e-6
                    assert len([i for i in summary['items'] if i['type']=='Composition'])==2
                else:
                    assert next(i for i in summary['items'] if i['id']==summary['activeComp'])['layers']==1
                def walk(n):
                    if 'children' in n:
                        for c in n['children']:yield from walk(c)
                    else:yield n
                animated=[]
                for p in walk(tree['properties']):
                    if p.get('keys') or p.get('expression'):
                        for dt in (0,d*.15,d*.6,d):
                            q=e.cmd('prop.get',layer=new,path=p['path'],time=.5+dt)
                            assert 'expressionError' not in q,(meta['id'],q)
                        animated.append(p['path'])
                assert animated,meta['id']
                if meta['id'] in (1,26,41,56,71,86,91):
                    folder=ROOT/'Plugin/Tests/Rendered'/f"{meta['id']:03d}"
                    folder.mkdir(parents=True,exist_ok=True)
                    images=[]
                    for k,dt in enumerate((-.1,d*.15,d*.6,d+.1)):
                        path=folder/f'{k}.png'
                        e.tool('render_frame',{'time':.5+dt,'max_side':320,'path':str(path),'inline':False})
                        images.append(Image.open(path).convert('RGB'))
                    assert any(ImageChops.difference(images[0],im).getbbox() for im in images[1:])
                    if mode==0:assert ImageChops.difference(images[0],images[-1]).getbbox() is None
                    # Moving the overlay preserves its local keys and shifts the effect in time.
                    if mode==0:
                        values={p:e.cmd('prop.get',layer=new,path=p,time=.5+d*.15) for p in animated}
                        e.cmd('layer.timing',layers=[new],delta=1.0)
                        for p in animated:
                            q=e.cmd('prop.get',layer=new,path=p,time=1.5+d*.15)
                            assert 'expressionError' not in q
                            a=values[p].get('evaluated',values[p]['value']);b=q.get('evaluated',q['value'])
                            if isinstance(a,list):assert all(abs(x-y)<1e-5 for x,y in zip(a,b)),(meta['id'],p,a,b)
                            else:assert abs(a-b)<1e-5,(meta['id'],p,a,b)
                # One Undo reverses both the inserted precomp and its effect stack, never source data.
                if meta['id'] not in (1,26,41,86,91):
                    e.cmd('edit.undo')
                    restored=e.cmd('project.summary')
                    assert len(restored['items'])==len(before['items']),(meta['id'],'undo failed')
                results.append({'id':meta['id'],'mode':'selection_precomp' if mode else 'overlay_precomp','duration':d,'strength':75,'passed':True})
                print(f"PASS native callback {meta['id']:03d} {meta['name']}",flush=True)
            report['results']=results
            report['cases'].append('98 real Apply callbacks at 150% duration and 75% strength; editable precomp layers and valid expressions')
            lid=scene(e,source=source)
            select(e,'Text Bounce In')
            e.cmd('layer.select',layers=[])
            before=e.cmd('project.summary')
            e.cmd('scriptui.click',widget='apply')
            assert widget(e,'status')['text'].startswith('Não aplicado:')
            assert e.cmd('project.summary')['items']==before['items']
            e.cmd('scriptui.set',widget='mode',value=0)
            e.cmd('scriptui.set',widget='duration',value='NaN')
            e.cmd('scriptui.click',widget='apply')
            assert e.cmd('project.summary')['items']==before['items']
            e.cmd('scriptui.set',widget='duration',value='30')
            e.cmd('scriptui.click',widget='apply')
            assert e.cmd('project.summary')['items']==before['items']
            report['cases'].append('Missing selection, non-finite duration and insufficient timeline room rejected without edits')
            for w,h,fps in ((1920,1080,24),(1080,1920,60)):
                scene(e,w,h,fps,text=True)
                e.cmd('time.set',time=.5)
                select(e,'Text Bounce In')
                e.cmd('scriptui.set',widget='duration',value='0.8')
                e.cmd('scriptui.click',widget='apply')
                assert widget(e,'status')['text'].startswith('Adicionado:')
            report['cases'].append('Selection precomp also applies at 1920x1080@24 and 1080x1920@60')
            e.cmd('scriptui.close')
            time.sleep(.08)
            tasks=e.cmd('script.runTasks')
            assert tasks['ran']==0 and tasks['next'] is None,tasks
            report['cases'].append('Closing panel cancels preview task')
        with Engine() as e:
            scene(e,source=source)
            e.cmd('prefs.set',key='general.undoLevels',value=2)
            for value in (97,98,99):e.cmd('prop.set',path='transform/opacity',value=value)
            before=e.cmd('project.summary')
            # Fault injection after the overlay exists proves rollback at a full undo history.
            injection="""var originalRun=app.run; app.run=function(id,p){
                if(id==='anim.applyPreset')throw new Error('Injected application failure');
                return originalRun(id,p);};"""
            loaded=e.cmd('script.run',code=wrapped+injection,name='rollback-test.jsx')
            assert loaded['ok'],loaded
            e.cmd('scriptui.click',widget='apply')
            assert widget(e,'status')['text'].startswith('Não aplicado:')
            after=e.cmd('project.summary')
            assert before['items']==after['items'],'Partial edit was not rolled back'
            assert e.cmd('prop.get',path='transform/opacity')['value']==99
            e.cmd('scriptui.close')
            report['cases'].append('Injected application failure rolls back new precomp and leaves source intact, even with full undo history')
        unrelated=config/'Scripts/ScriptUI Panels/User Panel.jsx'
        unrelated.write_text('user panel')
        panel.write_text(panel.read_text(encoding='utf-8')+'\n// customization',encoding='utf-8')
        assert install('Uninstall',config).returncode!=0
        assert panel.exists() and unrelated.read_text()=='user panel'
        assert not list((config/'IGPACK Motion Browser/Frames').rglob('*.png'))
        panel.unlink()
        r=install('Uninstall',config)
        assert r.returncode==0,r.stderr
        assert unrelated.exists()
        report['cases'].append('Uninstall preserves modified panel and unrelated scripts; removes only original assets')
    report['passed']=True
    report['source_sha256']=json.loads((ROOT/'Plugin/manifest.json').read_text())['files']['IGPACK Motion Browser.jsx']
    write_json(ROOT/'Plugin/Tests/integration_report.json',report)
    print('PASS all native plugin checks',flush=True)


if __name__=='__main__':main()
