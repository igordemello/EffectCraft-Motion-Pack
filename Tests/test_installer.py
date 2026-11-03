"""Run the real installer only in a temporary workspace-owned directory."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from ec import ROOT, find_cli
from build import write_json


def run(mode, target, cli=None):
    result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
                           str(ROOT/'Scripts/Manage-Pack.ps1'),'-Mode',mode,
                           '-PresetsDir',str(target),'-CliPath',cli or find_cli()],
                          capture_output=True,text=True,errors='replace')
    return result


def main():
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in ROOT.glob('*/*.ecpreset')}
    assert len(hashes)==98
    write_json(ROOT/'Documentation/preset_hashes.json',hashes)
    checks=[]
    (ROOT/'Tests/.runtime').mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='installer-',dir=ROOT/'Tests/.runtime') as folder:
        target=Path(folder)/'Presets'
        target.mkdir()
        unrelated=target/'user.ecpreset'
        unrelated.write_text('existing user data')
        receipt=target/'.effectcraft-motion-pack-1.0.json'
        result=run('Install',target)
        assert result.returncode==0,result.stderr
        files=[p for p in target.glob('ECMP *.ecpreset')]
        assert len(files)==98 and receipt.exists()
        checks.append('98 files installed to isolated target, user file preserved')
        result=run('Install',target)
        assert result.returncode!=0 and len(list(target.glob('ECMP *.ecpreset')))==98
        checks.append('repeat install refused without overwriting')
        modified=files[0]
        modified.write_text('user customization')
        result=run('Uninstall',target)
        assert result.returncode!=0 and modified.read_text()=='user customization'
        assert receipt.exists() and len(list(target.glob('ECMP *.ecpreset')))==1
        assert unrelated.read_text()=='existing user data'
        checks.append('uninstall removed 97 originals and preserved edited preset and unrelated file')
        modified.unlink()
        result=run('Uninstall',target)
        assert result.returncode==0 and not receipt.exists() and unrelated.exists(),result.stderr
        checks.append('uninstall completed after modified file moved away')
        collision=files[1]
        collision.write_text('existing content')
        result=run('Install',target)
        assert result.returncode!=0 and collision.read_text()=='existing content'
        assert len(list(target.glob('ECMP *.ecpreset')))==1 and not receipt.exists()
        checks.append('filename collision detected before copying any preset')
        collision.unlink()
        fake=Path(folder)/'wrong-version.cmd'
        fake.write_text('@echo off\necho effectcraft-cli 0.22.0\n')
        result=run('Install',target,str(fake))
        assert result.returncode!=0 and not receipt.exists()
        checks.append('incompatible CLI version refused before copying')
        # A receipt cannot be used to remove an arbitrary relative path.
        write_json(receipt,{'pack':'EffectCraft Motion Pack 1.0','target':str(target),
                            'files':[{'name':'../user.ecpreset','sha256':'0'*64}]})
        result=run('Uninstall',target)
        assert result.returncode!=0 and unrelated.exists()
        checks.append('unsafe receipt path rejected before removal')
    write_json(ROOT/'Tests/installer_report.json',{'passed':True,'production_installation_modified':False,'checks':checks})
    print('\n'.join('PASS '+check for check in checks))


if __name__=='__main__':main()
