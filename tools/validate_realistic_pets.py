"""Reimport every exported FBX and check geometry, UVs, maps and mesh counts."""
import bpy, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'assets'/'realistic_pets'
results=[]
for folder in sorted(ROOT.iterdir()):
    if not folder.is_dir() or not (folder/'asset_info.json').exists():continue
    info=json.loads((folder/'asset_info.json').read_text());name=info['name']
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for image in list(bpy.data.images):
        if image.users==0:bpy.data.images.remove(image)
    bpy.ops.import_scene.fbx(filepath=str(folder/(name+'.fbx')))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert len(meshes)==info['mesh_count'],(name,len(meshes))
    triangles=0;maps=[];small_faces=0
    for o in meshes:
        mesh=o.data;mesh.calc_loop_triangles();triangles+=len(mesh.loop_triangles)
        assert len(mesh.uv_layers)>0,name
        assert all(math.isfinite(x) for v in mesh.vertices for x in v.co),name
        assert all(math.isfinite(x) and -.00001<=x<=1.00001 for uv in mesh.uv_layers.active.data for x in uv.uv),name
        assert all(p.area>0 for p in mesh.polygons),name
        for m in mesh.materials:
            assert m.use_nodes,name
            textures=[n.image for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
            assert textures,(name,m.name)
            for img in textures:
                assert img.size[0]>0 and img.size[1]>0,(name,img.name)
                maps.append({'image':img.name,'resolution':list(img.size)})
    assert triangles==info['triangles'],(name,triangles,info['triangles'])
    assert any(m['resolution']==[4096,4096] for m in maps),name
    result={'name':name,'fbx_reimport':'passed','meshes':len(meshes),'triangles':triangles,
            'finite_geometry':True,'uv_coordinates_valid':True,'images_loaded':maps,
            'rigged':False,'animated':False,'roblox_studio_tested':False}
    (folder/'validation.json').write_text(json.dumps(result,indent=2))
    results.append(result);print('VALIDATED',name,triangles,flush=True)
assert len(results)==5,('Expected all five animals',len(results))
(ROOT/'validation_summary.json').write_text(json.dumps(results,indent=2))
print('ALL_FIVE_FBX_VALIDATED',flush=True)
