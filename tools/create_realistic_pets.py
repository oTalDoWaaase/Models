"""Original natural-proportion game animals; Blender 4.3, no external assets.
Usage: blender -b -t 6 --python tools/create_realistic_pets.py -- cat
Species: cat, rabbit, parrot, dog, ferret. Outputs beside this repository.
"""
import bpy, math, os, sys, json, random
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SPECIES=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'cat'
NAMES={'cat':'Gato_Tigrado','rabbit':'Coelho_Cinza','parrot':'Papagaio_Amazonas','dog':'Cachorro_Beagle','ferret':'Furao_Sable'}
NAME=NAMES[SPECIES]; OUT=ROOT/'assets'/'realistic_pets'/NAME
OUT.mkdir(parents=True,exist_ok=True)
random.seed(29)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.scene.render.engine='CYCLES'
bpy.context.scene.cycles.samples=8; bpy.context.scene.cycles.use_denoising=False
parts=[]; bodyparts=[]

def lin(v): return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def color(h): return tuple(lin(int(h[i:i+2],16)/255) for i in (0,2,4))
def mix(a,b,t):
    t=max(0,min(1,t)); return tuple(x*(1-t)+y*t for x,y in zip(a,b))
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a))); return t*t*(3-2*t)
def mat(name,h,rough=.7,fur=False):
    m=bpy.data.materials.new(name); m.use_nodes=True
    n=m.node_tree.nodes; l=m.node_tree.links; p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color(h),1)
    p.inputs['Roughness'].default_value=rough
    if fur:
        attr=n.new('ShaderNodeVertexColor'); attr.layer_name='Coat'
        tex=n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=95
        tex.inputs['Detail'].default_value=2; tex.inputs['Roughness'].default_value=.72
        geo=n.new('ShaderNodeNewGeometry'); scale=n.new('ShaderNodeVectorMath'); scale.operation='MULTIPLY'
        scale.inputs[1].default_value=(1.1,1.1,.18)
        l.new(geo.outputs['Position'],scale.inputs[0]); l.new(scale.outputs[0],tex.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.18
        ramp.color_ramp.elements[0].color=(.42,.42,.42,1)
        ramp.color_ramp.elements[1].position=.78; ramp.color_ramp.elements[1].color=(1.12,1.12,1.12,1)
        l.new(tex.outputs['Fac'],ramp.inputs[0])
        blend=n.new('ShaderNodeMixRGB'); blend.blend_type='MULTIPLY'; blend.inputs[0].default_value=1
        l.new(attr.outputs['Color'],blend.inputs[1]); l.new(ramp.outputs[0],blend.inputs[2]); l.new(blend.outputs[0],p.inputs['Base Color'])
        bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.24
        bump.inputs['Distance'].default_value=.011 if SPECIES!='parrot' else .005
        l.new(tex.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs[0],p.inputs['Normal'])
        p.inputs['Sheen Weight'].default_value=.18
    return m
FUR=mat('Natural coat','A09584',.83,True)
CREAM=mat('Whiskers and light fur','D2C9B8',.76)
BLACK=mat('Lips and eyelids','302823',.60)
NOSE=mat('Nose leather','302A29',.44)
PINK=mat('Soft ear skin','B78179',.83)
CLAWS=mat('Natural claws','4B4035',.52)

def add(o,name,m):
    o.name=name; o.data.materials.clear(); o.data.materials.append(m)
    for p in o.data.polygons:p.use_smooth=True
    parts.append(o); return o
def ell(name,loc,scale,m=FUR,seg=24,rings=16,rot=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
    o=bpy.context.object; o.scale=scale
    if rot is not None:o.rotation_euler=rot
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return add(o,name,m)
def mass(name,loc,scale,rot=None):
    o=ell(name,loc,scale,rot=rot); bodyparts.append(o);return o
def aligned_ell(name,loc,scale,m,normal,seg=24,rings=16):
    o=ell(name,loc,scale,m,seg,rings)
    o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,-1,0)).rotation_difference(Vector(normal).normalized())
    return o
