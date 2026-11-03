"""Deterministic original recipes; canonical instances come from EffectCraft 0.21.0."""
import copy
import hashlib
import json
from pathlib import Path
import sys

from ec import Engine, ROOT

TICKS = 254_016_000_000
CATEGORIES = ['01_Transitions', '02_Camera_Shake', '03_Glitch_Distortion',
              '04_Text_Animations', '05_Pop_Bounce_Scale', '06_Blur_Flash_Glow']
NAMES = [
    'Smooth Zoom In', 'Smooth Zoom Out', 'Fast Zoom In', 'Fast Zoom Out',
    'Whip Pan Left', 'Whip Pan Right', 'Whip Pan Up', 'Whip Pan Down',
    'Smooth Slide Left', 'Smooth Slide Right', 'Smooth Slide Up', 'Smooth Slide Down',
    'Spin Transition CW', 'Spin Transition CCW', 'Fast Rotation', 'Smooth Rotation',
    'Blur In', 'Blur Out', 'Directional Blur Left', 'Directional Blur Right',
    'Flash Transition', 'White Flash', 'Black Flash', 'Elastic Zoom', 'Cinematic Push',
    'Subtle Camera Shake', 'Medium Camera Shake', 'Heavy Camera Shake', 'Impact Shake',
    'Explosion Shake', 'Handheld Camera', 'Cinematic Handheld', 'Horizontal Shake',
    'Vertical Shake', 'Rotation Shake', 'Micro Jitter', 'Smooth Camera Drift',
    'Camera Punch', 'Camera Bounce', 'Camera Recoil',
    'Digital Glitch', 'RGB Split', 'RGB Split Heavy', 'Chromatic Glitch',
    'Digital Interference', 'Signal Distortion', 'Glitch Flicker', 'Pixel Distortion',
    'Horizontal Glitch', 'Vertical Glitch', 'VHS Distortion', 'Digital Breakdown',
    'Glitch Reveal', 'Glitch Exit', 'Cyberpunk Glitch',
    'Smooth Text Fade In', 'Smooth Text Fade Out', 'Text Slide Up', 'Text Slide Down',
    'Text Slide Left', 'Text Slide Right', 'Text Pop In', 'Text Pop Out',
    'Text Bounce In', 'Text Bounce Out', 'Text Elastic In', 'Text Elastic Out',
    'Text Scale Reveal', 'Text Overshoot', 'Text Cinematic Reveal',
    'Smooth Pop In', 'Smooth Pop Out', 'Fast Pop In', 'Fast Pop Out', 'Elastic Pop',
    'Bounce In', 'Bounce Out', 'Overshoot Scale', 'Smooth Scale Up', 'Smooth Scale Down',
    'Spring Scale', 'Rubber Scale', 'Punch Scale', 'UI Button Pop', 'Dynamic Bounce',
    'Smooth Blur In', 'Smooth Blur Out', 'Fast Blur', 'Focus Reveal', 'Focus Exit',
    'Soft Glow', 'Intense Glow', 'Glow Pulse', 'Neon Glow', 'Light Flash',
    'Impact Flash', 'Exposure Flash', 'Flicker Light', 'Cinematic Bloom', 'Dreamy Blur']
IDS = ['ec.distort.transform', 'ec.blur.gaussian', 'ec.blur.directional',
       'ec.stylize.glow', 'ec.color.exposure', 'ec.distort.turbulentdisplace',
       'ec.vr.digitalglitch', 'ec.vr.chromaticaberrations']
SHORT = dict(zip(['tr', 'blur', 'dir', 'glow', 'exposure', 'turb', 'glitch', 'chroma'], IDS))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def capture():
    """Use the real save command, including full parameter definitions and defaults."""
    with Engine() as e:
        e.cmd('comp.new', name='Canonical capture', width=320, height=180, frameRate=30, duration=4)
        lid = e.cmd('layer.newSolid', name='Source', width=160, height=90, color='#4567ad')['layer']
        registry = e.cmd('effect.list')
        write_json(ROOT / 'Documentation/effect_registry.json', registry)
        groups = {}
        for index, effect in enumerate(IDS):
            applied = e.cmd('effect.apply', effect=effect, layers=[lid])
            e.cmd('prop.select', layer=lid, prop=applied['effects'][0])
            path = ROOT / f'Tests/.runtime/capture-{index}.ecpreset'
            if path.exists():
                path.unlink()
            e.cmd('anim.savePreset', path=str(path), name=effect)
            saved = json.loads(path.read_text(encoding='utf-8'))
            assert saved['effectcraftAnimationPreset'] == 2
            assert len(saved['effects']) == 1
            groups[effect] = saved['effects'][0]
            path.unlink()
        write_json(ROOT / 'Documentation/native_effects.json', groups)
        return groups


