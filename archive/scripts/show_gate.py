import json, sys
r=json.load(open(sys.argv[1]))
print('excluded',round(r['excluded_fraction'],4),'writing face',r['writing_face'])
for f in ('top','bot'):
    x=r['faces'][f]; print(f,{k:(round(v,4) if isinstance(v,float) else v) for k,v in x.items() if not k.startswith('u')})
    for u in ('u05','u1','u2'):
        us=x[u]; T=[a for a in us if a['cls']=='text']; B=[a for a in us if a['cls']=='blank']
        ms=lambda L,k: round(sum(a[k] for a in L)/len(L),4) if L else None
        print('  ',u,'n',len(us),'text',len(T),'blank',len(B),'mean_s text/blank',ms(T,'mean_s'),ms(B,'mean_s'),'diff',ms(T,'mean_diff'),ms(B,'mean_diff'))