def path(name,pts,radii,m=FUR,sides=10,steps=4):
    coords=[]; rr=[]
    for i in range(len(pts)-1):
        p0=Vector(pts[max(0,i-1)]);p1=Vector(pts[i]);p2=Vector(pts[i+1]);p3=Vector(pts[min(len(pts)-1,i+2)])
        for j in range(steps):
            t=j/steps
            coords.append(.5*(2*p1+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
            rr.append(radii[i]*(1-t)+radii[i+1]*t)
    coords.append(Vector(pts[-1]));rr.append(radii[-1]);v=[];f=[]
    prev=None
    for i,p in enumerate(coords):
        d=(coords[min(i+1,len(coords)-1)]-coords[max(0,i-1)]).normalized()
        axis=Vector((0,0,1)) if abs(d.z)<.9 else Vector((0,1,0))
        u=d.cross(axis).normalized()
        if prev is not None and u.dot(prev)<0:u=-u
        prev=u;w=d.cross(u).normalized()
        for j in range(sides):v.append(p+rr[i]*(u*math.cos(j*math.tau/sides)+w*math.sin(j*math.tau/sides)))
    for i in range(len(coords)-1):
        for j in range(sides):
            a=i*sides+j;b=i*sides+(j+1)%sides;f.append((a,b,b+sides,a+sides))
    f.append(tuple(reversed(range(sides))));f.append(tuple((len(coords)-1)*sides+j for j in range(sides)))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(v,[],f);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);return add(o,name,m)
def line(name,pts,r=.004,m=BLACK):return path(name,pts,[r]*(len(pts)-1)+[r*.4],m,6,4)
def fuse():
    bpy.ops.object.select_all(action='DESELECT')
    for o in bodyparts:o.select_set(True);parts.remove(o)
    bpy.context.view_layer.objects.active=bodyparts[0];bpy.ops.object.join();o=bpy.context.object;o.name='Continuous_anatomy'
    rem=o.modifiers.new('Sculpt union','REMESH');rem.mode='VOXEL';rem.voxel_size=.012 if SPECIES=='ferret' else .015
    bpy.ops.object.modifier_apply(modifier=rem.name)
    mod=o.modifiers.new('Relax anatomy','SMOOTH');mod.factor=.85;mod.iterations=5;bpy.ops.object.modifier_apply(modifier=mod.name)
    tris=sum(len(p.vertices)-2 for p in o.data.polygons)
    dec=o.modifiers.new('Sculpt topology','DECIMATE');dec.ratio=min(1,28000/tris);bpy.ops.object.modifier_apply(modifier=dec.name)
    for p in o.data.polygons:p.use_smooth=True
    parts.append(o);return o

def ear(name,base,tip,width,depth,inner=True,triangular=False):
    # Closed, gently cupped ear with a separate recessed inner surface.
    base=Vector(base);tip=Vector(tip);axis=tip-base
    verts=[];faces=[];rows=12;cols=10
    for back in (False,True):
        for i in range(rows+1):
            t=i/rows;c=base+axis*t
            w=width*((1-t)**.75 if triangular else math.sin(math.pi*(.12+.88*t))**.70)+.001
            for j in range(cols+1):
                u=2*j/cols-1
                y=(depth*.42 if back else -depth*.42)+depth*.55*(1-u*u)*math.sin(math.pi*t)
                verts.append(c+Vector((w*u,y,0)))
    layer=(rows+1)*(cols+1)
    for b in range(2):
        for i in range(rows):
            for j in range(cols):
                a=b*layer+i*(cols+1)+j; q=(a,a+1,a+cols+2,a+cols+1)
                faces.append(q if b==0 else tuple(reversed(q)))
    border=list(range(cols+1))+[i*(cols+1)+cols for i in range(1,rows+1)]+[rows*(cols+1)+j for j in range(cols-1,-1,-1)]+[i*(cols+1) for i in range(rows-1,0,-1)]
    for a,b in zip(border,border[1:]+border[:1]):faces.append((a,b,b+layer,a+layer))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);add(o,name,FUR)
    if inner:
        iv=[];ff=[]
        for i in range(10):
            t=.12+.72*i/9;c=base+axis*t
            outer=width*((1-t)**.75 if triangular else math.sin(math.pi*(.12+.88*t))**.70)
            inner_ratio=.78*math.sqrt(max(.0001,math.sin(math.pi*i/9)))
            w=inner_ratio*outer
            for j in range(7):
                u=2*j/6-1
                y=-depth*.42+depth*.55*(1-(u*inner_ratio)**2)*math.sin(math.pi*t)-.0015
                iv.append(c+Vector((w*u,y,0)))
        for i in range(9):
            for j in range(6):
                a=i*7+j;ff.append((a,a+1,a+8,a+7))
        me=bpy.data.meshes.new(name+'_inner');me.from_pydata(iv,[],ff);me.update()
        ob=bpy.data.objects.new(name+'_inner',me);bpy.context.collection.objects.link(ob);add(ob,ob.name,PINK)
    return o

def eyes(x,y,z,size,iris_color,slit=False,lateral=.45):
    iris=mat('Iris',iris_color,.16);pupil=mat('Pupil','080B0A',.12)
    n=iris.node_tree.nodes;l=iris.node_tree.links;p=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=22;tex.inputs['Detail'].default_value=3
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=(*[v*.32 for v in color(iris_color)],1)
    ramp.color_ramp.elements[1].color=(*color(iris_color),1)
    l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
    for s in (-1,1):
        n=Vector((s*lateral,-math.sqrt(1-lateral*lateral),.03)).normalized();c=Vector((s*x,y,z))-n*size*.22
        aligned_ell('Eye_globe',c,(size,size*.55,size*.78),iris,n,32,20)
        pupil_size=.60 if SPECIES in ('dog','rabbit','ferret') else .40
        aligned_ell('Pupil',c+n*size*.535,(size*(.12 if slit else pupil_size),size*.055,size*(.54 if slit else pupil_size)),pupil,n)
        # Upper and lower eyelid arcs make an almond opening.
        rot=Vector((0,-1,0)).rotation_difference(n)
        for up in (-1,1):
            coords=[]
            for j in range(9):
                t=math.pi*j/8
                q=Vector((size*1.04*math.cos(t),-size*.28,up*size*.76*math.sin(t)))
                coords.append(c+rot@q)
            line('Eyelid',coords,size*.085,FUR if SPECIES!='parrot' else BLACK)

