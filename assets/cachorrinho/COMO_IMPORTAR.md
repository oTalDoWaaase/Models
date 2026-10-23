# Biscoito — cachorrinho para Roblox

Modelo original de um filhote pequeno, caramelo e creme, com orelhas caídas,
bandana azul e medalha de patinha. Pose em pé, boca sorrindo e língua de fora.

## Arquivos

- `Biscoito_Puppy.fbx`: modelo principal, com textura de cores incorporada.
- `Biscoito_BaseColor.png`: a mesma textura, separada para importação manual.
- `Biscoito_Puppy.blend`: fonte editável no Blender 4.3 ou posterior.
- `Biscoito_Preview.png`, `Biscoito_Front.png`, `Biscoito_Back.png`: imagens do modelo.
- `Biscoito_FBX_Check.png`: render de conferência feito após reimportar o FBX.
- `asset_info.json` e `validation.json`: informações técnicas e verificações.

## Importar no Roblox Studio

1. Abra seu jogo e use o importador 3D do Studio (Import 3D).
2. Selecione `Biscoito_Puppy.fbx`. Confira o tamanho e a orientação na prévia.
3. Importe a malha e sua textura. O FBX contém uma malha e um material.
4. Caso as cores não sejam carregadas automaticamente, importe
   `Biscoito_BaseColor.png` como imagem e use seu ID em `MeshPart.TextureID`.
   Também é possível usar a imagem em `SurfaceAppearance.ColorMap`.
   Mantenha `MeshPart.Color` branco para não alterar as cores da textura.
5. Ajuste o tamanho para o jogo: cerca de 2 a 3 studs de altura funciona
   como ponto de partida para um pet pequeno. Preserve as proporções.
6. Para decoração, ative `Anchored`. Para um pet seguidor, o movimento e a
   configuração de colisão devem ser controlados pelo script do jogo.

O pivô está no chão, no centro do modelo. O FBX usa Y para cima; no arquivo
Blender, Z é o eixo vertical. Confira a frente no importador antes de salvar.

## Especificações e limites

- Uma malha com aproximadamente 9.400 triângulos e UVs.
- Textura de cores de 512 × 512 pixels, sem dependências externas.
- Modelo estático: sem esqueleto e sem animações de andar ou correr.
- Partes visuais reunidas em uma malha, com componentes sobrepostos;
  destinado a jogos, não a impressão 3D ou deformação orgânica.
- As prévias de estúdio usam iluminação e brilho próprios do Blender.
  A aparência no Studio depende da iluminação e do material do jogo.
- O FBX foi reimportado no Blender e conferido quanto a geometria, UVs e
  carregamento da textura. A importação no Roblox Studio não foi executada
  neste ambiente.

Para recriar os arquivos no repositório:

```sh
cd /workspace/Models
blender -b -t 4 --python tools/create_puppy.py
blender -b -t 2 --python tools/validate_puppy.py
```
