# Especificação técnica — EffectCraft Motion Pack

Este documento descreve o núcleo de receitas da versão 1. O painel nativo e as precomps da versão 2 estão documentados em [Plugin/README.md](../Plugin/README.md), com relatórios próprios de ScriptUI e da interface desktop.

## Escopo

O pacote contém 100 entradas planejadas no catálogo: 98 presets implementados e dois RGB Split uniformes deliberadamente não gerados. A implementação usa exclusivamente efeitos e propriedades nativos presentes no EffectCraft 0.21.0. O formato é o resultado serializado de `anim.savePreset`, não um formato inferido a partir de presets internos.

## Formato e compatibilidade

Cada `.ecpreset` tem `effectcraftAnimationPreset: 2`, `properties` e `effects`. Os grupos de efeitos e propriedades foram capturados pelo CLI instalado e exportados no formato v2. Quadros-chave armazenam tempo e valor tipados; expressões são usadas onde a animação precisa acompanhar a composição ou preservar uma transformação da camada.

O pacote foi construído contra o upstream oficial [storytold/effectcraft](https://github.com/storytold/effectcraft/tree/7870b5916ae0749d497d880989683bf2946d6c8b), versão 0.21.0, commit `7870b5916ae0749d497d880989683bf2946d6c8b`.

Referências de implementação no commit fixado:

- [animation.rs — versão do preset, save e apply](https://github.com/storytold/effectcraft/blob/7870b5916ae0749d497d880989683bf2946d6c8b/crates/engine/src/cmd/animation.rs#L18-L250): v2 na linha 18, save na 63 e aplicação nas linhas 135–250.
- [keyframe/lib.rs](https://github.com/storytold/effectcraft/blob/7870b5916ae0749d497d880989683bf2946d6c8b/crates/keyframe/src/lib.rs#L24-L61): interpolação e representação de quadros-chave.
- [time/lib.rs](https://github.com/storytold/effectcraft/blob/7870b5916ae0749d497d880989683bf2946d6c8b/crates/time/src/lib.rs#L17): 254.016.000.000 ticks por segundo.
- [props.rs](https://github.com/storytold/effectcraft/blob/7870b5916ae0749d497d880989683bf2946d6c8b/crates/project/src/props.rs#L52-L273): expressões, `PropGroup` e `Node`.

Os JSONs internos em `crates/engine/presets/{transitions,backgrounds,behaviors}.json` usam abreviações internas diferentes do arquivo importável. `anim.applyBuiltinPreset` constrói instâncias nativas; os arquivos internos não são um esquema de `.ecpreset`.

## Efeitos nativos usados

- Desfoque gaussiano e direcional: [misc.rs](https://github.com/storytold/effectcraft/blob/7870b5916ae0749d497d880989683bf2946d6c8b/crates/effects/src/misc.rs#L688-L743).
- Exposição: [color_fx.rs](https://github.com/storytold/effectcraft/blob/7870b5916ae0749d497d880989683bf2946d6c8b/crates/effects/src/color_fx.rs#L1036).
- Transformação: [distort.rs](https://github.com/storytold/effectcraft/blob/7870b5916ae0749d497d880989683bf2946d6c8b/crates/effects/src/distort.rs#L491).
- Turbulência: [distort2.rs](https://github.com/storytold/effectcraft/blob/7870b5916ae0749d497d880989683bf2946d6c8b/crates/effects/src/distort2.rs#L735).
- Aberração cromática e glitch VR: [vr.rs](https://github.com/storytold/effectcraft/blob/7870b5916ae0749d497d880989683bf2946d6c8b/crates/effects/src/vr.rs#L996-L1038).

A transformação nativa `ec.distort.transform` mantém os transforms base da camada; centro/posição usam expressões cientes da resolução. As duas operações VR têm semântica específica: a aberração cromática usa projeção esférica radial, e o glitch desloca canais em faixas aleatórias com wrap horizontal. As descrições “VHS-style” são aproximações visuais: não há emulação de tracking de fita, áudio ou PAL/NTSC. “Pixel Distortion” é deslocamento em blocos/faixas, não pixelização em mosaico.

Propriedades animadas pelo pack (nomes relativos ao grupo do efeito):

| Efeito | Propriedades | Tipo / unidade |
|---|---|---|
| Transform | `position`, `anchor` | Vec2, pixels no espaço do efeito; as curvas de posição do pack são convertidas por expressão de frações da composição |
| Transform | `scaleHeight`, `scaleWidth`, `opacity` | Scalar, porcentagem; `uniform` seleciona escala uniforme |
| Transform | `rotation` | Scalar, graus |
| Gaussian Blur | `blurriness` | Scalar, pixels, convertido proporcionalmente à largura da composição |
| Directional Blur | `length`, `direction` | Scalar, pixels e graus |
| Glow | `radius`, `intensity` | Scalar, pixels e multiplicador; `threshold` controla a seleção de brilho |
| Exposure | `master/exposure`, `master/offset` | Scalar, stops e offset linear |
| Turbulent Displace | `amount`, `evolution` | Scalar, pixels e graus |
| Digital Glitch | `masterAmplitude` | Scalar, porcentagem; demais parâmetros definem faixas, taxa e distorção |
| Chromatic Aberrations | `aberrationRed`, `aberrationBlue` | Scalar, amplitude nativa da aberração VR |

`Documentation/native_effects.json` registra todas as propriedades, tipos, defaults e controles das oito instâncias nativas. Valores são serializados como `{"t":"Scalar","v":100}` ou `{"t":"Vec2","v":[0,0]}`. Grupos usam `kind: {kind: "Effect", effect: "ec.distort.transform"}`; filhos distinguem `node: "Prop"` e `node: "Group"`. Cada keyframe contém `time` inteiro em ticks, `value` tipado e interpoladores `Linear`, `Bezier` ou `Hold`. As curvas numéricas usam Bezier, velocidade zero e influência de 1/3 por dimensão; as oscilações de câmera usam expressões contínuas em segundos.

O loader desloca os keyframes pelo tempo local da camada na posição do CTI e reatribui os UIDs dos efeitos. Ele pode ignorar silenciosamente uma propriedade incompatível; por isso os testes exigem `skipped: []` e conferem a quantidade de efeitos adicionados. Aplicar um preset adiciona efeitos, sem fundir com efeitos anteriores. Propriedades antes/depois das chaves seguem o comportamento nativo de manter o primeiro/último valor; reveals ficam ocultos antes da entrada e exits ficam ocultos depois da saída. Shakes têm janela finita explícita na expressão.

Em texto, o pivot usa `sourceRectAtTime()` somado à origem do espaço de efeitos, centrado na composição. O renderer define esse espaço para texto/shapes em [eval.rs:368](https://github.com/storytold/effectcraft/blob/7870b5916ae0749d497d880989683bf2946d6c8b/crates/render/src/eval.rs#L368). O texto permanece editável e o pivot acompanha seus limites.

Não foi verificada uma API de plugin nativo que implemente separação RGB uniforme. Os presets RGB Split e Heavy (IDs 42 e 43) foram retidos; não se simula essa operação com o efeito VR.

## Conteúdo e autoria

`Documentation/catalog.json` é o inventário legível por máquina dos 100 IDs, com nome, categoria, duração, intensidade, efeitos, notas e caminho. `Documentation/CATALOG.md` é a apresentação do catálogo. Os arquivos gerados ficam em seis pastas numeradas; essas categorias organizam o pacote, mas o scanner nativo procura arquivos somente no diretório plano de presets, sem subdiretórios.

`Tests/build.py` gera receitas a partir dos grupos nativos capturados; primeiro executa-se a prova de conceito de cinco presets e sua validação. Após aprovação, a geração completa grava 98 arquivos e mantém os dois não implementados explicitamente no catálogo.

## Aplicação e comportamento

Aplicar exige uma camada selecionada e CTI posicionado. O comando de aplicação associa a animação à camada; não edita a montagem para criar sobreposição. Transições que dependem de duas tomadas exigem sobreposição manual, alinhamento e, quando aplicável, aplicação do efeito às duas camadas.

Animações de texto atuam na camada inteira. O texto segue editável, mas não há selectors por caractere nem atraso por glifo. Shake é movimento finito aditivo no espaço do efeito; pode mostrar bordas vazias do conteúdo. Para mudar o tempo de shake, alterar apenas os quadros finais não basta: a expressão contém duração `d` (4 s em vários shakes, ou duração específica nos impactos), e o valor deve acompanhar os novos quadros.

## Instalação

`Install.bat` e `Uninstall.bat` chamam `Scripts/Manage-Pack.ps1`. O instalador consulta a versão real com `--version`, copia exclusivamente os arquivos do pacote e mantém um manifesto de hashes para gestão da cópia. A pasta de destino é `EC_PRESETS_DIR`, se definida; caso contrário é `$HOME`, ou `$USERPROFILE` quando `HOME` não existe, seguido do caminho literal `Documents/EffectCraft/Presets`. Não usa a Known Folder do Windows para Documentos e, portanto, não resolve por conta própria o redirecionamento para OneDrive. A instalação não foi executada numa conta real de usuário.

## Verificação e limites

`python Tests/validate.py` requer Python 3.10+, Pillow e CLI instalado. O caminho do CLI pode ser informado em `EFFECTCRAFT_CLI`; sem isso, o verificador procura os locais padrão de instalação por usuário e para todos os usuários.

O relatório `Tests/compatibility_report.json` registra sucesso com EffectCraft 0.21.0 no renderizador CPU/headless: os 98 presets passaram por integração do mecanismo em seis cenários (1920×1080 e 1080×1920, cada um a 24/30/60 fps). Foram amostrados parâmetros, não a reprodução completa; 13 quadros 320×180 por preset foram renderizados e usados nos GIFs de `Previews/`. A prova de conceito de cinco presets passou antes da geração em massa.

Não foram testados: reprodução visual na interface desktop, GPU, filmagem comercial, nem todos os quadros em todas as taxas. Os GIFs e a integração headless não certificam resultado visual em material ou hardware de produção.

## Recursos que exigem desenvolvimento adicional

O pack não exige plugins. Separação uniforme de canais em 2D precisa de uma composição com cópias/canais ou de um efeito adicional, e não foi encapsulada como um preset nativo verificado. Não foi criada uma extensão nem modificado o aplicativo. Uma futura implementação deve primeiro verificar o mecanismo oficial de distribuição de efeitos, ou propor a alteração ao upstream com autorização.

Subpastas e thumbnails dentro do navegador padrão Effects & Presets exigiriam alterar seu scanner/UI: [effects_presets.rs:30–49](https://github.com/storytold/effectcraft/blob/7870b5916ae0749d497d880989683bf2946d6c8b/crates/ui-egui/src/panels/effects_presets.rs#L30-L49). A versão 2 cria um navegador separado por ScriptUI, com sequência PNG, duração, intensidade e inserção de precomps, sem modificar esse scanner nem o binário. Transições com montagem automática, texto por caractere e um ensaio completo de render/GPU em vídeos reais continuam fora do escopo.