def nose(loc,width,height,pink=False):
    x,y,z=loc
    if SPECIES=='dog':
        ell('Canine nose',(x,y-.015,z),(width,.048,height),NOSE,32,20)
        for s in (-1,1):
            ell('Nostril',(x+s*width*.60,y-.058,z+.003),(width*.22,.009,height*.22),BLACK,20,12,rot=(0,0,s*.16))
        line('Nasal seam',[(x,y-.064,z+.02),(x,y-.065,z-.025)],.002,BLACK)
        return
    m=mat('Nose pink','B17D78',.48) if pink else NOSE
    v=[(x-width,y+.02,z+height*.35),(x+width,y+.02,z+height*.35),(x,y+.02,z-height),
       (x-width*.92,y-.035,z+height*.35),(x+width*.92,y-.035,z+height*.35),(x,y-.04,z-height)]
    f=[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)]
    me=bpy.data.meshes.new('Nose');me.from_pydata(v,[],f);me.update()
    o=bpy.data.objects.new('Nose',me);bpy.context.collection.objects.link(o);add(o,'Nose',m)
    bpy.context.view_layer.objects.active=o;be=o.modifiers.new('Soft nose','BEVEL');be.width=height*.30;be.segments=3;bpy.ops.object.modifier_apply(modifier=be.name)
    for s in (-1,1):ell('Nostril',(x+s*width*.62,y-.037,z),(width*.22,.008,height*.15),BLACK,16,8)

def whiskers(muzzle,spread,length,count=5):
    x,y,z=muzzle
    for s in (-1,1):
        for i in range(count):
            t=i/(count-1)-.5
            reach=length*random.uniform(.78,1.17)
            p=(s*x,y+.035*abs(t),z+t*spread)
            pts=[p,(s*(x+reach*.5),y-.025,z+t*spread*2.5),(s*(x+reach),y+.03+abs(t)*.1,z+t*spread*5)]
            path('Whisker',pts,[.0009,.00065,.00015],CREAM,4,4)

def paws(x,y,z=.09,w=.09,length=.14):
    mass('Paw',(x,y,z),(w,length,z*.9))
    for dx in (-.035,0,.035):
        line('Toe crease',[(x+dx,y-length*.89,z*.8),(x+dx,y-length*.8,z*1.3)],.0025,BLACK)

def build_cat():
    mass('Ribcage',(0,.03,1.00),(.255,.48,.30))
    mass('Abdomen',(0,.35,.98),(.235,.36,.25))
    mass('Pelvis',(0,.51,1.04),(.27,.28,.31))
    mass('Shoulders',(0,-.29,1.06),(.25,.25,.34))
    mass('Neck',(0,-.46,1.25),(.185,.235,.28),(.22,0,0))
    mass('Skull',(0,-.625,1.48),(.25,.235,.25))
    for s in (-1,1):
        mass('Cheek',(s*.105,-.762,1.38),(.135,.135,.12))
        mass('Muzzle',(s*.065,-.842,1.365),(.083,.087,.064))
        mass('Shoulder muscle',(s*.18,-.27,.95),(.12,.17,.25))
        mass('Foreleg',(s*.19,-.32,.59),(.073,.082,.30))
        mass('Wrist',(s*.19,-.34,.27),(.058,.064,.17))
        paws(s*.19,-.385,.105,.084,.13)
        mass('Haunch',(s*.20,.48,.83),(.15,.21,.27))
        mass('Rear shin',(s*.205,.59,.49),(.073,.085,.23),(-.28,0,0))
        mass('Hock',(s*.21,.61,.25),(.055,.065,.16))
        paws(s*.21,.54,.105,.083,.135)
        ear('Pointed ear',(s*.15,-.55,1.61),(s*.235,-.49,1.88),.135,.05,triangular=True)
    mass('Chin',(0,-.79,1.308),(.12,.10,.055))
    tail=path('Tail',[(0,.69,1.11),(.11,.93,1.21),(.24,1.07,1.48),(.31,1.08,1.74),(.24,.98,1.88)], [.095,.083,.068,.05,.017],FUR,16,6)
    eyes(.153,-.796,1.51,.062,'A3A861',True,.48)
    nose((0,-.924,1.378),.043,.026,True)
    line('Philtrum',[(0,-.925,1.35),(0,-.916,1.317)],.0025)
    for s in (-1,1):line('Mouth',[(0,-.916,1.317),(s*.06,-.907,1.307),(s*.10,-.865,1.321)],.0025)
    whiskers((.085,-.90,1.365),.035,.24,6)

