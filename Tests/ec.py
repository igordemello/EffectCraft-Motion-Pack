"""Small stdio client for the installed EffectCraft 0.21.0 engine."""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def find_cli():
    candidates = [os.environ.get('EFFECTCRAFT_CLI', '')]
    for base in ('LOCALAPPDATA', 'ProgramFiles', 'ProgramFiles(x86)'):
        folder = Path(os.environ.get(base, '.'))
        if base == 'LOCALAPPDATA':
            folder /= 'Programs'
        candidates.append(str(folder / 'ArtCraft/EffectCraft/effectcraft-cli.exe'))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            version = subprocess.check_output([candidate, '--version'], text=True).strip()
            if version != 'effectcraft-cli 0.21.0':
                raise RuntimeError(f'Expected 0.21.0, found {version}')
            return candidate
    raise FileNotFoundError('Set EFFECTCRAFT_CLI to effectcraft-cli.exe 0.21.0')


class Engine:
    def __init__(self):
        env = dict(os.environ)
        env['EFFECTCRAFT_CONFIG_DIR'] = str(ROOT / 'Tests/.runtime')
        Path(env['EFFECTCRAFT_CONFIG_DIR']).mkdir(parents=True, exist_ok=True)
        self.process = subprocess.Popen([find_cli(), 'mcp'], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                        text=True, encoding='utf-8', env=env)
        self.serial = 0
        self.rpc('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {},
                               'clientInfo': {'name': 'effectcraft-motion-pack', 'version': '1.0'}})

    def rpc(self, method, params):
        self.serial += 1
        self.process.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': self.serial,
                                            'method': method, 'params': params}) + '\n')
        self.process.stdin.flush()
        reply = json.loads(self.process.stdout.readline())
        if 'error' in reply:
            raise RuntimeError(reply['error'])
        return reply['result']

    def tool(self, name, args):
        result = self.rpc('tools/call', {'name': name, 'arguments': args})
        if result.get('isError'):
            raise RuntimeError(result['content'])
        texts = [c['text'] for c in result['content'] if c['type'] == 'text']
        return json.loads(texts[0]) if texts else result

    def cmd(self, command, **params):
        return self.tool('execute_command', {'command': command, 'params': params})

    def close(self):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=10)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


if __name__ == '__main__':
    with Engine() as engine:
        print(json.dumps(engine.cmd('app.capabilities')))