def props(group, prefix=''):
    for child in group.get('children', []):
        path = prefix + child['match']
        if child['node'] == 'Prop':
            yield path, child
        else:
            yield from props(child, path + '/')


def key(t, value, ease=True):
    k = {'time': round(t * TICKS), 'value': copy.deepcopy(value)}
    if ease and value['t'] not in ('Bool', 'Enum'):
        n = len(value['v']) if isinstance(value['v'], list) else 1
        k.update(in_interp='Bezier', out_interp='Bezier',
                 in_ease=[{'speed': 0.0, 'influence': 1 / 3}] * n,
                 out_ease=[{'speed': 0.0, 'influence': 1 / 3}] * n)
    elif value['t'] in ('Bool', 'Enum'):
        k.update(in_interp='Hold', out_interp='Hold')
    return k


def effect(groups, kind, sets=None, curves=None, expressions=None):
    g = copy.deepcopy(groups[SHORT[kind]])
    lookup = dict(props(g))
    if kind == 'tr':
        expressions = {'anchor': '[thisLayer.width/2,thisLayer.height/2]',
                       'position': '[thisLayer.width/2,thisLayer.height/2]', **(expressions or {})}
    for path, val in (sets or {}).items():
        lookup[path]['value']['v'] = val
    for path, points in (curves or {}).items():
        p = lookup[path]
        p['keys'] = [key(t, dict(p['value'], v=val)) for t, val in points]
        p['value'] = copy.deepcopy(p['keys'][0]['value'])
    for path, body in (expressions or {}).items():
        lookup[path]['expr'] = {'text': body, 'enabled': True}
    return g