def build_dog():
    mass('Chest',(0,-.20,.98),(.285,.37,.36))
    mass('Ribcage',(0,.12,.97),(.29,.49,.31))
    mass('Abdomen',(0,.42,.98),(.235,.30,.245))
    mass('Rump',(0,.57,1.00),(.27,.28,.30))
    mass('Neck',(0,-.47,1.16),(.22,.25,.32),(.27,0,0))
    mass('Skull',(0,-.68,1.40),(.26,.275,.28))
    mass('Brow ridge',(0,-.845,1.425),(.215,.14,.13))
    mass('Muzzle bridge',(0,-.94,1.292),(.145,.255,.125))
    for s in (-1,1):
        mass('Upper lip',(s*.077,-1.03,1.23),(.105,.16,.08))
        mass('Shoulder',(s*.205,-.28,.84),(.125,.17,.26))
        mass('Foreleg',(s*.215,-.34,.50),(.075,.08,.27))
        mass('Pastern',(s*.215,-.36,.23),(.067,.07,.13))
        paws(s*.215,-.415,.115,.10,.15)
        mass('Thigh',(s*.205,.54,.77),(.15,.21,.27),(-.25,0,0))
        mass('Rear shin',(s*.22,.70,.48),(.075,.105,.22),(-.38,0,0))
        mass('Hock',(s*.23,.73,.23),(.06,.07,.14))
        paws(s*.23,.665,.11,.095,.15)
        # Dropped ears with a broad rounded lower lobe, attached behind the eye.
        ell('Dropped ear',(s*.27,-.56,1.24),(.075,.185,.31),FUR,32,24,rot=(.15,s*.13,0))
    mass('Lower jaw',(0,-.97,1.18),(.13,.20,.063))
    path('Raised tail',[(0,.76,1.11),(.10,.98,1.29),(.18,1.09,1.54),(.20,1.06,1.71)],[.09,.075,.052,.008],FUR,14,6)
    eyes(.177,-.933,1.446,.056,'493B2C',False,.42)
    nose((0,-1.205,1.30),.092,.057)
    for s in (-1,1):line('Relaxed lip',[(0,-1.184,1.205),(s*.095,-1.13,1.19),(s*.137,-.968,1.19)],.004)
    line('Nose groove',[(0,-1.22,1.257),(0,-1.19,1.209)],.003)
    whiskers((.115,-1.1,1.26),.025,.10,3)

def build_rabbit():
    mass('Rounded rump',(0,.34,.57),(.34,.44,.43))
    mass('Chest',(0,-.09,.59),(.245,.32,.34))
    mass('Neck',(0,-.29,.83),(.19,.22,.27))
    mass('Head',(0,-.45,1.05),(.235,.255,.245))
    for s in (-1,1):
        mass('Cheek',(s*.10,-.60,.975),(.145,.15,.145))
        mass('Muzzle',(s*.065,-.721,.965),(.083,.08,.067))
        mass('Haunch',(s*.245,.34,.37),(.20,.29,.28))
        paws(s*.245,.13,.095,.13,.28)
        mass('Front leg',(s*.15,-.265,.35),(.064,.073,.24))
        paws(s*.15,-.37,.078,.073,.145)
        ear('Long ear',(s*.125,-.35,1.20),(s*.235,-.17,1.94),.096,.045)
    ell('Cotton tail',(0,.752,.48),(.135,.13,.14),FUR)
    eyes(.175,-.616,1.101,.058,'332820',False,.77)
    nose((0,-.801,.984),.033,.024,True)
    line('Split upper lip',[(0,-.806,.961),(0,-.797,.924)],.0023)
    for s in (-1,1):line('Rabbit mouth',[(0,-.797,.924),(s*.049,-.773,.923)],.002)
    whiskers((.085,-.76,.98),.036,.23,6)

def build_ferret():
    mass('Long ribcage',(0,.02,.48),(.18,.49,.195))
    mass('Loin',(0,.40,.46),(.19,.34,.20))
    mass('Shoulder',(0,-.36,.48),(.17,.21,.205))
    mass('Neck',(0,-.55,.56),(.145,.22,.18))
    mass('Head',(0,-.77,.625),(.18,.235,.165))
    mass('Muzzle',(0,-.967,.555),(.105,.145,.078))
    for s in (-1,1):
        mass('Front upper leg',(s*.13,-.36,.31),(.075,.11,.15))
        mass('Foreleg',(s*.15,-.43,.16),(.047,.06,.11))
        paws(s*.15,-.49,.061,.062,.115)
        mass('Hind thigh',(s*.15,.43,.31),(.105,.15,.16))
        mass('Hind shin',(s*.17,.53,.16),(.05,.07,.115))
        paws(s*.17,.46,.064,.066,.12)
        ear('Round ear',(s*.15,-.655,.68),(s*.205,-.63,.805),.072,.038)
    path('Tapered tail',[(0,.63,.47),(.11,.90,.38),(.27,1.15,.21),(.40,1.30,.12),(.50,1.28,.105)],[.10,.087,.062,.033,.008],FUR,14,6)
    eyes(.119,-.951,.664,.036,'30291F',False,.50)
    nose((0,-1.104,.575),.043,.026,True)
    for s in (-1,1):line('Ferret mouth',[(0,-1.088,.524),(s*.055,-1.06,.518),(s*.083,-.986,.532)],.002)
    whiskers((.071,-1.035,.563),.025,.18,5)
    for s in (-1,1):
        for y in (-.49,.46):
            for dx in (-.025,0,.025):
                path('Small claw',[(s*.16+dx,y-.08,.055),(s*.16+dx,y-.12,.043),(s*.16+dx,y-.135,.025)],[.007,.005,.0008],CLAWS,6,3)

