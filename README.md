<div align="center">

# EffectCraft Motion Pack

**Movimento, impacto e acabamento em 98 presets nativos.**

`EffectCraft 0.21.0` · `Windows` · `Sem plugins externos` · `MIT`

[Baixar o pack](https://github.com/igordemello/EffectCraft-Motion-Pack/releases/latest/download/EffectCraft-Motion-Pack-0.21.0.zip) · [Catálogo completo](Documentation/CATALOG.md) · [Relatório de testes](Documentation/TEST_REPORT.md) · [Especificação técnica](Documentation/TECHNICAL_SPEC.md)

![Elastic Zoom — renderização pelo motor EffectCraft](Previews/024%20-%20Elastic%20Zoom.gif)

*Prévia real do motor CPU do EffectCraft. Os GIFs usam amostras de 320×180 e temporização aproximada.*

</div>

## Instale em três passos

1. **[Baixe o ZIP da release](https://github.com/igordemello/EffectCraft-Motion-Pack/releases/latest/download/EffectCraft-Motion-Pack-0.21.0.zip)** e extraia o arquivo inteiro para uma pasta gravável. Não execute os scripts de dentro do ZIP.
2. **Abra `Install.bat` com dois cliques.** O instalador procura o CLI instalado, confirma a versão **0.21.0** e copia os presets. Não precisa executar como administrador.
3. No EffectCraft, abra **Effects & Presets**, habilite **Animation Presets**, atualize a lista e procure por **`ECMP`**. Se necessário, reinicie o aplicativo.

**Para usar:** selecione uma camada → posicione o cursor de tempo no início da animação → aplique o preset. Ajuste os efeitos e quadros-chave em **Effect Controls**. Para desfazer uma aplicação, use **Undo**.

> **Requisito:** EffectCraft **0.21.0 para Windows**, com `effectcraft-cli.exe` instalado. Python e Pillow são necessários apenas para gerar ou testar o pack; não são necessários para instalar e usar.

## O que vem no pack

| Categoria | Presets | Exemplos |
|---|---:|---|
| Transitions | 25 | Whip Pan, Elastic Zoom, Cinematic Push |
| Camera Shake & Motion | 15 | Impact Shake, Camera Recoil, Handheld |
| Glitch & Distortion | 13 | Digital Glitch, Signal Distortion, Cyberpunk Glitch |
| Text Animations | 15 | Text Bounce In, Text Overshoot, Cinematic Reveal |
| Pop, Bounce & Scale | 15 | Elastic Pop, Rubber Scale, UI Button Pop |
| Blur, Flash & Glow | 15 | Focus Reveal, Glow Pulse, Cinematic Bloom |
| **Total** | **98** | **100 efeitos planejados, com status individual no catálogo** |

Os presets adicionam efeitos nativos e preservam as propriedades de transformação base da camada. Texto continua editável. O pacote inclui arquivos `.ecpreset`, receitas de geração, instalador, desinstalador, relatórios e **98 GIFs**.

### Veja antes de aplicar

| Glitch | Texto | Pop & Bounce |
|:---:|:---:|:---:|
| ![Digital Glitch](Previews/041%20-%20Digital%20Glitch.gif) | ![Text Bounce In](Previews/064%20-%20Text%20Bounce%20In.gif) | ![Dynamic Bounce](Previews/085%20-%20Dynamic%20Bounce.gif) |

Para navegar por todos os efeitos com busca e filtro por categoria, abra **`Previews/index.html` no navegador depois de extrair o ZIP**. O GitHub exibe os GIFs; o catálogo HTML funciona localmente.

## Exemplos de uso

- **Título:** crie uma camada de texto, posicione o cursor e aplique `Text Bounce In`.
- **Corte entre vídeos:** sobreponha as tomadas por aproximadamente 0,6 s e aplique `Smooth Zoom In` à camada que entra.
- **Impacto:** aplique `Impact Shake` no frame do impacto. Aumente um pouco a escala da filmagem se o movimento revelar suas bordas.

As transições atuam em uma camada. Faça a sobreposição e o alinhamento dos clipes na montagem. Flashes podem precisar ser aplicados às duas camadas para cobrir o corte.

## Onde os presets são instalados

O destino segue exatamente a lógica do EffectCraft 0.21.0:

1. Se `EC_PRESETS_DIR` estiver definida, usa esse caminho.
2. Caso contrário, usa `HOME`; se ausente, usa `USERPROFILE`, acrescentando `Documents\EffectCraft\Presets`.

Em uma instalação comum do Windows:

```text
C:\Users\SEU_USUARIO\Documents\EffectCraft\Presets
```

**Atenção ao OneDrive:** o aplicativo usa o nome literal `Documents`. Ele não consulta automaticamente a pasta Documentos redirecionada pelo Windows. O instalador mostra o caminho exato utilizado.

O scanner lê apenas uma pasta, sem subpastas. Por isso, o instalador coloca os arquivos juntos, com categoria e número no nome. Ele recusa sobrescrever qualquer arquivo existente.

<details>
<summary><strong>Instalação personalizada ou manual</strong></summary>

Se o CLI estiver em outro local, abra um terminal na pasta extraída e execute:

```powershell
.\Install.bat -CliPath "D:\Apps\EffectCraft\effectcraft-cli.exe"
```

Para usar outra pasta de presets:

```powershell
.\Install.bat -PresetsDir "D:\Presets"
```

Configure `EC_PRESETS_DIR` com o mesmo caminho no ambiente em que o EffectCraft é iniciado. Informe o mesmo destino na desinstalação.

Para aplicar sem instalar: selecione a camada e o tempo de início, abra **Animation → Apply Animation Preset** e escolha um `.ecpreset` de qualquer categoria do pack.

Para copiar manualmente: coloque os `.ecpreset` diretamente na pasta de presets, sem subpastas e sem substituir arquivos existentes. Essa cópia não cria manifesto de instalação; remova depois somente os arquivos `ECMP 001 - ...` a `ECMP 100 - ...` que você copiou.

</details>

## Desinstalação

Execute **`Uninstall.bat`** na pasta do pack. O script usa o manifesto e os hashes para remover somente os arquivos instalados pelo pacote.

Arquivos que você editou são preservados. Nesse caso, o manifesto fica no local: mova os arquivos personalizados para outra pasta e execute a desinstalação novamente. A pasta de presets e os arquivos de terceiros permanecem.

## O que foi validado

| Verificação | Resultado |
|---|---|
| Estrutura, propriedades, tipos e conteúdo não vazio | **98/98 aprovados** |
| Integração com leitura dos arquivos pelo CLI 0.21.0 | **588 cenários aprovados** |
| Cenários de integração | 1920×1080 e 1080×1920, cada um a 24, 30 e 60 FPS |
| Renderizações CPU para as prévias | **1.274 quadros**, 13 amostras por preset |
| Instalador e desinstalador em pasta temporária | **7 verificações aprovadas** |
| Reprodução na interface desktop / GPU | **Não testada** |

A integração amostrou parâmetros e expressões. Não houve renderização de todos os frames em cada resolução/FPS, teste em filmagem comercial ou certificação de aparência em qualquer material. A instalação real e a biblioteca de presets do usuário não foram alteradas durante os testes.

[Leia o relatório completo](Documentation/TEST_REPORT.md), incluindo os limites da revisão visual de quadros renderizados.

## Ajustes e limites conhecidos

- **98 de 100 planejados:** `RGB Split` e `RGB Split Heavy` ficaram pendentes. Não foi encontrada uma operação nativa validada para deslocamento uniforme de canais 2D. O [catálogo](Documentation/CATALOG.md) registra os dois sem gerar arquivos vazios.
- **Texto:** anima a camada inteira, sem atraso por caractere ou seletores de glifos. O pivô acompanha os limites do texto.
- **Shakes:** têm duração finita. Para retimar, ajuste a chave final e a duração `d` na expressão. Amplitude e frequência também são números na expressão.
- **Slides:** as curvas de posição usam frações da composição. `0.1` corresponde a 10% da largura/altura, convertido pela expressão, embora o controle nativo seja um Point.
- **Glitch e aberração:** usam efeitos VR nativos, com deslocamento por faixas ou projeção esférica e wrap nas bordas. `VHS Distortion` é uma aproximação visual; `Pixel Distortion` desloca blocos/faixas e não aplica mosaico.
- **Blur e glow:** o raio acompanha a largura da composição. A aparência pode variar entre horizontal e vertical; glow depende de detalhes claros no conteúdo.
- **Pilha de efeitos:** efeitos anteriores continuam antes dos novos. Reaplicar um preset adiciona outra pilha. Use uma precomp para tratar vários elementos como uma imagem.
- **Camadas:** use em conteúdo 2D. Comportamento em câmeras, luzes, camadas 3D e camadas de ajuste não foi validado.

## Resolução de problemas

| Problema | O que conferir |
|---|---|
| O pack não aparece | Caminho mostrado pelo instalador, `EC_PRESETS_DIR`, opção **Animation Presets** e atualização da lista. Reinicie o aplicativo se necessário. |
| CLI não encontrado | Confirme a instalação de `effectcraft-cli.exe` ou informe `-CliPath`. |
| Versão recusada | O instalador exige **0.21.0**; outras versões não foram validadas. |
| Arquivo existente ou manifesto detectado | Use `Uninstall.bat` na instalação anterior ou aplique o preset manualmente. Preserve seus arquivos personalizados. |
| Glow quase invisível | Teste em detalhes claros sobre fundo escuro e ajuste threshold/intensidade. |
| Bordas aparecem durante shake/slide | Aumente a escala do conteúdo ou trabalhe em uma precomp com margem. |

## Fontes e testes

As receitas e os scripts estão em [`Tests/`](Tests/). As instâncias exportadas pelo motor estão em [`Documentation/native_effects.json`](Documentation/native_effects.json), e os detalhes do formato em [`TECHNICAL_SPEC.md`](Documentation/TECHNICAL_SPEC.md).

Para reproduzir a geração, use Python 3.10+, Pillow e o CLI 0.21.0. Defina `EFFECTCRAFT_CLI` se o executável estiver fora dos locais padrão.

```powershell
python -m pip install Pillow
python Tests/build.py --poc
python Tests/validate.py --poc
python Tests/build.py
python Tests/validate.py
python Tests/test_installer.py
python Tests/package.py
```

Esses comandos regravam os arquivos e as prévias do próprio pack. Use uma cópia se tiver personalizado o conteúdo. Os testes do instalador usam uma pasta temporária; o empacotador exclui `.git`, caches e dados de execução.

## Licença e créditos

Receitas e scripts originais sob [MIT](LICENSE.txt). Os metadados nativos derivam do [EffectCraft](https://github.com/storytold/effectcraft), versão 0.21.0, commit `7870b5916ae0749d497d880989683bf2946d6c8b`. Licenças e avisos do upstream estão em [`Documentation/`](Documentation/).

Veja a [atribuição dos arquivos](Documentation/ATTRIBUTION.md). Nenhum preset proprietário foi copiado. Este é um pacote independente, sem vínculo ou endosso do projeto EffectCraft.
