import trimesh, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
O='out/'
C={'rail':(0.30,0.36,0.26),'roof':(0.52,0.62,0.40),'flap':(0.70,0.76,0.52),'bezel':(0.22,0.22,0.25),'screen':(0.08,0.14,0.24)}
unit=trimesh.load(O+'unit.stl',force='mesh')
bezel=unit.slice_plane([0,0,0.5],[0,0,-1], cap=True)   # only the bezel slab z<=0.5
screen=trimesh.load(O+'screen.stl',force='mesh')
def load(n): return trimesh.load(O+n+'.stl', force='mesh')
states={
 'open':   ['rail_R','rail_L','roof_R','roof_L','flap_R','flap_L'],
 'folded': ['rail_R','rail_L','roof_R','roof_L','flap_R_folded','flap_L_folded'],
 'closed': ['rail_R','rail_L','roof_R_closed','roof_L_closed','flap_R_closed','flap_L_closed'],
}
Lt=np.array([0.3,-0.5,0.8]); Lt/=np.linalg.norm(Lt)   # plot coords (X, Z, Y)
def draw(ax, names, elev, azim, lim=None):
    tris=[]; cols=[]
    items=[('bezel',bezel),('screen',screen)]+[(n,load(n)) for n in names]
    for n,m in items:
        vv,ff=trimesh.remesh.subdivide_to_size(m.vertices,m.faces,max_edge=6,max_iter=12); m=trimesh.Trimesh(vv,ff,process=False)
        v=m.vertices[:,[0,2,1]]; tri=v[m.faces]; nrm=m.face_normals[:,[0,2,1]]
        shade=0.30+0.70*np.clip(np.abs(nrm@Lt),0,1)
        base=np.array(C[n.split('_')[0]])
        tris.append(tri); cols.append(np.clip(base[None,:]*shade[:,None],0,1))
    pc=Poly3DCollection(np.concatenate(tris), facecolors=np.concatenate(cols), edgecolors='none', linewidths=0)
    ax.add_collection3d(pc)
    lx,ly,lz = lim or ((-165,165),(-140,10),(-60,110))
    ax.set_xlim(*lx); ax.set_ylim(*ly); ax.set_zlim(*lz)
    ax.set_box_aspect((lx[1]-lx[0], ly[1]-ly[0], lz[1]-lz[0]))
    ax.view_init(elev=elev, azim=azim, vertical_axis='z'); ax.set_axis_off()
fig=plt.figure(figsize=(22,8))
for i,(st,title) in enumerate([('open','1. Раскрыт: крыша + боковины, штифты в фиксаторах'),
                               ('folded','2. Боковины сложены под крышу'),
                               ('closed','3. Крыша опущена на экран')]):
    ax=fig.add_subplot(1,3,i+1,projection='3d'); draw(ax, states[st], 18, -58); ax.set_title(title, fontsize=14)
plt.subplots_adjust(left=0,right=1,top=0.93,bottom=0,wspace=0); plt.savefig('fs9_visor_states.png', dpi=85)
fig=plt.figure(figsize=(22,8))
ax=fig.add_subplot(1,3,1,projection='3d'); draw(ax, states['open'], 2, -90); ax.set_title('Раскрыт — спереди', fontsize=14)
ax=fig.add_subplot(1,3,2,projection='3d'); draw(ax, states['open'], 0, 0); ax.set_title('Раскрыт — сбоку', fontsize=14)
ax=fig.add_subplot(1,3,3,projection='3d'); draw(ax, ['rail_R','roof_R','flap_R'], 12, -30, ((60,165),(-60,10),(-45,100))); ax.set_title('Правый угол: шарниры и фиксатор', fontsize=14)
plt.subplots_adjust(left=0,right=1,top=0.93,bottom=0,wspace=0); plt.savefig('fs9_visor_views.png', dpi=85)
print('ok')
