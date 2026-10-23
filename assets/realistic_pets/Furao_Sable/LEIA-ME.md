# Furão

Modelo original com anatomia e acabamento de orientação naturalista.
Prévia: `Furao_Sable_Preview.png`.

## Conteúdo

- `Furao_Sable.fbx`: modelo com as texturas incorporadas.
- `Furao_Sable.blend`: arquivo editável do Blender 4.3, incluído no ZIP.
- `Furao_Sable_BaseColor.png`: cor, 4096 × 4096 pixels, sRGB.
- `Furao_Sable_Normal.png`: detalhes de superfície, 2048 × 2048 pixels, Non-Color, espaço tangente/OpenGL.
- `Furao_Sable_Roughness.png`: rugosidade, 1024 × 1024 pixels, Non-Color.
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

- 518,596 triângulos no total; 2 malha(s).
- Modelo estático, sem esqueleto, animações ou formas de expressão.
- A prioridade desta versão é a qualidade visual; não foi otimizada para Roblox.
- A iluminação da prévia não é incorporada ao FBX.
- FBX reimportado e validado no Blender; outros aplicativos podem tratar
  materiais, escalas e normais de maneira diferente.

O eixo vertical no FBX é Y; a fonte Blender usa Z. Ajuste a escala conforme a cena.
As partes de detalhe incluem componentes sobrepostos: este é um modelo visual,
não um sólido preparado para impressão 3D.
