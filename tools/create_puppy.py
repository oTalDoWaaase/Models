"""Generate an original, textured static puppy asset and its studio renders.
Run: blender -b --python tools/create_puppy.py
"""
import bpy, math, os, json
from mathutils import Vector

OUT = '/workspace/Models/assets/cachorrinho'
os.makedirs(OUT, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.materials):
    bpy.data.materials.remove(block)

COLORS = {
    'caramel': '#CB8F51', 'cream': '#FFF0D4', 'ear': '#A96536',
    'inner': '#DE9A7E', 'dark': '#302321', 'eye': '#171E25',
    'white': '#FFFFFF', 'pink': '#F19C9E', 'teal': '#329C9D',
    'teal_light': '#65C4BF', 'gold': '#EEC368', 'toe': '#D8B98E',
}
def rgb(h):
    return tuple(int(h[i:i+2],16)/255 for i in (1,3,5))
def linear(v):
    return v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4
mats = {}
for key, h in COLORS.items():
    m=bpy.data.materials.new(key); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*[linear(v) for v in rgb(h)],1)
    p.inputs['Roughness'].default_value=.27 if key=='eye' else .68
    mats[key]=m
parts=[]
def finish(o,name,col):
    o.name=name; o.data.materials.clear(); o.data.materials.append(mats[col])
    for p in o.data.polygons: p.use_smooth=True
    parts.append(o)
    return o
def ell(name,loc,scale,col,seg=24,rings=16,rot=None):
    if name=='Puppy_head': seg,rings=32,20
    elif name.startswith('Floppy_ear'): seg,rings=20,14
    elif name.startswith('Muzzle_') or name in ('Eye_L','Eye_R'): seg,rings=20,12
    else: seg,rings=min(seg,16),min(rings,10)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
    o=bpy.context.object; o.scale=scale
    if rot: o.rotation_euler=rot
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,col)
def tube(name,points,radii,col,sides=10):
    verts=[]; faces=[]
    for i,co in enumerate(points):
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
        tangent.normalize()
        axis=Vector((0,1,0)) if abs(tangent.y)<.9 else Vector((1,0,0))
        u=tangent.cross(axis).normalized(); v=tangent.cross(u).normalized()
        for j in range(sides):
            q=Vector(co)+radii[i]*(u*math.cos(j*math.tau/sides)+v*math.sin(j*math.tau/sides))
            verts.append(q)
    for i in range(len(points)-1):
        for j in range(sides):
            a=i*sides+j; b=i*sides+(j+1)%sides
            faces.append((a,b,b+sides,a+sides))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple((len(points)-1)*sides+j for j in range(sides)))
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    o=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(o)
    return finish(o,name,col)
def curve(name,coords,r,col):
    c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.resolution_u=10
    c.bevel_depth=r; c.bevel_resolution=2
    s=c.splines.new('BEZIER'); s.bezier_points.add(len(coords)-1)
    for p,co in zip(s.bezier_points,coords):
        p.co=co; p.handle_left_type='AUTO'; p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,c); bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active=o; o.select_set(True)
    bpy.ops.object.convert(target='MESH'); o=bpy.context.object
    o.select_set(False)
    return finish(o,name,col)

# A compact torso with sculpted, continuous shoulders and short legs.
bodyparts=[ell('Torso',(0,.30,.85),(.51,.68,.49),'caramel'),
           ell('Neck',(0,-.20,1.05),(.39,.38,.40),'caramel')]
for x in (-.34,.34):
    for y in (-.23,.72):
        bodyparts.append(ell('Leg',(x,y,.43),(.225,.24,.36),'caramel',20,12))
bpy.ops.object.select_all(action='DESELECT')
for o in bodyparts: o.select_set(True); parts.remove(o)
bpy.context.view_layer.objects.active=bodyparts[0]; bpy.ops.object.join()
body=bpy.context.object; body.name='Body_sculpt'
rem=body.modifiers.new('Soft fused silhouette','REMESH'); rem.mode='VOXEL'; rem.voxel_size=.045
bpy.ops.object.modifier_apply(modifier=rem.name)
sm=body.modifiers.new('Relax','SMOOTH'); sm.factor=1.1; sm.iterations=5
bpy.ops.object.modifier_apply(modifier=sm.name)
de=body.modifiers.new('Game mesh','DECIMATE'); de.ratio=.28
bpy.ops.object.modifier_apply(modifier=de.name)
parts.append(body)
for p in body.data.polygons: p.use_smooth=True

