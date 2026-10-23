"""Package the five verified models and create a GitHub download gallery."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from PIL import Image
import json, hashlib

repo=Path(__file__).resolve().parents[1]
root=repo/'assets'/'realistic_pets'
packages=root/'packages';packages.mkdir(exist_ok=True)
models=[('Gato_Tigrado','Gato tigrado'),('Coelho_Cinza','Coelho cinza'),
        ('Papagaio_Amazonas','Papagaio'),('Cachorro_Beagle','Cachorro beagle'),('Furao_Sable','Furão')]
gallery=['# Animais — coleção naturalista','',
         'Cinco modelos originais com proporções mais naturais, texturas PBR e detalhes de pelos ou penas. '
         'Esta edição prioriza a aparência, sem o limite de polígonos do primeiro cachorrinho.', '',
         'Os modelos são estáticos, sem rig ou animações. Os mamíferos incluem pelos em geometria; '
         'o papagaio inclui penas sobrepostas. As prévias são renders dos próprios modelos.', '',
         '## Downloads','',
         'Cada ZIP inclui FBX, fonte editável Blender, texturas, prévia e instruções. '
         'No GitHub, abra o arquivo e use **Download raw file**, ou os links diretos abaixo.', '',
         '| Animal | Pacote completo | FBX | Triângulos |',
         '| --- | --- | --- | ---: |']
checksums={}
base='https://github.com/oTalDoWaaase/Models/raw/refs/heads/assets/animais-naturalistas/assets/realistic_pets'
for name,label in models:
    folder=root/name;info=json.loads((folder/'asset_info.json').read_text())
    validation=json.loads((folder/'validation.json').read_text());assert validation['fbx_reimport']=='passed'
    for p in folder.glob('*.png'):
        with Image.open(p) as im:im.verify()
    guide=f'''# {label}

Modelo original com anatomia e acabamento de orientação naturalista.
Prévia: `{name}_Preview.png`.

## Conteúdo

- `{name}.fbx`: modelo com as texturas incorporadas.
- `{name}.blend`: arquivo editável do Blender 4.3, incluído no ZIP.
- `{name}_BaseColor.png`: cor, 4096 × 4096 pixels, sRGB.
- `{name}_Normal.png`: detalhes de superfície, 2048 × 2048 pixels, Non-Color, espaço tangente/OpenGL.
- `{name}_Roughness.png`: rugosidade, 1024 × 1024 pixels, Non-Color.
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

- {info['triangles']:,} triângulos no total; {info['mesh_count']} malha(s).
- Modelo estático, sem esqueleto, animações ou formas de expressão.
- A prioridade desta versão é a qualidade visual; não foi otimizada para Roblox.
- A iluminação da prévia não é incorporada ao FBX.
- FBX reimportado e validado no Blender; outros aplicativos podem tratar
  materiais, escalas e normais de maneira diferente.

O eixo vertical no FBX é Y; a fonte Blender usa Z. Ajuste a escala conforme a cena.
As partes de detalhe incluem componentes sobrepostos: este é um modelo visual,
não um sólido preparado para impressão 3D.
'''
    (folder/'LEIA-ME.md').write_text(guide)
    archive=packages/(name+'.zip')
    with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(folder.iterdir()):
            if p.is_file() and p.suffix!='.blend1':z.write(p,name+'/'+p.name)
    with ZipFile(archive) as z:assert z.testzip() is None
    assert archive.stat().st_size<100*1024*1024,(archive,archive.stat().st_size)
    for p in [archive,folder/(name+'.fbx')]:checksums[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    gallery.append(f'| {label} | [Baixar ZIP]({base}/packages/{name}.zip) | [Baixar FBX]({base}/{name}/{name}.fbx) | {info["triangles"]:,} |')
    print('PACKAGE',name,archive.stat().st_size,flush=True)
gallery+=['','## Prévias','']
for name,label in models:
    gallery+=[f'### {label}','',f'![{label}]({name}/{name}_Preview.png)','']
gallery+=['## Verificação','',
          'Os cinco arquivos FBX foram reimportados no Blender e conferidos: '
          'número de malhas e triângulos, coordenadas finitas, UVs e leitura das texturas. '
          'Os pacotes ZIP também tiveram sua integridade verificada.', '',
          'Scripts de geração e validação: `tools/create_realistic_pets.py` e '
          '`tools/validate_realistic_pets.py`, na raiz do repositório.']
(root/'README.md').write_text('\n'.join(gallery)+'\n')
(root/'SHA256SUMS.json').write_text(json.dumps(checksums,indent=2)+'\n')
print('ALL_FIVE_PACKAGED',flush=True)
