# Blender View Layer Addon

## Overview
O Blender View Layer Addon é uma ferramenta poderosa para criar e gerenciar view layers e collections no Blender. Ele automatiza a configuração de passes, AOVs e organiza as collections de forma eficiente, seguindo convenções de nomenclatura específicas.

## Features
- Criação automática de view layers a partir de collections.
- Configuração de passes de renderização e AOVs (Arbitrary Output Variables).
- Suporte a convenções de nomenclatura para collections e view layers.
- Painéis intuitivos para gerenciar view layers, passes e AOVs.
- Detecção automática de AOVs configurados nos materiais do projeto.
- Suporte a collections específicas, como `lgt.` (lighting) e `.hdt` (holdout).

## Installation
1. Baixe os arquivos do addon.
2. Abra o Blender e vá para `Edit > Preferences`.
3. Navegue até a aba `Add-ons`.
4. Clique em `Install...` e selecione o arquivo zip ou pasta do addon.
5. Ative o addon marcando a caixa ao lado do nome na lista.

## Usage
- Acesse o painel do addon na barra lateral (`N`) no Viewport 3D, na aba **View Layer Generator**.
- Utilize os botões disponíveis para:
  - Gerar view layers a partir de collections.
  - Configurar passes de renderização e AOVs.
  - Atualizar a lista de collections e passes disponíveis.
- Personalize as configurações diretamente no painel.

## Naming Conventions
O addon segue convenções de nomenclatura específicas para organizar as collections e view layers. Essas convenções são fundamentais para o funcionamento correto do addon:

### View Layers
- **View Layers baseados em collections**: O nome do view layer será igual ao nome da collection correspondente.
- **View Layers para Grease Pencil**: Devem terminar com `.GP` ou `.GP.vl` (exemplo: `Sketches.GP`).
- **View Layers de iluminação**: Devem começar com `lgt.` (exemplo: `lgt.key`, `lgt.fill`).

### Collections
- **Collections de iluminação (`lgt.`)**:
  - Devem começar com `lgt.` e podem incluir um sufixo para especificar o tipo de iluminação (exemplo: `lgt.key`, `lgt.fill`).
  - A collection `lgt.all` será ativada em todos os view layers, exceto os de Grease Pencil.
- **Collections de holdout (`.hdt`)**:
  - Devem terminar com `.hdt` e serão configuradas como holdout no view layer correspondente.
  - Exemplo: `Background.hdt`.
- **Collections gerais (`.all`)**:
  - Devem terminar com `.all` e serão ativadas em todos os view layers.
  - Exemplo: `Environment.all`.

### AOVs (Arbitrary Output Variables)
- Os AOVs são detectados automaticamente nos materiais do projeto.
- Cada AOV deve ter um nome único e pode ser do tipo `COLOR` ou `VALUE`.

## Development
Este addon é desenvolvido em Python utilizando a API do Blender. Contribuições são bem-vindas! Certifique-se de seguir as práticas recomendadas para desenvolvimento de addons no Blender.

### Notas de Desenvolvimento
- Certifique-se de que todas as novas funcionalidades respeitem as convenções de nomenclatura descritas acima.
- Teste o addon em diferentes versões do Blender para garantir compatibilidade.

## License
Este projeto está licenciado sob a licença MIT. Consulte o arquivo LICENSE para mais detalhes.