for side,x in [('L',-.34),('R',.34)]:
    for label,y in [('Front',-.34),('Back',.74)]:
        ell(f'{label}_paw_{side}',(x,y,.205),(.235,.285,.195),'cream',20,12)
        for dx in (-.065,.065):
            curve(f'{label}_toe_{side}',[(x+dx,y-.263,.22),(x+dx,y-.249,.27),(x+dx,y-.219,.302)],.009,'toe')

ell('Soft_chest',(0,-.322,.80),(.30,.23,.34),'cream')
ell('Puppy_head',(0,-.43,1.57),(.635,.535,.59),'caramel',32,24)
ell('Cheek_L',(-.32,-.73,1.32),(.28,.25,.255),'caramel')
ell('Cheek_R',(.32,-.73,1.32),(.28,.25,.255),'caramel')

# A cream blaze follows the surface of the head instead of floating above it.
verts=[]; faces=[]; rows=16; cols=8
for i in range(rows+1):
    z=1.34+.68*i/rows
    t=i/rows; width=.07+.13*(1-t)**2
    width*=math.sqrt(max(.0001,1-t))
    for j in range(cols+1):
        x=width*(2*j/cols-1)
        q=max(.001,1-(x/.635)**2-((z-1.57)/.59)**2)
        y=-.43-.535*math.sqrt(q)-.009
        verts.append((x,y,z))
for i in range(rows):
    for j in range(cols):
        a=i*(cols+1)+j; faces.append((a,a+1,a+cols+2,a+cols+1))
mesh=bpy.data.meshes.new('Blaze'); mesh.from_pydata(verts,[],faces); mesh.update()
o=bpy.data.objects.new('Cream_forehead_blaze',mesh); bpy.context.collection.objects.link(o)
finish(o,o.name,'cream')

for sign,side in [(-1,'L'),(1,'R')]:
    ell('Floppy_ear_'+side,(sign*.61,-.32,1.54),(.235,.205,.425),'ear',24,16,rot=(0,sign*-.27,sign*.10))
    ell('Ear_inner_'+side,(sign*.655,-.492,1.48),(.125,.049,.255),'inner',20,12,rot=(0,sign*-.26,0))
    ell('Eye_rim_'+side,(sign*.278,-.891,1.64),(.163,.068,.181),'ear',24,16)
    ell('Eye_'+side,(sign*.278,-.941,1.648),(.132,.065,.15),'eye',24,16)
    ell('Eye_sparkle_'+side,(sign*.278-.038,-1.002,1.704),(.035,.012,.039),'white',16,10)
    ell('Eye_small_sparkle_'+side,(sign*.278+.035,-1.004,1.609),(.014,.008,.016),'white',12,8)
    ell('Brow_'+side,(sign*.29,-.846,1.868),(.105,.026,.04),'cream',16,10,rot=(0,sign*-.15,0))
    ell('Muzzle_'+side,(sign*.135,-.929,1.337),(.225,.179,.174),'cream',24,16)
    for dx,dz in [(0,.02),(.06,-.01),(.025,-.05)]:
        ell('Whisker_dot_'+side,(sign*(.205+dx),-1.086+dx*.25,1.345+dz),(.011,.007,.011),'toe',10,6)

# Rounded triangular nose with a small warm glint.
verts=[(-.125,-1.087,1.458),(.125,-1.087,1.458),(0,-1.124,1.315),
       (-.105,-1.193,1.451),(.105,-1.193,1.451),(0,-1.207,1.346)]
faces=[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)]
mesh=bpy.data.meshes.new('Nose'); mesh.from_pydata(verts,[],faces); mesh.update()
o=bpy.data.objects.new('Button_nose',mesh); bpy.context.collection.objects.link(o); finish(o,o.name,'dark')
bpy.context.view_layer.objects.active=o
be=o.modifiers.new('Rounded nose','BEVEL'); be.width=.042; be.segments=3
bpy.ops.object.modifier_apply(modifier=be.name)
ell('Nose_glint',(-.032,-1.195,1.445),(.032,.009,.012),'inner',16,8)
curve('Smile_L',[(0,-1.113,1.32),(-.06,-1.114,1.283),(-.139,-1.094,1.308)],.013,'dark')
curve('Smile_R',[(0,-1.113,1.32),(.06,-1.114,1.283),(.139,-1.094,1.308)],.013,'dark')
ell('Tiny_tongue',(0,-1.083,1.248),(.064,.045,.089),'pink',20,12)
curve('Tongue_crease',[(0,-1.128,1.277),(0,-1.129,1.237)],.005,'inner')