def recipe(groups, number):
    fx = []
    duration = 0.6
    notes = ''
    intensity = 'medium'

    def add(kind, sets=None, curves=None, expressions=None):
        g = effect(groups, kind, sets, curves, expressions)
        fx.append(g)
        return g

    def tr(curves=None, sets=None, expressions=None):
        return add('tr', sets, curves, expressions)

    def move(points):
        return tr({'position': points}, expressions={'position':
            '[thisLayer.width/2+value[0]*thisComp.width,thisLayer.height/2+value[1]*thisComp.height]'})

    def blur(points, amount=1):
        return add('blur', {'repeatEdge': True}, {'blurriness': points},
                   {'blurriness': f'value*thisComp.width/1920*{amount}'})

    def flash(points):
        return add('exposure', curves={'master/exposure': points})

    def glitch(amp, geom=35, color=40, scan=12, rate=14, bands=28):
        return add('glitch', {'geometricDistortion': geom, 'colorDistortion': color,
                             'scanlines': scan, 'distortionRate': rate,
                             'distortionComplexity': bands, 'randomSeed': number * 17},
                   {'masterAmplitude': amp})

    def glow(radius, strength, threshold=55, curves=None):
        return add('glow', {'radius': radius, 'intensity': strength, 'threshold': threshold},
                   curves, {'radius': 'value*thisComp.width/1920'})

    if number in (42, 43):
        return None, {'reason': 'Uniform 2D RGB channel translation is not a native preset operation; VR aberrations are spherical, and VR glitch splits channels only in random bands.'}
    if number <= 4:
        duration = .6 if number < 3 else .22
        start = 155 if number in (1, 3) else 70
        tr({'scaleHeight': [(0, start), (duration, 100)], 'opacity': [(0, 0), (duration * .55, 100)]})
    elif number <= 12:
        fast = number <= 8
        duration = .28 if fast else .7
        axis = (number - 5) % 4
        offset = [(1.1, 0), (-1.1, 0), (0, 1.1), (0, -1.1)][axis]
        move([(0, list(offset)), (duration, [0, 0])])
        if fast:
            add('dir', {'direction': 90 if axis < 2 else 0}, {'length': [(0, 100), (duration, 0)]}, {'length': 'value*thisComp.width/1920'})
        notes = 'Incoming layer travels in the named direction; overlap it above the outgoing clip.'
    elif number <= 16:
        duration = .28 if number == 15 else .85 if number == 16 else .55
        angle = {13: -180, 14: 180, 15: -75, 16: 28}[number]
        tr({'rotation': [(0, angle), (duration, 0)], 'scaleHeight': [(0, 65 if number < 15 else 90), (duration, 100)], 'opacity': [(0, 0), (duration * .65, 100)]})
    elif number <= 20:
        duration = .42
        if number < 19:
            incoming = number == 17
            blur([(0, 65 if incoming else 0), (duration, 0 if incoming else 65)])
            tr({'opacity': [(0, 0 if incoming else 100), (duration, 100 if incoming else 0)]})
        else:
            add('dir', {'direction': 90}, {'length': [(0, 90), (duration, 0)]}, {'length': 'value*thisComp.width/1920'})
            move([(0, [.14 if number == 19 else -.14, 0]), (duration, [0, 0])])
    elif number <= 23:
        duration = .32 if number == 21 else .24 if number == 22 else .38
        peak = 3 if number == 21 else 0
        if number == 21:
            flash([(0, 0), (.08, peak), (duration, 0)])
        else:
            # Offset makes actual white/black even on black/white input, unlike exposure alone.
            add('exposure', curves={'master/offset': [(0, 0), (duration * .24, 1 if number == 22 else -1), (duration, 0)]})
        notes = 'Single-layer luminance pulse; apply to both overlapped clips for a cut flash.'
    elif number == 24:
        duration = .8
        tr({'scaleHeight': [(0, 180), (.32, 91), (.49, 105), (.64, 98), (.8, 100)], 'opacity': [(0, 0), (.22, 100)]})
    elif number == 25:
        duration = 1.2
        tr({'scaleHeight': [(0, 112), (1.2, 100)], 'opacity': [(0, 0), (.35, 100)]})
        blur([(0, 16), (.6, 0)])
    elif number <= 40:
        duration = {29:.65,30:1.1,38:.4,39:.85,40:.5}.get(number, 4.0)
        if number <= 37:
            amp = {26:.0018,27:.0045,28:.012,29:.018,30:.026,31:.0035,32:.0025,33:.006,34:.007,35:0,36:.0011,37:.009}[number]
            freq = {26:8,27:13,28:19,29:22,30:25,31:1.8,32:.8,33:11,34:9,35:7,36:28,37:.25}[number]
            envelope = f'Math.exp(-t*{6 if number == 29 else 4})' if number in (29,30) else 'Math.sin(Math.PI*t/d)'
            prefix = f'var d={duration}; var t=time-key(1).time; var a=(t>=0&&t<=d)?({envelope}):0; '
            x = f'a*{amp}*(Math.sin(t*{freq}*6.28318)+.35*Math.sin(t*{freq*1.73}*6.28318))' if number != 34 else '0'
            y = f'a*{amp}*(Math.sin(t*{freq*1.19}*6.28318+.7)+.3*Math.sin(t*{freq*2.13}*6.28318))' if number != 33 else '0'
            move([(0,[0,0]),(duration,[0,0])])
            dict(props(fx[-1]))['position']['expr']['text'] = prefix + f'[thisLayer.width/2+thisComp.width*({x}),thisLayer.height/2+thisComp.height*({y})]'
            rotamp = 1.5 if number == 35 else .6 if number in (28,30) else .18
            dict(props(fx[-1]))['rotation']['keys'] = [key(0, {'t':'Scalar','v':0}),key(duration,{'t':'Scalar','v':0})]
            dict(props(fx[-1]))['rotation']['expr'] = {'enabled': True, 'text':prefix + f'a*{rotamp}*Math.sin(t*{freq*.7}*6.28318)'}
            intensity = 'heavy' if number in (28,30) else 'subtle' if number in (26,31,32,36,37) else 'medium'
        elif number == 38:
            tr({'scaleHeight': [(0,100),(.07,115),(.18,97),(.4,100)]})
        elif number == 39:
            move([(0,[0,0]),(.12,[0,-.065]),(.35,[0,.024]),(.55,[0,-.009]),(.85,[0,0])])
        else:
            move([(0,[0,0]),(.05,[-.03,.02]),(.2,[.008,-.006]),(.5,[0,0])])
        notes = 'Finite additive effect-space camera motion; base layer transform is preserved. Scale footage slightly to cover revealed edges.'
    elif number <= 55:
        duration = {41:.6,44:.7,45:2,46:1.4,47:.45,48:.8,49:.5,50:.55,51:3,52:.9,53:.65,54:.65,55:1.1}[number]
        pulse = [(0,0),(duration*.18,100),(duration*.4,25),(duration*.58,75),(duration,0)]
        if number == 44:
            add('chroma', curves={'aberrationRed':[(0,0),(.15,32),(.7,0)],'aberrationBlue':[(0,0),(.18,-26),(.7,0)]})
            glitch(pulse,geom=4,color=24,scan=0)
            notes = 'Real radial RGB aberration using native VR spherical sampling, plus band interference; wrapped edges may appear.'
        elif number == 46:
            add('turb', {'amount':18,'size':70,'displacement':7}, {'amount':[(0,0),(.2,32),(1.4,0)],'evolution':[(0,0),(1.4,450)]})
        elif number == 47:
            tr({'opacity':[(0,100),(.06,15),(.1,100),(.18,35),(.22,100),(.33,50),(.45,100)]})
            glitch(pulse,geom=5,color=15,scan=5,rate=24)
        else:
            geom,color,scan,rate,bands = {
                41:(35,40,12,14,28),45:(8,18,42,30,70),48:(65,12,0,9,90),
                49:(70,22,8,16,12),50:(65,8,6,18,18),51:(12,28,28,6,55),
                52:(90,75,45,24,40),53:(42,35,10,12,24),54:(48,40,14,15,22),
                55:(24,90,20,20,45)}[number]
            g=glitch(pulse,geom,color,scan,rate,bands)
            if number == 50:
                p=dict(props(g));p['geometric/horizontalDisplacement']['value']['v']=0;p['geometric/verticalDisplacement']['value']['v']=100
            if number in (53,54):
                incoming=number==53
                tr({'opacity':[(0,0 if incoming else 100),(duration,100 if incoming else 0)]})
            if number == 51:
                blur([(0,1.5),(1.5,4),(3,1.5)])
                notes='VHS-style band jitter, scanlines and softened image; no authentic tape tracking, audio or PAL/NTSC emulation.'
            if number == 55:
                glow(12,1.3,45,{'intensity':[(0,0),(.2,1.7),(.6,.4),(1.1,0)]})
            if number == 48:
                notes='Native block/band signal displacement; not a spatial mosaic/pixelation filter.'
        notes = notes or 'Native VR Digital Glitch: per-band channel offsets and displacement with horizontal wrap. Not a uniform RGB split.'
    elif number <= 85:
        text = number <= 70
        if number in (56,57):
            duration=.75
            incoming=number==56
            tr({'opacity':[(0,0 if incoming else 100),(.75,100 if incoming else 0)]})
        elif number in (58,59,60,61):
            duration=.55
            xy={58:[0,.12],59:[0,-.12],60:[.16,0],61:[-.16,0]}[number]
            move([(0,xy),(.55,[0,0])])
            dict(props(fx[-1]))['opacity'].update(value={'t':'Scalar','v':0},keys=[key(0,{'t':'Scalar','v':0}),key(.35,{'t':'Scalar','v':100})])
        elif number==70:
            duration=1.15
            tr({'scaleHeight':[(0,106),(1.15,100)],'opacity':[(0,0),(.85,100)]})
            blur([(0,28),(.9,0)])
        else:
            curves={
                62:[(0,0),(.2,108),(.36,100)],63:[(0,100),(.1,112),(.32,0)],
                64:[(0,0),(.22,119),(.4,92),(.57,103),(.72,100)],
                65:[(0,100),(.15,87),(.3,115),(.6,0)],
                66:[(0,0),(.25,126),(.43,87),(.59,106),(.75,98),(.9,100)],
                67:[(0,100),(.16,112),(.3,94),(.42,120),(.72,0)],
                68:[(0,65),(.68,100)],69:[(0,78),(.28,113),(.6,100)],
                71:[(0,0),(.5,100)],72:[(0,100),(.52,0)],73:[(0,0),(.16,100)],74:[(0,100),(.18,0)],
                75:[(0,0),(.2,132),(.36,82),(.51,109),(.67,96),(.82,100)],
                76:[(0,0),(.27,116),(.45,90),(.62,104),(.8,100)],
                77:[(0,100),(.18,85),(.35,110),(.66,0)],
                78:[(0,60),(.3,121),(.7,100)],79:[(0,100),(1.0,125)],80:[(0,100),(1.05,75)],
                81:[(0,70),(.18,125),(.34,85),(.5,109),(.66,95),(.82,102),(1.0,100)],
                82:[(0,100),(.15,72),(.3,120),(.5,93),(.72,100)],
                83:[(0,100),(.08,120),(.2,94),(.4,100)],
                84:[(0,100),(.07,91),(.18,106),(.32,100)],
                85:[(0,35),(.17,138),(.33,76),(.49,116),(.66,94),(.9,100)]}[number]
            duration=curves[-1][0]
            m={'scaleHeight':curves}
            if number in (62,64,66,68,69,71,73,75,76,78,85):
                m['opacity']=[(0,0),(duration*.45,100)]
            if number in (63,65,67,72,74,77):
                m['opacity']=[(0,100),(duration*.6,100),(duration,0)]
            g=tr(m)
            if number==82:
                p=dict(props(g));p['uniform']['value']['v']=False
                p['scaleWidth']['keys']=[key(t,{'t':'Scalar','v':200-v}) for t,v in curves]
            if number==85:
                move([(0,[0,.08]),(.33,[0,-.025]),(.66,[0,.008]),(.9,[0,0])])
        if text:
            notes='Whole text layer animation. Editable text is preserved; no per-character selectors or glyph staggering.'
    elif number <= 90:
        duration={86:.9,87:.95,88:.2,89:.7,90:.75}[number]
        incoming=number in (86,89)
        if number==88:
            blur([(0,0),(.065,45),(.2,0)])
        else:
            amount=48 if number<89 else 90
            blur([(0,amount if incoming else 0),(duration,0 if incoming else amount)])
            if number>=89:
                tr({'opacity':[(0,0 if incoming else 100),(duration,100 if incoming else 0)]})
    elif number <= 94:
        duration={91:1.1,92:.9,93:2.4,94:1.3}[number]
        radius,strength,threshold={91:(22,.65,65),92:(48,2.2,45),93:(30,1.5,55),94:(9,2.8,35)}[number]
        if number==93:
            c={'intensity':[(0,.2),(.6,1.8),(1.2,.2),(1.8,1.8),(2.4,.2)]}
        else:
            c={'intensity':[(0,0),(duration,strength)]}
        glow(radius,strength,threshold,c)
        notes='Glow depends on source color/brightness and alpha; strongest with bright detail on dark backgrounds.'
    elif number <= 98:
        duration={95:.6,96:.28,97:.5,98:1.2}[number]
        points={95:[(0,0),(.15,1.2),(.6,0)],96:[(0,0),(.035,3.5),(.28,0)],97:[(0,0),(.1,2),(.23,-.4),(.5,0)],
                98:[(0,0),(.12,.8),(.2,0),(.34,1.5),(.42,.1),(.65,.7),(.8,0),(.94,1.2),(1.2,0)]}[number]
        flash(points)
    elif number==99:
        duration=1.6
        glow(75,1.1,72,{'intensity':[(0,0),(.8,1.1),(1.6,.7)]})
        flash([(0,0),(.8,.3),(1.6,.12)])
    else:
        duration=2.0
        blur([(0,0),(1,8),(2,5)])
        glow(60,.65,58,{'intensity':[(0,0),(1.2,.65),(2,.45)]})
    if 56 <= number <= 70:
        # Text has comp-sized effect bounds centered on its origin; pivot on the glyph bounds.
        for g in fx:
            if g['kind']['effect'] == SHORT['tr']:
                for path in ('anchor','position'):
                    p=dict(props(g))[path]
                    p['expr']['text']='var r=sourceRectAtTime(time,false); '+p['expr']['text'].replace(
                        'thisLayer.width/2','thisComp.width/2+r.left+r.width/2').replace(
                        'thisLayer.height/2','thisComp.height/2+r.top+r.height/2')
    doc={'effectcraftAnimationPreset':2,'name':f'ECMP {number:03d} - {NAMES[number-1]}','properties':[],'effects':fx}
    cat = 0 if number<=25 else 1 if number<=40 else 2 if number<=55 else 3 if number<=70 else 4 if number<=85 else 5
    return doc, {'id':number,'name':NAMES[number-1],'category':CATEGORIES[cat],
                 'duration':duration,'intensity':intensity,'notes':notes,
                 'effects':[g['kind']['effect'] for g in fx]}


def emit(groups, numbers):
    catalog=[]
    for n in numbers:
        doc,meta=recipe(groups,n)
        if doc is None:
            catalog.append({'id':n,'name':NAMES[n-1],'implemented':False,**meta})
            continue
        rel=Path(meta['category']) / f"{doc['name']}.ecpreset"
        write_json(ROOT/rel,doc)
        catalog.append(dict(meta,path=rel.as_posix(),implemented=True))
    return catalog


if __name__=='__main__':
    groups_path=ROOT/'Documentation/native_effects.json'
    groups=json.loads(groups_path.read_text(encoding='utf-8')) if groups_path.exists() else capture()
    if '--poc' in sys.argv:
        write_json(ROOT/'Tests/poc_catalog.json',emit(groups,[1,26,41,56,91]))
        print('Five proof-of-concept files generated; run validate.py --poc before full build.')
    else:
        gate=ROOT/'Tests/poc_report.json'
        assert gate.exists() and json.loads(gate.read_text())['passed'], 'Proof of concept must pass first'
        write_json(ROOT/'Documentation/catalog.json',emit(groups,range(1,101)))
        print('98 implemented recipes; RGB Split / Heavy explicitly withheld.')