def feather(name,start,end,width,h,normal_hint=(1,0,0)):
    start=Vector(start);end=Vector(end);axis=end-start
    # Feather vanes are slightly ridged with curved, tapered tips.
    tangent=axis.normalized();side=tangent.cross(Vector(normal_hint))
    if side.length<.01:side=tangent.cross(Vector((0,0,1)))
    side.normalize();normal=side.cross(tangent).normalized()
    v=[];f=[];rows=10
    for i in range(rows+1):
        t=i/rows;c=start+axis*t+normal*.003*math.sin(math.pi*t)
        w=width*(math.sin(math.pi*(.06+.94*t))**.58)+.0004
        for u in (-1,-.45,0,.45,1):v.append(c+side*w*u+normal*.0015*(1-abs(u))*math.sin(math.pi*t))
    for i in range(rows):
        for j in range(4):
            a=i*5+j;f.append((a,a+1,a+6,a+5))
    me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    m=bpy.data.materials.get('Feather_'+h)
    if m is None:
        m=mat('Feather_'+h,h,.71)
        # Fine parallel barbs and a narrow raised shaft.
        n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
        tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=160;tex.inputs['Detail'].default_value=1
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.004
        l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    add(o,name,m)
    line('Feather shaft',[start+normal*.002,start+axis*.55+normal*.005,end],.00065,m)
    # Feather shells have thickness and consistent outward normals.
    bpy.context.view_layer.objects.active=o
    sol=o.modifiers.new('Vane thickness','SOLIDIFY');sol.thickness=.002;bpy.ops.object.modifier_apply(modifier=sol.name)
    return o

def build_parrot():
    mass('Breast',(0,.07,.78),(.245,.265,.35),(-.12,0,0))
    mass('Back',(0,.22,.92),(.23,.24,.32))
    mass('Neck',(0,-.07,1.11),(.17,.18,.22))
    mass('Head',(0,-.14,1.32),(.198,.207,.209))
    mass('Brow',(0,-.245,1.38),(.18,.12,.125))
    for s in (-1,1):
        mass('Thigh',(s*.125,.10,.48),(.09,.12,.15))
        ell('Leg scales',(s*.125,.035,.265),(.039,.043,.115),mat('Foot skin','777568',.85),18,12)
        footmat=bpy.data.materials['Foot skin']
        for k in range(4):
            direction=-1 if k<2 else 1
            side=-1 if k%2 else 1
            start=(s*.125,.015,.20)
            mid=(s*.125+side*.047,.015+direction*.10,.10)
            end=(s*.125+side*.07,.015+direction*(.20 if k<2 else .15),.075)
            path('Zygodactyl toe',[start,mid,end],[.023,.018,.010],footmat,8,5)
            path('Curved claw',[end,(end[0],end[1]+direction*.025,.06),(end[0],end[1]+direction*.035,.025)],[.012,.009,.001],CLAWS,8,4)
            for q in range(2,6):
                t=q/6;c=Vector(mid).lerp(Vector(end),t)
                line('Toe scale',[(c.x-.012,c.y,c.z+.014),(c.x,c.y-.003,c.z+.018),(c.x+.012,c.y,c.z+.014)],.0025,CLAWS)
        ell('Wing shoulder',(s*.22,.15,.93),(.075,.21,.24),FUR,24,16,rot=(-.2,s*.07,0))
        # Stacked primary flight feathers, secondaries and small coverts.
        for i in range(8):
            feather('Primary flight feather',(s*(.23+.003*i),.02+i*.032,.91-i*.011),
                    (s*(.25+.003*i),.46+i*.021,.48+i*.014),.037,['23665C','285F75','345A74'][i%3])
        for i in range(7):
            feather('Secondary feather',(s*.282,-.015+i*.048,1.01-i*.01),
                    (s*.306,.18+i*.047,.69-i*.014),.047,['458C3B','50963D','397C35'][i%3])
        for row in range(3):
            for i in range(6):
                start=(s*(.28+.009*row),-.025+i*.055,1.105-row*.084)
                end=(s*(.30+.009*row),.055+i*.055,.965-row*.080)
                feather('Wing covert',start,end,.036, ['598F35','629E3E','477E32'][(i+row)%3] if row!=2 or i<3 else 'B44732')
    # Contour plumage follows the curved breast rather than floating over it.
    for row in range(14):
        z=.56+row*.038
        for col in range(13):
            x=(col-6)*.028+(row%2)*.014
            q=1-(x/.245)**2-((z-.78)/.35)**2
            q2=1-(x/.245)**2-((z-.075-.78)/.35)**2
            if min(q,q2)<.09:continue
            y=.07-.265*math.sqrt(q)-.001
            y2=.07-.265*math.sqrt(q2)-.004
            feather('Breast contour feather',(x,y,z),(x,y2,z-.085),.018,['5F893B','608A3A','648C3D'][(row+col)%3],normal_hint=(0,-1,0))
    for i in range(7):
        x=(i-3)*.037
        feather('Tail feather',(x,.29,.63),(x*1.4,.73+(.05 if i in (2,3,4) else 0),.20),.045,'477A3A' if i%2 else '527F38',normal_hint=(0,0,1))
    # Broad horn-coloured hooked bill, with a darker cutting edge.
    bill=mat('Horn bill','66665C',.44); lower=mat('Lower bill','393C36',.50)
    path('Hooked upper bill',[(0,-.30,1.32),(0,-.405,1.30),(0,-.465,1.23),(0,-.457,1.15)],[.100,.092,.058,.008],bill,18,7)
    ell('Lower mandible',(0,-.355,1.158),(.074,.079,.047),lower,24,16)
    for s in (-1,1):
        ell('Nostril',(s*.051,-.391,1.346),(.014,.008,.009),BLACK,16,10)
        # Natural bare eye ring and a small orange iris, facing sideways.
        n=Vector((s*.9,-.435,.03)).normalized();c=Vector((s*.166,-.237,1.363))
        skin=mat('Bare eye skin','CEC9AD',.83)
        aligned_ell('Orbital skin',c,(.040,.012,.042),skin,n)
    eyes(.173,-.244,1.368,.031,'C4973E',False,.90)
    for s in (-1,1):line('Bill seam',[(s*.065,-.393,1.203),(s*.086,-.356,1.217)],.002,BLACK)