# A lifted, gently curling tail; the cream tip reads from every angle.
tailpts=[(0,.81,.90),(.20,1.02,.99),(.40,1.16,1.15),(.52,1.17,1.35),(.54,1.08,1.51),(.49,.97,1.58),(.45,.91,1.59)]
tailr=[.17,.16,.145,.125,.095,.055,.003]
smoothpts=[]; smoothr=[]
for i in range(len(tailpts)-1):
    p0=Vector(tailpts[max(0,i-1)]); p1=Vector(tailpts[i])
    p2=Vector(tailpts[i+1]); p3=Vector(tailpts[min(len(tailpts)-1,i+2)])
    for j in range(5):
        t=j/5
        smoothpts.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
        smoothr.append(tailr[i]*(1-t)+tailr[i+1]*t)
smoothpts.append(Vector(tailpts[-1])); smoothr.append(tailr[-1])
tail=tube('Curled_tail',smoothpts,smoothr,'caramel',12)
tail.data.materials.append(mats['cream'])
for p in tail.data.polygons:
    if p.index>=20*12 and p.index<(len(smoothpts)-1)*12: p.material_index=1
tail.data.polygons[-1].material_index=1

# Turquoise neckerchief with a raised hem, tied ends and a tiny gold medallion.
bpy.ops.mesh.primitive_torus_add(major_segments=40,minor_segments=10,location=(0,-.23,1.105),major_radius=.34,minor_radius=.055)
o=bpy.context.object; o.scale=(1.15,1,.8); finish(o,'Bandana_neck','teal')
verts=[(-.29,-.535,1.075),(.29,-.535,1.075),(0,-.594,.67),(-.25,-.495,1.075),(.25,-.495,1.075),(0,-.554,.69)]
faces=[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)]
mesh=bpy.data.meshes.new('Bandana'); mesh.from_pydata(verts,[],faces); mesh.update()
o=bpy.data.objects.new('Bandana_front',mesh); bpy.context.collection.objects.link(o); finish(o,o.name,'teal')
bpy.context.view_layer.objects.active=o
be=o.modifiers.new('Soft fabric edges','BEVEL'); be.width=.025; be.segments=3
bpy.ops.object.modifier_apply(modifier=be.name)
curve('Bandana_stitched_hem',[(-.23,-.56,1.038),(0,-.617,.728),(.23,-.56,1.038)],.009,'teal_light')
ell('Bandana_knot',(.365,-.19,1.106),(.09,.095,.08),'teal_light',16,10)
ell('Bandana_tie',(.419,-.11,1.011),(.064,.06,.14),'teal',16,10,rot=(0,-.4,-.4))
ell('Gold_tag',(0,-.606,.951),(.072,.018,.073),'gold',20,12)
ell('Tag_paw_pad',(0,-.626,.938),(.024,.006,.019),'cream',12,8)
for x,z in [(-.028,.963),(0,.977),(.028,.963)]:
    ell('Tag_paw_toe',(x,-.625,z),(.010,.005,.011),'cream',10,6)

