# IGPACK Motion Browser

Painel nativo para navegar e aplicar 98 animações no EffectCraft 0.21.0. Cada item tem uma prévia animada, controles de duração e intensidade e pode ser inserido como clipe de efeito ou aplicado a uma seleção precomposta.

## Instalar e abrir

No Windows, execute `Install.bat` na pasta do pacote. O instalador verifica o CLI do EffectCraft 0.21.0, copia o painel e os quadros de prévia sem sobrescrever arquivos existentes e grava um recibo com hashes. Reinicie o EffectCraft se necessário; abra em **Window/Janela > IGPACK > Motion Browser**. O painel encaixa como ScriptUI e reorganiza filtros, lista e prévia em coluna quando o dock fica estreito.

O destino de configuração é, nesta ordem: `EFFECTCRAFT_CONFIG_DIR`, diretório portátil indicado por `portable.txt` ou `EffectCraft.portable` ao lado do CLI (pasta `EffectCraftData`), ou `%APPDATA%\EffectCraft`. O painel fica em `Scripts/ScriptUI Panels/IGPACK/`; as imagens ficam em `IGPACK Motion Browser/Frames/`.

Para remover, execute `Uninstall.bat`. Arquivos modificados e scripts alheios são preservados; se houver arquivos alterados, o desinstalador informa que ficaram e mantém o recibo para nova tentativa. O formato legado de presets continua disponível em `Install-Presets.bat` e `Uninstall-Presets.bat`. Uma instalação v1 existente não impede o painel e não precisa ser removida.

## Usar

1. Abra uma composição e pesquise por nome ou filtre por categoria.
2. Selecione um item para ver a prévia original. Ajuste **Duração (s)** e **Intensidade (%)** se desejar.
3. Escolha o modo e clique **Adicionar à timeline** no CTI atual.

A duração é limitada a 1 quadro–30 s, ajustada à grade de quadros da composição e precisa caber depois do CTI. A intensidade aceita 0–200%; ela escala os parâmetros animados, mas preserva opacidade/fades para manter as entradas e saídas. O painel agrupa a operação em um undo; se a aplicação falhar parcialmente, desfaz as alterações feitas.

### Sobrepor à imagem (precomp de ajuste)

Cria uma precomp de cobertura branca com a duração escolhida, aplica os efeitos à camada externa e ativa o modo adjustment na camada externa. O conteúdo da precomp funciona como máscara alfa branca, então o efeito afeta a composição abaixo apenas durante o intervalo do clipe. O novo clipe é colocado no topo da composição; mova-o na timeline para reposicionar, ou duplique/remova como qualquer clipe. Abra a precomp para inspecionar sua cobertura. Os parâmetros ficam nos efeitos da camada externa.

### Animar seleção (nova precomp)

Precompõe as camadas selecionadas e aplica os efeitos à nova precomp. O painel calcula o pivô pelo conteúdo visível usando `sourceRectAtTime` e `sourcePointToComp`. A seleção deve conter camadas AV 2D desbloqueadas. Conexões de parenting ou track matte devem estar incluídas por completo; se houver dependência parcial, a operação é recusada para evitar mudança silenciosa. Camadas 3D, de ajuste e bloqueadas também são recusadas. O conteúdo permanece editável ao abrir a precomp.

## Prévia e limitações

A prévia mostra a receita original do catálogo. Alterar duração ou intensidade não renderiza uma prévia nova; os valores personalizados só são aplicados ao adicionar à timeline. O painel usa 13 imagens PNG por receita, atualizadas por `app.scheduleTask`; não depende de navegador, servidor ou download. ScriptUI exibe sequências de PNG, não GIF animado.

O pacote oferece 98 receitas; RGB Split uniforme e RGB Split Heavy (IDs 42 e 43) não foram incluídos porque os efeitos nativos verificados não implementam essa operação. Em transições, o painel cria o clipe, mas não monta nem reposiciona a tomada de saída. Transformações de câmera podem revelar bordas do conteúdo; aumente a escala quando necessário. Não há suporte a arrastar e soltar itens do navegador: use **Adicionar à timeline** e depois mova o clipe.

## Implementação

`Plugin/Browser.template.jsx` contém o painel ScriptUI. `Tests/build_plugin.py` combina o template com receitas validadas e grupos de propriedades nativos, converte os GIFs de origem em 13 PNGs por receita e gera `Plugin/IGPACK Motion Browser.jsx` e `Plugin/manifest.json`. O instalador injeta no JSX o caminho absoluto dos assets. O painel usa a ponte `app.run` do EffectCraft 0.21.0 para abrir composição, posicionar CTI, aplicar preset nativo e selecionar a camada. Não altera o binário do aplicativo nem exige permissão de rede.

Para reconstruir o JSX e as imagens, instale Python 3.10+ e Pillow, configure `EFFECTCRAFT_CLI` se necessário e gere/valide primeiro as receitas e prévias do pack; em seguida gere o painel:

```powershell
python Tests/build.py --poc
python Tests/validate.py --poc
python Tests/build.py
python Tests/validate.py
python Tests/build_plugin.py
```

O build exige `Documentation/native_effects.json`, `Documentation/catalog.json` e os GIFs de `Previews/`; produz 98 receitas, 1.274 PNGs e manifesto de hashes. A instalação requer EffectCraft 0.21.0 no Windows. Para reinstalar uma build, remova a anterior com `Uninstall.bat` antes de executar `Install.bat`.

## Verificação

`Plugin/Tests/integration_report.json` registra sucesso em testes headless: filtros e busca, timer de prévia e fechamento do painel, instalação duplicada, desinstalação com preservação de arquivos alterados e 98 callbacks reais de **Adicionar à timeline** em 150% da duração e 75% da intensidade. Também foram verificadas rejeições por seleção ausente, duração inválida e falta de espaço na composição. A descoberta do painel foi confirmada em uma instalação isolada do aplicativo; as capturas de encaixe estão em `Plugin/Tests/`.

O relatório `Plugin/Tests/desktop_report.json` também registra a descoberta e abertura do painel nativo, avanço da prévia, renderização antes/durante/depois de uma sobreposição, precomp de texto e Undo na interface real. A instância de teste usou a GPU AMD Radeon RX 7600 (Vulkan), em perfil isolado. Foram amostradas três receitas nessa instância, não toda a biblioteca em GPU; não houve certificação com filmagem comercial nem exportação de todos os frames. As prévias são de referência e não garantem o resultado em toda composição.