def coat_at(p):
    x,y,z=p;ax=abs(x)
    grain=(math.sin(x*39+y*27+z*43)+math.sin(x*81-y*47+z*35))*.5
    if SPECIES=='cat':
        base=color('8F8673');dark=color('3B3831');light=color('D4CCB7')
        wave=math.sin(y*38+z*12+math.sin(z*21+x*7)*1.5)
        stripe=smooth(.40,.86,wave)*(1-smooth(.17,.26,ax)*.15)
        if y<-.49 and z>1.20:
            stripe=smooth(.25,.83,math.sin(x*70+z*16+math.sin(z*25)))*.85
            base=mix(base,light,smooth(-.74,-.89,y)*.85)
        if y>.72:stripe=smooth(.15,.70,math.sin((z+y)*32))
        base=mix(base,dark,stripe*.90)
        belly=(1-smooth(.68,.91,z))*(1-smooth(.08,.21,ax))
        base=mix(base,light,belly*.75)
        if y<-.74 and z<1.34 and z>1.25:base=mix(base,light,.9)
        return mix(base,color('C0B499'),.08+.04*grain)
    if SPECIES=='dog':
        tan=color('AD7847');white=color('E4DDCA');black=color('292825')
        base=tan
        saddle=smooth(-.12,.03,y)*(1-smooth(.49,.69,y))*smooth(.80,.99,z)
        base=mix(base,black,saddle)
        chest=(1-smooth(-.48,-.18,y))*(1-smooth(1.00,1.16,z))
        socks=1-smooth(.33,.59,z)
        base=mix(base,white,max(chest,socks))
        if y<-.80:
            blaze=(1-smooth(.035,.075,ax))*(1-smooth(1.55,1.64,z))
            muzzle=1-smooth(1.29,1.38,z)
            base=mix(base,white,max(blaze,muzzle))
        if y>.88:base=mix(base,white,smooth(1.46,1.60,z))
        return mix(base,color('8E6B4C'),.025+.02*grain)
    if SPECIES=='rabbit':
        base=color('8C877E');light=color('D6CFC2');dark=color('655F58')
        base=mix(base,dark,.2+.14*grain)
        base=mix(base,light,(1-smooth(.38,.65,z))*.7)
        if y<-.57:base=mix(base,light,(1-smooth(1.01,1.10,z))*.75)
        if z>1.25:base=mix(base,dark,smooth(1.63,1.91,z)*.6)
        if y>.65:base=mix(base,light,.85)
        return base
    if SPECIES=='ferret':
        base=color('B7AA88');dark=color('493B2C');light=color('D7D0B9')
        base=mix(base,dark,smooth(.48,.64,z)*.35 if y>-.5 else 0)
        base=mix(base,dark,(1-smooth(.20,.35,z))*.90)
        if y>.70:base=mix(base,dark,.8)
        if y<-.57:
            base=mix(base,light,.82)
            eye_mask=math.exp(-((z-.661)/.041)**2)*smooth(.04,.083,ax)*(1-smooth(-.79,-.62,y))
            base=mix(base,dark,eye_mask*.98)
            cap=smooth(.72,.79,z)*(1-smooth(-.72,-.56,y))
            base=mix(base,dark,cap*.55)
        return mix(base,dark,.04+.025*grain)
    # Blue-fronted Amazon parrot: green body, yellow face and turquoise forehead.
    base=color('558B39');base=mix(base,color('789F42'),smooth(.08,-.23,y)*.35)
    if z>1.15:
        yellow=smooth(-.10,-.25,y)*smooth(1.16,1.32,z)
        base=mix(base,color('D5BB45'),yellow)
        blue=smooth(1.38,1.48,z)*(1-smooth(.05,.15,ax))*smooth(-.10,-.27,y)
        base=mix(base,color('398E9A'),blue)
    return mix(base,color('345B2B'),.06+.05*grain)

