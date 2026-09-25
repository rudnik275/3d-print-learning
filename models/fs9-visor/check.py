import trimesh, numpy as np, itertools, math
from trimesh.transformations import rotation_matrix as R
O='out/'
def L(n): return trimesh.load(O+n+'.stl', force='mesh')
# geometry constants from the model print
YH,ZH,XF,YF = 83.97,-28.0,150.38,80.87
unit=L('unit')
parts={n:L(n) for n in ['rail_R','rail_L','roof_R','roof_L','flap_R','flap_L']}
def vol(a,b):
    try:
        i=trimesh.boolean.intersection([a,b], engine='manifold')
        return 0.0 if i.is_empty else abs(i.volume)
    except Exception as e: return f'err {e}'
def report(tag, meshes):
    bad=[]
    for (na,a),(nb,b) in itertools.combinations(meshes.items(),2):
        if na.split('_')[0]==nb.split('_')[0]=='rail' : pass
        if not a.bounds_overlap(b) if hasattr(a,'bounds_overlap') else False: continue
        v=vol(a,b)
        if isinstance(v,str) or v>0.5: bad.append((na,nb,v))
    print(tag, 'OK' if not bad else bad)
def rot_flap(m, side, ang):  # ang 0=deployed, 90=folded
    s = -1 if side=='R' else 1
    x = XF if side=='R' else -XF
    return m.copy().apply_transform(R(math.radians(s*ang),[0,0,1],[x,YF,0]))
def rot_roof(m, ang):  # ang 0=open, 90=closed
    return m.copy().apply_transform(R(math.radians(-ang),[1,0,0],[0,YH,ZH]))
unitm = unit
# 1) static open with unit
report('open', {'unit':unitm, **parts})
# 2) flap sweep 0..90 (roof open)
for a in [15,30,45,60,75,90]:
    ms={'unit':unitm,'rail_R':parts['rail_R'],'rail_L':parts['rail_L'],'roof_R':parts['roof_R'],'roof_L':parts['roof_L'],
        'flap_R':rot_flap(parts['flap_R'],'R',a),'flap_L':rot_flap(parts['flap_L'],'L',a)}
    report(f'flap {a}', ms)
# 3) roof sweep 0..90 with folded flaps
for a in [-20,15,30,45,60,75,90,95]:
    ms={'unit':unitm,'rail_R':parts['rail_R'],'rail_L':parts['rail_L'],
        'roof_R':rot_roof(parts['roof_R'],a),'roof_L':rot_roof(parts['roof_L'],a),
        'flap_R':rot_roof(rot_flap(parts['flap_R'],'R',90),a),'flap_L':rot_roof(rot_flap(parts['flap_L'],'L',90),a)}
    report(f'roof {a}', ms)
# 4) roof must be locked when flaps deployed: try rotating roof +-3 deg with flaps deployed
for a in [-3,3]:
    ms={'rail_R':parts['rail_R'],'roof_R':rot_roof(parts['roof_R'],a),'flap_R':rot_roof(parts['flap_R'],a)}
    report(f'lock test roof {a} (expect flap_R x rail_R clash)', ms)
