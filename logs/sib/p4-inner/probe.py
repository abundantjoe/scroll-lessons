import json,urllib.request,numpy as np
B="https://vesuvius-challenge-open-data.s3.amazonaws.com/PHercParis4/representations/predictions/"
a=json.load(open('umb.json'));U=np.array(sorted([[p['z'],p['x'],p['y']] for p in a['control_points']]))
prods={
 'surface_m7_L2':('surfaces/20260411134726-surface-20260413222639-surface-m7-L2-th0.2.zarr/0',4),
 'surface_recto_L0_lvl2':('surfaces/20260411134726-surface-20260413141734-surface-recto-2um-ps256-L0-th0.45.zarr/2',4),
 'lasagna_cos_L3':('lasagna/20260411134726-lasagna-20260419180421-L2/PHercParis4-20260411134726-las-sd2-5b17ff6c_cos.ome.zarr/3',8),
 'fibers0915_presence_L3':('fibers/20260411134726-fibers-20260915212757-L1/PHercParis4-20260411134726-las-sd1-7ff0ce6c_presence.ome.zarr/3',8),
 'fibers0801_presence_L3':('fibers/20260411134726-fibers-20260801084232-L1/PHercParis4-20260411134726-las-sd1-d74cca79_presence.ome.zarr/3',8),
 'ink3d_lvl2':('ink-3d/20260411134726-ink3d-20260428123845-v3-78k-fullsup.zarr/2',4),
}
def head(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,method='HEAD'));return int(r.headers['Content-Length'])
    except Exception as e: return str(getattr(e,'code',e))
out={}
for name,(p,f) in prods.items():
    za=json.loads(urllib.request.urlopen(B+p+'/.zarray').read());sep=za.get('dimension_separator','.');ch=za['chunks']
    res={'zarray_shape':za['shape'],'chunks':ch,'dtype':za['dtype'],'probes':[]}
    for zmm in (50,80,110,140,160):
        z=zmm/2.4e-3;ux=np.interp(z,U[:,0],U[:,1]);uy=np.interp(z,U[:,0],U[:,2])
        for rmm,ang in ((0,0),(0.75,0),(0.75,180),(5,90),(20,0)):
            x=ux+rmm/2.4e-3*np.cos(np.radians(ang));y=uy+rmm/2.4e-3*np.sin(np.radians(ang))
            idx=[int(v/f//c) for v,c in zip((z,y,x),ch)]
            res['probes'].append({'z_mm':zmm,'r_mm':rmm,'ang':ang,'chunk':idx,'bytes':head(B+p+'/'+sep.join(map(str,idx)))})
    out[name]=res
    print(name,ch,[(q['z_mm'],q['r_mm'],q['bytes']) for q in res['probes']])
json.dump(out,open('probe.json','w'),indent=1)