{'cat':build_cat,'dog':build_dog,'rabbit':build_rabbit,'ferret':build_ferret,'parrot':build_parrot}[SPECIES]()
body=fuse()
# Bake natural colour boundaries from world-space coat painting.
for o in parts:
    if FUR not in list(o.data.materials):continue
    attr=o.data.color_attributes.new(name='Coat',type='FLOAT_COLOR',domain='POINT')
    for vertex,entry in zip(o.data.vertices,attr.data):
        c=color('966039') if SPECIES=='dog' and o.name.startswith('Dropped ear') else coat_at(o.matrix_world@vertex.co)
        entry.color=(*c,1)

bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();animal=bpy.context.object;animal.name=NAME
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
# Orient shells consistently before triangulation and tangent-space baking.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
tri=animal.modifiers.new('Triangulate','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name)
fur_faces=[poly.index for poly in animal.data.polygons if animal.data.materials[poly.material_index]==FUR]
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=.5,correct_aspect=True)
bpy.ops.object.mode_set(mode='OBJECT')
scene=bpy.context.scene;scene.render.bake.margin=8
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
images={}
original_mats=list(animal.data.materials)
for kind,size in [('BaseColor',4096),('Normal',2048),('Roughness',1024)]:
    img=bpy.data.images.new(NAME+'_'+kind,width=size,height=size,alpha=False)
    img.colorspace_settings.name='sRGB' if kind=='BaseColor' else 'Non-Color'
    for m in original_mats:
        n=m.node_tree.nodes
        for node in n:node.select=False
        target=n.new('ShaderNodeTexImage');target.image=img;target.select=True;n.active=target
    print('BAKE_START',NAME,kind,flush=True)
    bpy.ops.object.bake(type={'BaseColor':'DIFFUSE','Normal':'NORMAL','Roughness':'ROUGHNESS'}[kind])
    img.filepath_raw=str(OUT/(NAME+'_'+kind+'.png'));img.file_format='PNG';img.save()
    images[kind]=img

pbr=bpy.data.materials.new(NAME+'_PBR');pbr.use_nodes=True;n=pbr.node_tree.nodes;l=pbr.node_tree.links;p=n.get('Principled BSDF')
for kind,img in images.items():
    t=n.new('ShaderNodeTexImage');t.image=img;t.label=kind
    if kind=='Normal':
        normal=n.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.55
        l.new(t.outputs['Color'],normal.inputs['Color']);l.new(normal.outputs[0],p.inputs['Normal'])
    else:l.new(t.outputs['Color'],p.inputs['Base Color' if kind=='BaseColor' else 'Roughness'])
animal.data.materials.clear();animal.data.materials.append(pbr)
for poly in animal.data.polygons:poly.material_index=0

