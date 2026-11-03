# Relatório de validação

Escopo: receitas `.ecpreset` da versão 1. Para a extensão v2, veja [integração do painel](../Plugin/Tests/integration_report.json) e [teste desktop/GPU](../Plugin/Tests/desktop_report.json).

Data: 2026-11-03. EffectCraft CLI 0.21.0, Windows, motor CPU/headless.
Commit de referência: `7870b5916ae0749d497d880989683bf2946d6c8b`.

- Estrutura: **98/98 aprovados**; tipos e nomes conferidos contra instâncias exportadas pelo motor, tempos em ticks, curvas não vazias, IDs nativos e diretórios completos. Zero duplicatas de conteúdo após ignorar UIDs.
- Autoteste do validador: rejeitou efeito desconhecido, propriedade inexistente, tipo incompatível e animação vazia.
- Integração: **588 cenários aprovados** — 98 presets × 1920×1080/1080×1920 × 24/30/60 FPS. Cada aplicação leu o arquivo `.ecpreset`, retornou zero caminhos ignorados e preservou posição, escala, rotação e opacidade base da camada.
- Avaliação: propriedades animadas e expressões amostradas no início, 23%, 57%, fim e após o fim; ausência de erros de expressão e de números não finitos. CTI de 0,5 s confirmado como início.
- Render: **1274 quadros** 320×180, 30 FPS na composição, amostrados ao longo das durações; todos os 98 exibiram alteração entre amostras. GIFs usam temporização aproximada. Isso não é uma renderização de todos os frames em cada resolução/FPS.
- Prova de conceito anterior à produção: cinco categorias aprovadas, `Tests/poc_report.json` e `Previews/poc-contact-sheet.png`.
- Instalação: **7 verificações aprovadas** em pasta temporária, sem alterar a instalação nem a biblioteca real do usuário.
- Revisão visual de quadros renderizados: 98 presets revisados em folhas de contato com amostras a 25% e 58% da duração; POC também em 0%, 25%, 58% e 100%. Texto reposicionado na cena de teste e pivot alinhado ao conteúdo; 15 presets de texto revalidados em seis cenários. Revisão de imagens do motor, sem reprodução na UI..
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
