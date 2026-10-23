# Cachorro beagle

Modelo original com anatomia e acabamento de orientação naturalista.
Prévia: `Cachorro_Beagle_Preview.png`.

## Conteúdo

- `Cachorro_Beagle.fbx`: modelo com as texturas incorporadas.
- `Cachorro_Beagle.blend`: arquivo editável do Blender 4.3, incluído no ZIP.
- `Cachorro_Beagle_BaseColor.png`: cor, 4096 × 4096 pixels, sRGB.
- `Cachorro_Beagle_Normal.png`: detalhes de superfície, 2048 × 2048 pixels, Non-Color, espaço tangente/OpenGL.
- `Cachorro_Beagle_Roughness.png`: rugosidade, 1024 × 1024 pixels, Non-Color.
- Nos mamíferos, `*_FurColor.png`: cores da malha separada de pelos.
- `validation.json`: verificações da reimportação do FBX no Blender.

## Usar em um editor 3D

Importe o FBX. Se o editor não reconhecer as texturas incorporadas, use os PNGs
fornecidos nos canais Base Color, Normal e Roughness do material. Metalness = 0.
Na fonte Blender, os mapas já estão conectados.

Os pelos dos mamíferos são geometria real, em um objeto separado chamado
`*_GuardHairs`, com material e textura próprios. Não dependem de um sistema
de partículas. É possível ocultar essa malha para editar o corpo com mais leveza.

## Especificações

- 460,408 triângulos no total; 2 malha(s).
- Modelo estático, sem esqueleto, animações ou formas de expressão.
- A prioridade desta versão é a qualidade visual; não foi otimizada para Roblox.
- A iluminação da prévia não é incorporada ao FBX.
- FBX reimportado e validado no Blender; outros aplicativos podem tratar
  materiais, escalas e normais de maneira diferente.

O eixo vertical no FBX é Y; a fonte Blender usa Z. Ajuste a escala conforme a cena.
As partes de detalhe incluem componentes sobrepostos: este é um modelo visual,
não um sólido preparado para impressão 3D.
