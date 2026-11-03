"""Build the offline catalogue, traceable report and ZIP from passing test outputs."""
import hashlib
import html
import json
from pathlib import Path
import shutil
import zipfile

from build import CATEGORIES, write_json
from ec import ROOT


def main():
    catalog=json.loads((ROOT/'Documentation/catalog.json').read_text(encoding='utf-8'))
    report=json.loads((ROOT/'Tests/compatibility_report.json').read_text(encoding='utf-8'))
    installer=json.loads((ROOT/'Tests/installer_report.json').read_text(encoding='utf-8'))
    assert report['passed'] and installer['passed'] and report['loaded_from_files']
    assert len(report['results'])==98 and sum(len(r['matrix']) for r in report['results'])==588
    assert all(len(list(ROOT.glob(f"{c}/*.ecpreset")))==n for c,n in zip(CATEGORIES,[25,15,13,15,15,15]))
    results={r['id']:r for r in report['results']}
    review_path=ROOT/'Tests/visual_review.json'
    reviews=json.loads(review_path.read_text(encoding='utf-8')) if review_path.exists() else {}
    lines=['# Catálogo — 100 efeitos planejados', '',
           '98 arquivos implementados. “Render” indica 13 quadros pelo motor CPU; “UI” indica reprodução visual no aplicativo.', '',
           '| ID | Efeito | Categoria | Duração | Estrutura | Integração | Render | UI |',
           '|---:|---|---|---:|---|---|---|---|']
    cards=[]
    for m in catalog:
        n=m['id']
        if not m['implemented']:
            lines.append(f"| {n} | {m['name']} | Glitch | — | Não gerado | Não testado | Não testado | Não testado |")
            cards.append(f'<article data-category="03_Glitch_Distortion"><h2>{n:03d} · {html.escape(m["name"])}</h2><p class="pending">Não implementado</p><p>{html.escape(m["reason"])}</p></article>')
            continue
        r=results[n]
        assert r['structural'] and r['engine_integration'] and r['rendered_cpu']['changed']
        lines.append(f"| {n} | {m['name']} | {m['category']} | {m['duration']:g} s | Validado | 6 cenários | 13 quadros | Não testado |")
        gif=Path(r['rendered_cpu']['gif']).name
        cards.append(f'''<article data-category="{m['category']}">
<img loading="lazy" src="{html.escape(gif,quote=True)}" alt="{html.escape(m['name'],quote=True)} — quadros reais do motor EffectCraft CPU">
<h2>{n:03d} · {html.escape(m['name'])}</h2><p class="meta">{m['category']} · {m['duration']:g} s · intensidade {m['intensity']}</p>
<p>{html.escape(m['notes']) or 'Curva original com interpolação Bezier.'}</p>
<a href="../{html.escape(m['path'],quote=True)}">Arquivo .ecpreset</a></article>''')
    lines.extend(['','## Limitações por efeito',''])
    for m in catalog:
        note=m.get('notes') or m.get('reason')
        if note:lines.append(f"- **{m['id']:03d} — {m['name']}:** {note}")
    (ROOT/'Documentation/CATALOG.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EffectCraft Motion Pack — prévias</title>
<style>*{box-sizing:border-box}body{margin:0;background:#0b1120;color:#e8effa;font:16px system-ui,sans-serif}header,main{max-width:1440px;margin:auto;padding:28px}header p{max-width:920px;line-height:1.6;color:#b9c8dc}h1{font-size:32px;margin:0 0 12px}label{display:block;margin:12px 0 5px}input,select{font:inherit;color:inherit;background:#19253a;border:1px solid #7e94b5;border-radius:6px;padding:10px;width:min(100%,460px);margin-right:12px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:20px;padding-top:0}article{background:#142035;border:1px solid #30415d;border-radius:10px;overflow:hidden;padding-bottom:20px}article img{width:100%;display:block}article h2{font-size:18px;margin:16px}article p,article a{margin:12px 16px;font-size:14px;line-height:1.55}a{color:#81d9ff}.meta{color:#b3c5df}.pending{color:#ffd27a}article[hidden]{display:none}</style>
<header><h1>EffectCraft Motion Pack</h1><p>98 presets nativos para 0.21.0. Prévias geradas pelo próprio motor CPU em 320×180: 13 amostras por animação, duração aproximada no GIF. O texto permanece editável nos presets de texto. Integração de parâmetros validada em horizontal/vertical a 24/30/60 FPS; reprodução na interface e GPU não testadas.</p>
<label for="search">Buscar efeito</label><input id="search" type="search" placeholder="Zoom, bounce, shake…"><label for="category">Categoria</label><select id="category"><option value="">Todas</option>'''
    page+=''.join(f'<option value="{c}">{c}</option>' for c in CATEGORIES)
    page+='</select><p id="count" role="status">100 entradas · 98 implementadas · 2 pendentes</p></header><main>'+''.join(cards)+'</main>'
    page+='''<script>const search=document.querySelector('#search'),category=document.querySelector('#category');function filter(){let count=0;for(const card of document.querySelectorAll('article')){card.hidden=!(card.textContent.toLowerCase().includes(search.value.toLowerCase())&&(!category.value||card.dataset.category===category.value));if(!card.hidden)count++}document.querySelector('#count').textContent=count+' entradas encontradas'}search.addEventListener('input',filter);category.addEventListener('change',filter);</script></html>'''
    (ROOT/'Previews/index.html').write_text(page,encoding='utf-8')

    from PIL import Image,ImageDraw
    for cat in CATEGORIES:
        entries=[m for m in catalog if m.get('category')==cat and m['implemented']]
        sheet=Image.new('RGB',(1280,((len(entries)+3)//4)*120),'#101827')
        draw=ImageDraw.Draw(sheet)
        for index,m in enumerate(entries):
            x=(index%4)*320;y=(index//4)*120
            for col,k in enumerate((3,7)):
                im=Image.open(ROOT/'Previews'/f"{m['id']:03d}"/f'{k:02d}.png').convert('RGB').resize((160,90))
                sheet.paste(im,(x+col*160,y))
            draw.text((x+5,y+94),f"{m['id']:03d} {m['name']}",fill='white')
        sheet.save(ROOT/'Previews'/f'{cat}-contact-sheet.png')
    poc_sheet=Image.new('RGB',(1280,1050),'#101827')
    for row,n in enumerate((1,26,41,56,91)):
        for col,k in enumerate((0,3,7,12)):
            im=Image.open(ROOT/'Previews'/f'{n:03d}'/f'{k:02d}.png').convert('RGB')
            poc_sheet.paste(im,(col*320,row*210))
            ImageDraw.Draw(poc_sheet).text((col*320+8,row*210+183),f'Preset {n:03d}, frame {k:02d}',fill='white')
    poc_sheet.save(ROOT/'Previews/poc-contact-sheet.png')

    matrix_count=sum(len(r['matrix']) for r in report['results'])
    body=f'''# Relatório de validação

Data: 2026-11-03. EffectCraft CLI 0.21.0, Windows, motor CPU/headless.
Commit de referência: `7870b5916ae0749d497d880989683bf2946d6c8b`.

- Estrutura: **98/98 aprovados**; tipos e nomes conferidos contra instâncias exportadas pelo motor, tempos em ticks, curvas não vazias, IDs nativos e diretórios completos. Zero duplicatas de conteúdo após ignorar UIDs.
- Autoteste do validador: rejeitou efeito desconhecido, propriedade inexistente, tipo incompatível e animação vazia.
- Integração: **{matrix_count} cenários aprovados** — 98 presets × 1920×1080/1080×1920 × 24/30/60 FPS. Cada aplicação leu o arquivo `.ecpreset`, retornou zero caminhos ignorados e preservou posição, escala, rotação e opacidade base da camada.
- Avaliação: propriedades animadas e expressões amostradas no início, 23%, 57%, fim e após o fim; ausência de erros de expressão e de números não finitos. CTI de 0,5 s confirmado como início.
- Render: **{len(results)*13} quadros** 320×180, 30 FPS na composição, amostrados ao longo das durações; todos os 98 exibiram alteração entre amostras. GIFs usam temporização aproximada. Isso não é uma renderização de todos os frames em cada resolução/FPS.
- Prova de conceito anterior à produção: cinco categorias aprovadas, `Tests/poc_report.json` e `Previews/poc-contact-sheet.png`.
- Instalação: **{len(installer['checks'])} verificações aprovadas** em pasta temporária, sem alterar a instalação nem a biblioteca real do usuário.
- Revisão visual de quadros renderizados: {reviews.get('summary','pendente; consulte visual_review.json quando disponível')}.
- Reprodução visual na interface do aplicativo: **não testada**.
- GPU, clipes de produção, comportamento 3D/ajuste, todas as imagens possíveis e certificação comercial: **não testados**.

Os IDs 42 e 43 não geraram arquivos. O efeito RGB uniforme não foi substituído por deslocamento de posição ou por aberração VR.
VHS e Pixel Distortion são aproximações nativas explicitadas no catálogo; não são emulação de fita ou mosaico.
Comparação perceptiva por pares entre todos os presets não foi automatizada; curvas, durações e mecanismos diferentes não garantem distinção em qualquer conteúdo.

## Reproduzir

Instale Python 3.10+ e Pillow (`python -m pip install Pillow`), use o CLI 0.21.0 e execute na pasta do pack:

```text
python Tests/build.py --poc
python Tests/validate.py --poc
python Tests/build.py
python Tests/validate.py
python Tests/test_installer.py
python Tests/package.py
```

O gerador reutiliza `Documentation/native_effects.json`, exportado do motor. Se esse arquivo faltar, ele captura novamente as instâncias com o comando nativo `anim.savePreset`. O teste do instalador escreve apenas em diretório temporário sob `Tests/.runtime`.
As etapas de geração/revalidação regravam os arquivos do próprio pack e as prévias; execute em uma cópia se você os personalizou.
Os resultados detalhados ficam em `Tests/compatibility_report.json` e `Tests/installer_report.json`.
'''
    (ROOT/'Documentation/TEST_REPORT.md').write_text(body,encoding='utf-8')
    upstream=ROOT.parent/'upstream/effectcraft-0.21.0'
    if upstream.exists():
        for filename in ('LICENSE-MIT','LICENSE-APACHE','NOTICE'):
            shutil.copyfile(upstream/filename,ROOT/'Documentation'/f'UPSTREAM-{filename}.txt')
    hashes=json.loads((ROOT/'Documentation/preset_hashes.json').read_text())
    for rel,digest in hashes.items():
        assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest
    files=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and not {'.git','.runtime','__pycache__'}.intersection(p.parts)]
    assert len([p for p in files if p.suffix=='.ecpreset'])==98
    archive=ROOT.parent/'EffectCraft-Motion-Pack-0.21.0.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in files:z.write(path,Path(ROOT.name)/path.relative_to(ROOT))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len([n for n in z.namelist() if n.endswith('.ecpreset')])==98
        assert all('.git' not in Path(n).parts for n in z.namelist())
        assert all('..' not in Path(n).parts and not Path(n).is_absolute() for n in z.namelist())
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    (archive.with_suffix('.zip.sha256')).write_text(f'{digest}  {archive.name}\n')
    print(f'ZIP verified: {archive.name}; {archive.stat().st_size:,} bytes; 98 presets, 98 GIFs')


if __name__=='__main__':main()
