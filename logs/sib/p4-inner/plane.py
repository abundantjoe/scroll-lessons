import numpy as np,urllib.request,concurrent.futures as cf,time
B="https://vesuvius-challenge-open-data.s3.amazonaws.com/PHercParis4/volumes/20260608103018-1.129um-0.2m-78keV-masked.zarr/0/"
SH=(59969,36006,32354);C=128
def getplane_chunk(cz,zi,cy,cx):
    u=f"{B}{cz}/{cy}/{cx}";off=zi*C*C
    for a in range(4):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={'Range':f'bytes={off}-{off+C*C-1}'}),timeout=60)
            return np.frombuffer(r.read(),np.uint8).reshape(C,C)
        except urllib.error.HTTPError as e:
            if e.code==404: return None
        except Exception: time.sleep(1+a)
    raise RuntimeError(u)
def plane(z,y0,y1,x0,x1,workers=48):
    """z-plane z (1.129 vox), y in [y0,y1), x in [x0,x1); returns array, missing chunks -> 0, plus mask of present"""
    cz,zi=divmod(z,C);cys=range(y0//C,(y1-1)//C+1);cxs=range(x0//C,(x1-1)//C+1)
    out=np.zeros(((len(cys))*C,(len(cxs))*C),np.uint8);pres=np.zeros_like(out,bool)
    jobs={}
    with cf.ThreadPoolExecutor(workers) as ex:
        for i,cy in enumerate(cys):
            for j,cx in enumerate(cxs): jobs[ex.submit(getplane_chunk,cz,zi,cy,cx)]=(i,j)
        for f in cf.as_completed(jobs):
            i,j=jobs[f];a=f.result()
            if a is not None: out[i*C:(i+1)*C,j*C:(j+1)*C]=a;pres[i*C:(i+1)*C,j*C:(j+1)*C]=True
    oy=cys[0]*C;ox=cxs[0]*C
    return out[y0-oy:y1-oy,x0-ox:x1-ox],pres[y0-oy:y1-oy,x0-ox:x1-ox]
if __name__=='__main__':
    t=time.time();a,p=plane(30000,17000,20200,14000,17200);print(time.time()-t,'s',a.shape,p.mean(),a.mean())