# Short tapered guard hairs are real geometry and survive FBX export.
# They use a dedicated colour atlas instead of hundreds of tiny baked UV islands.
fur_object=None
if SPECIES!='parrot':
    import bisect
    from array import array
    source=[];cumulative=[];total=0
    for idx in fur_faces:
        poly=animal.data.polygons[idx]
        if poly.area<1e-12:continue
        source.append(poly);total+=poly.area;cumulative.append(total)
    count=50000 if SPECIES in ('cat','rabbit') else 40000 if SPECIES=='ferret' else 35000
    verts=[];faces=[];hair_indices=[];pixels=array('f',[.5,.5,.5,1])*(512*512)
    def srgb(v):return 12.92*v if v<=.0031308 else 1.055*max(0,v)**(1/2.4)-.055
    for i in range(count):
        poly=source[bisect.bisect_left(cumulative,random.random()*total)]
        vs=[animal.data.vertices[j] for j in poly.vertices]
        a=math.sqrt(random.random());b=random.random();weights=(1-a,a*(1-b),a*b)
        root=sum((v.co*w for v,w in zip(vs,weights)),Vector())
        normal=sum((v.normal*w for v,w in zip(vs,weights)),Vector()).normalized()
        # Groom down the flanks, back along the spine and away from the face.
        flow=Vector((root.x*.65,.60,-.5))
        if root.y<-.50:flow=Vector((root.x*1.6,.15,-.6))
        if root.z>1.50:flow=Vector((root.x*.3,.35,.6))
        tangent=flow-normal*flow.dot(normal)
        if tangent.length<.001:tangent=normal.cross(Vector((1,0,0)))
        tangent.normalize()
        length=random.uniform(.012,.026) if SPECIES in ('rabbit','ferret') else random.uniform(.007,.018)
        if root.y<-.6:length*=.52
        if root.z<.18:length*=.45
        direction=(normal*.55+tangent*.83).normalized()
        side=direction.cross(Vector((0,0,1)))
        if side.length<.01:side=direction.cross(Vector((1,0,0)))
        side.normalize();other=direction.cross(side).normalized()
        thick=random.uniform(.00065,.00115)
        start=len(verts)
        for ring in range(3):
            t=ring/2;center=root+direction*length*t+normal*length*.12*t*t
            radius=thick*(1-t*.94)
            for k in range(3):verts.append(center+radius*(side*math.cos(k*math.tau/3)+other*math.sin(k*math.tau/3)))
        for ring in range(2):
            for k in range(3):
                j=start+ring*3+k;nextj=start+ring*3+(k+1)%3
                faces.append((j,nextj,nextj+3,j+3));hair_indices.append(i)
        shade=random.uniform(.67,1.19)
        ca=animal.data.color_attributes.get('Coat')
        sampled=sum((Vector(ca.data[v.index].color[:3])*w for v,w in zip(vs,weights)),Vector()) if ca else coat_at(root)
        rgb=tuple(max(0,min(1,srgb(v*shade))) for v in sampled)
        px=(i%256)*2;py=(i//256)*2
        for dy in range(2):
            for dx in range(2):
                off=((py+dy)*512+px+dx)*4
                pixels[off:off+4]=array('f',(*rgb,1))
    mesh=bpy.data.meshes.new(NAME+'_Fur');mesh.from_pydata(verts,[],faces);mesh.update()
    uv=mesh.uv_layers.new(name='UVMap')
    for poly,idx in zip(mesh.polygons,hair_indices):
        for loop in poly.loop_indices:uv.data[loop].uv=((idx%256+.5)/256,(idx//256+.5)/256)
        poly.use_smooth=True
    fur_object=bpy.data.objects.new(NAME+'_GuardHairs',mesh);bpy.context.collection.objects.link(fur_object)
    fur_image=bpy.data.images.new(NAME+'_FurColor',width=512,height=512,alpha=False)
    fur_image.pixels.foreach_set(pixels);fur_image.filepath_raw=str(OUT/(NAME+'_FurColor.png'));fur_image.file_format='PNG';fur_image.save();fur_image.pack()
    fm=mat(NAME+'_Fur','A09070',.94)
    node=fm.node_tree.nodes.new('ShaderNodeTexImage');node.image=fur_image
    fm.node_tree.links.new(node.outputs['Color'],fm.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    fm.node_tree.nodes.get('Principled BSDF').inputs['Sheen Weight'].default_value=.3
    mesh.materials.append(fm);fur_object.select_set(True)

scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.ops.export_scene.fbx(filepath=str(OUT/(NAME+'.fbx')),use_selection=True,object_types={'MESH'},
    apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',
    mesh_smooth_type='FACE',use_tspace=True,add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
for img in images.values():img.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(NAME+'.blend')))
info={'name':NAME,'species':SPECIES,'triangles':len(animal.data.polygons)+(len(fur_object.data.polygons)*2 if fur_object else 0),'vertices':len(animal.data.vertices)+(len(fur_object.data.vertices) if fur_object else 0),
      'dimensions':list(animal.dimensions),'mesh_count':2 if fur_object else 1,'texture_resolution':4096,'rigged':False,'animated':False,
      'maps':['BaseColor','Normal','Roughness'],'roblox_studio_tested':False}
(OUT/'asset_info.json').write_text(json.dumps(info,indent=2))

# Render the exact exported material, including the baked normal and roughness maps.
floor=mat('Studio floor','565B58',.9)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0));bpy.context.object.data.materials.append(floor)
world=scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.39,.43,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.5
for loc,power,size in [((-3,-4,5),420,3),((4,-1,3),250,3),((0,4,4),550,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size
    o.rotation_euler=(Vector((0,0,.8))-o.location).to_track_quat('-Z','Y').to_euler()
target=Vector((0,-.02,.95 if SPECIES in ('cat','rabbit','dog') else .78 if SPECIES=='parrot' else .46))
bpy.ops.object.camera_add(location=(3,-4.6,2.5 if SPECIES!='ferret' else 1.65));camera=bpy.context.object
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO'
camera.data.ortho_scale=2.65 if SPECIES in ('cat','dog') else 2.30 if SPECIES=='rabbit' else 2.05 if SPECIES=='parrot' else 2.50
scene.camera=camera;scene.cycles.samples=48;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(OUT/(NAME+'_Preview.png'));bpy.ops.render.render(write_still=True)
print('ASSET_FINISHED',json.dumps(info),flush=True)