# Keep one UV-mapped mesh for Roblox. Each palette colour occupies its own tile.
bpy.ops.object.select_all(action='DESELECT')
for o in parts: o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.object.join(); puppy=bpy.context.object; puppy.name='Biscoito_Puppy'
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
bpy.context.scene.cursor.location=(0,0,0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
tri=puppy.modifiers.new('Export triangulation','TRIANGULATE'); bpy.ops.object.modifier_apply(modifier=tri.name)
# Cap the asset below 10k triangles without sacrificing the major silhouettes.
if len(puppy.data.polygons)>9500:
    de=puppy.modifiers.new('Triangle budget','DECIMATE'); de.ratio=9400/len(puppy.data.polygons)
    de.delimit={'MATERIAL','SEAM'}; bpy.ops.object.modifier_apply(modifier=de.name)

keys=list(COLORS); size=512; tile=size//4
img=bpy.data.images.new('Biscoito_BaseColor',width=size,height=size,alpha=True)
pixels=[]
for y in range(size):
    for x in range(size):
        idx=min(11,(y//tile)*4+x//tile)
        pixels.extend((*rgb(COLORS[keys[idx]]),1))
img.pixels=pixels
img.filepath_raw=os.path.join(OUT,'Biscoito_BaseColor.png'); img.file_format='PNG'; img.save()
uv=puppy.data.uv_layers.active or puppy.data.uv_layers.new(name='UVMap')
for poly in puppy.data.polygons:
    key=puppy.data.materials[poly.material_index].name
    idx=keys.index(key); cx=(idx%4+.5)/4; cy=(idx//4+.5)/4
    for k,li in enumerate(poly.loop_indices):
        # Nonzero-area islands, comfortably inset inside the colour tile.
        offsets=[(-.025,-.025),(.025,-.025),(0,.025)]
        dx,dy=offsets[k%3]; uv.data[li].uv=(cx+dx,cy+dy)

# Save material indices for richer studio-render roughness after export.
render_ids=[p.material_index for p in puppy.data.polygons]
render_mats=list(puppy.data.materials)
material=bpy.data.materials.new('Biscoito_Atlas'); material.use_nodes=True
nodes=material.node_tree.nodes; shader=nodes.get('Principled BSDF')
tex=nodes.new('ShaderNodeTexImage'); tex.image=img; tex.interpolation='Closest'
material.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color'])
shader.inputs['Roughness'].default_value=.65
puppy.data.materials.clear(); puppy.data.materials.append(material)
for p in puppy.data.polygons: p.material_index=0

bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'Biscoito_Puppy.fbx'),use_selection=True,
    object_types={'MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
    axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='FACE',
    use_tspace=True,add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)

stats={'name':puppy.name,'vertices':len(puppy.data.vertices),'triangles':len(puppy.data.polygons),
       'dimensions_blender_units':list(puppy.dimensions),'rigged':False,'animated':False,
       'texture':'Biscoito_BaseColor.png','texture_size':[size,size],'mesh_objects':1}
with open(os.path.join(OUT,'asset_info.json'),'w') as f: json.dump(stats,f,indent=2)

# Preserve the exact textured export mesh in the editable source file.
img.pack()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Biscoito_Puppy.blend'))

# Studio staging is render-only and never included in the FBX.
puppy.data.materials.clear()
for m in render_mats: puppy.data.materials.append(m)
for p,i in zip(puppy.data.polygons,render_ids): p.material_index=i
floor=bpy.data.materials.new('Studio sage'); floor.diffuse_color=(.135,.215,.215,1); floor.use_nodes=True
floor.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.135,.215,.215,1)
floor.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0)); bpy.context.object.data.materials.append(floor)
world=bpy.context.scene.world; world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.37,.49,.54,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.45
def area(name,loc,energy,size):
    bpy.ops.object.light_add(type='AREA',location=loc); o=bpy.context.object; o.name=name
    o.data.energy=energy; o.data.shape='DISK'; o.data.size=size
    o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
area('Large softbox',(-3,-4,6),450,4)
area('Fill',(4,-2,3),230,3)
area('Rim',(1,4,5),550,3)
bpy.ops.object.camera_add(location=(3.25,-5.5,2.65)); camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,1.08))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO'; camera.data.ortho_scale=3.2; bpy.context.scene.camera=camera
scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=80
scene.cycles.use_denoising=False; scene.render.resolution_x=1100; scene.render.resolution_y=1100; scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'
scene.render.filepath=os.path.join(OUT,'Biscoito_Preview.png'); bpy.ops.render.render(write_still=True)
camera.location=(0,-6,2.15); camera.rotation_euler=(Vector((0,-.05,1.08))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=os.path.join(OUT,'Biscoito_Front.png'); bpy.ops.render.render(write_still=True)
camera.location=(3.8,4.8,2.7); camera.rotation_euler=(Vector((0,.2,1.03))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=os.path.join(OUT,'Biscoito_Back.png'); bpy.ops.render.render(write_still=True)
print('ASSET_REPORT',json.dumps(stats))
