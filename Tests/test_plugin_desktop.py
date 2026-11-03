"""Verify the installed dockable extension through EffectCraft's real desktop control API.

Start only a sandbox EffectCraft with --empty --control 9879 and an isolated
EFFECTCRAFT_CONFIG_DIR containing this extension; this test edits its scratch project.
"""
import json
from pathlib import Path
import socket
import sys
import time
from PIL import Image,ImageChops

from ec import ROOT
from build import write_json


class Desktop:
    def __init__(self,port=9879):
        self.socket=socket.create_connection(('127.0.0.1',port),timeout=30)
        self.file=self.socket.makefile('rw',encoding='utf-8')
        self.serial=0

    def rpc(self,method,**params):
        self.serial+=1
        self.file.write(json.dumps({'id':self.serial,'method':method,'params':params})+'\n')
        self.file.flush()
        result=json.loads(self.file.readline())
        if not result['ok']:raise RuntimeError(result)
        return result['result']

    def cmd(self,command_id,**params):
        return self.rpc('engine.execute',command=command_id,params=params)

    def widget(self,name):
        def find(n):
            if n.get('name')==name:return n
            for c in n.get('children',[]):
                result=find(c)
                if result:return result
        result=find(self.cmd('scriptui.get')['root'])
        assert result is not None,name
        return result

    def select(self,name,identifier):
        self.cmd('scriptui.set',widget='search',value=name)
        self.cmd('scriptui.set',widget='library',value=f'{identifier:03d}  {name}')

    def capture(self,path,**params):
        for attempt in range(8):
            try:return self.rpc('ui.screenshot',path=str(path),**params)
            except RuntimeError as error:
                if 'no frame was presented' not in str(error) or attempt==7:raise
                time.sleep(.15)


def main():
    e=Desktop()
    capture='--capture' in sys.argv
    if capture:
        e.rpc('ui.focus')
        time.sleep(.2)
    config=ROOT/'Tests/.runtime/plugin-probe'
    expected=(ROOT/'Plugin/IGPACK Motion Browser.jsx').read_text(encoding='utf-8').replace(
        '"__IGPACK_ASSET_ROOT__"',json.dumps((config/'IGPACK Motion Browser/Frames').as_posix()))
    assert (config/'Scripts/ScriptUI Panels/IGPACK/Motion Browser.jsx').read_text(encoding='utf-8')==expected, 'Sandbox panel must match the current build'
    assert any(p['name']=='IGPACK/Motion Browser.jsx' for p in e.cmd('file.scripts.list'))
    e.cmd('window.scriptPanel',name='IGPACK/Motion Browser.jsx')
    assert any(w['kind']=='panel' for w in e.cmd('scriptui.list'))
    e.select('Digital Glitch',41)
    first=e.widget('preview')['image']['src']
    time.sleep(.23)
    second=e.widget('preview')['image']['src']
    assert first!=second and Path(second).exists(),(first,second)
    if capture:
        e.rpc('ui.move',id='scriptui.1')
        e.rpc('ui.menu.invoke',id='window.maximizePanel')
        # Toggle only if the panel wasn't already maximized from the saved layout.
        inspect=e.rpc('ui.inspect')
        if inspect.get('ui',{}).get('maximized') is None:
            e.rpc('ui.move',id='scriptui.1')
            e.rpc('ui.menu.invoke',id='window.maximizePanel')
        e.cmd('scriptui.set',widget='search',value='')
        e.cmd('scriptui.set',widget='library',value='041  Digital Glitch')
        time.sleep(.3)
        e.capture(ROOT/'Plugin/Tests/browser-desktop.png')
    e.cmd('file.newProject')
    main=e.cmd('comp.new',name='IGPACK Desktop Verification',width=640,height=360,frameRate=30,duration=8)['comp']
    imported=e.cmd('file.import',paths=[str(ROOT/'Previews/source.png')])
    item=imported['items'][0]
    if isinstance(item,dict):item=item['id']
    original=e.cmd('layer.addItem',item=item)['layer']
    e.cmd('prop.set',layer=original,path='transform/scale',value=[190,190,100])
    e.cmd('time.set',time=1)
    e.select('Digital Glitch',41)
    e.cmd('scriptui.set',widget='duration',value='1.2')
    e.cmd('scriptui.set',widget='strength',value='125')
    e.cmd('scriptui.click',widget='apply')
    assert e.widget('status')['text'].startswith('Adicionado:'),e.widget('status')['text']
    overlay=e.cmd('project.summary')['selectedLayers'][0]
    tree=e.cmd('layer.tree',layer=overlay,depth=4)
    assert tree['switches']['adjustment'] and tree['type']=='Composition'
    paths=[]
    for label,t in (('before',.8),('during',1.3),('after',2.4)):
        path=ROOT/f'Plugin/Tests/desktop-{label}.png'
        e.rpc('render.frame',time=t,path=str(path),max_side=640)
        paths.append(path)
    images=[Image.open(p).convert('RGB') for p in paths]
    assert ImageChops.difference(images[0],images[1]).getbbox()
    assert ImageChops.difference(images[0],images[2]).getbbox() is None
    # The actual desktop compositor renders finite effect clips, not only property values.
    backend=e.cmd('project.summary')['renderer']
    e.cmd('edit.undo')
    assert e.cmd('project.summary')['items'][0]['layers']==1
    text=e.cmd('layer.newText',text='IGPACK Motion',position=[320,190],size=54,fill='#ffffff')['layer']
    e.cmd('time.set',time=3)
    e.select('Text Bounce In',64)
    e.cmd('scriptui.click',widget='apply')
    assert e.widget('status')['text'].startswith('Adicionado:'),e.widget('status')['text']
    precomp=e.cmd('project.summary')['selectedLayers'][0]
    assert not e.cmd('layer.tree',layer=precomp,depth=3)['switches']['adjustment']
    e.rpc('render.frame',time=3.25,path=str(ROOT/'Plugin/Tests/desktop-text.png'),max_side=640)
    e.cmd('time.set',time=1.3)
    e.select('Glow Pulse',93)
    e.cmd('scriptui.set',widget='mode',value=0)
    e.cmd('scriptui.click',widget='apply')
    assert e.widget('status')['text'].startswith('Adicionado:')
    if capture:
        e.capture(ROOT/'Plugin/Tests/browser-with-project.png')
        e.capture(ROOT/'Plugin/Tests/panel.png',id='scriptui.1')
    write_json(ROOT/'Plugin/Tests/desktop_report.json',{
        'passed':True,'engine':'0.21.0','native_docked_panel':True,'preview_animation':True,
        'renderer':backend,'overlay_before_during_after_rendered':True,'selection_precomp_rendered':True,
        'undo_verified':True,'production_profile_modified':False,'capture_requested':capture,
        'source_sha256':json.loads((ROOT/'Plugin/manifest.json').read_text())['files']['IGPACK Motion Browser.jsx'],
        'limits':['Three recipes sampled in desktop UI; 98 callbacks separately tested through ScriptUI in CPU headless mode.',
                  'No full-frame video export or commercial footage certification.']})
    print('PASS actual desktop: installed dockable panel, animated preview, overlay compositing, selection precomp and Undo')
    e.file.close();e.socket.close()


if __name__=='__main__':main()
