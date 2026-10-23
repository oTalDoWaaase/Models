import bpy, os, json, math
from mathutils import Vector

root='/workspace/Models/assets/cachorrinho'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=os.path.join(root,'Biscoito_Puppy.fbx'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(objects)==1, len(objects)
o=objects[0]; mesh=o.data; mesh.calc_loop_triangles()
with open(os.path.join(root,'asset_info.json')) as f: expected=json.load(f)
assert len(mesh.loop_triangles)==expected['triangles']
assert 0<len(mesh.loop_triangles)<=9500
assert len(mesh.uv_layers)==1
assert all(math.isfinite(v) for vertex in mesh.vertices for v in vertex.co)
assert all(poly.area>1e-12 for poly in mesh.polygons)
assert all(0<=v<=1 for uv in mesh.uv_layers.active.data for v in uv.uv)
assert len(mesh.materials)==1
images=[n.image for n in mesh.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
assert images and all(tuple(i.size)==(512,512) for i in images)
assert not any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
report={'fbx_reimport':'passed','mesh_count':len(objects),'triangles':len(mesh.loop_triangles),
        'uv_in_range':True,'texture_loaded':True,'finite_geometry':True,'nonzero_face_area':True,
        'roblox_studio_tested':False}
with open(os.path.join(root,'validation.json'),'w') as f: json.dump(report,f,indent=2)
print('VALIDATION',json.dumps(report))

# A neutral thumbnail of the actual reimported FBX, including its exported texture.
scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=False
scene.render.resolution_x=640; scene.render.resolution_y=640; scene.render.resolution_percentage=100
scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
# Imported axes are converted by the importer back into Blender's Z-up space.
bpy.ops.object.camera_add(location=(3.25,-5.5,2.65)); camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,1.08))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO'; camera.data.ortho_scale=3.2; scene.camera=camera
bpy.ops.object.light_add(type='AREA',location=(-3,-4,6)); light=bpy.context.object
light.data.energy=450; light.data.size=4
light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
scene.view_settings.view_transform='AgX'; scene.render.image_settings.file_format='PNG'
scene.render.filepath=os.path.join(root,'Biscoito_FBX_Check.png')
bpy.ops.render.render(write_still=True)
