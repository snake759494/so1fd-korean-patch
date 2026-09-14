import sys,json
sys.path.insert(0,'work/full_patch');import build_name_fonts as n
leaf=n.tree.find(n.tree.parse(n.fe.p.read(2330),'2330'),'2330!/1');im,at=n.small.tim(leaf.data);pat=leaf.data[at+2048:at+3072];hits=[]
for m in range(n.fe.p.count):
 if n.fe.p.sizes[m]>5000000:continue
 t=n.tree.parse(n.fe.p.read(m),str(m))
 for x in n.tree.walk(t):
  if x.kids:continue
  o=x.data.find(pat)
  if o>=0:
   print(m,x.path,o,len(x.data),flush=True);hits.append(dict(member=m,path=x.path,offset=o,size=len(x.data)))
 if m%1000==0:print('scanned',m,flush=True)
(n.P/'review09/battle_atlas_search.json').write_text(json.dumps(hits,indent=1))
