"""Package only an extension build matching its passing native and desktop tests."""
import ast
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote
import zipfile

from ec import ROOT


def main():
    manifest=json.loads((ROOT/'Plugin/manifest.json').read_text(encoding='utf-8'))
    source_hash=manifest['files']['IGPACK Motion Browser.jsx']
    for filename in ('integration_report.json','desktop_report.json'):
        report=json.loads((ROOT/'Plugin/Tests'/filename).read_text(encoding='utf-8'))
        assert report['passed'] and report['source_sha256']==source_hash,filename+' must pass for current build'
    assert len(manifest['files'])==1275
    for rel,digest in manifest['files'].items():
        assert hashlib.sha256((ROOT/'Plugin'/rel).read_bytes()).hexdigest()==digest,rel
    for source in (ROOT/'Tests').glob('*.py'):ast.parse(source.read_text(encoding='utf-8'),filename=str(source))
    for readme in (ROOT/'README.md',ROOT/'Plugin/README.md'):
        for target in re.findall(r'\]\(([^)]+)\)',readme.read_text(encoding='utf-8')):
            if not target.startswith(('http://','https://','#')):
                assert (readme.parent/unquote(target)).exists(),target
    files=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and not {'.git','.runtime','__pycache__'}.intersection(p.parts)]
    archive=ROOT.parent/'IGPACK-Motion-Browser-2.0.0-EffectCraft-0.21.0.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in files:z.write(path,Path(ROOT.name)/path.relative_to(ROOT))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert not any({'.git','.runtime','__pycache__'}.intersection(Path(n).parts) for n in z.namelist())
        assert z.read(ROOT.name+'/Install.bat').find(b'Manage-Plugin.ps1')>=0
        assert z.read(ROOT.name+'/Plugin/IGPACK Motion Browser.jsx')==(ROOT/'Plugin/IGPACK Motion Browser.jsx').read_bytes()
        assert len([n for n in z.namelist() if '/Plugin/Frames/' in n and n.endswith('.png')])==1274
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n')
    print(f'PASS native plugin package: {archive.name}; {archive.stat().st_size:,} bytes; {len(files)} files')


if __name__=='__main__':main()
