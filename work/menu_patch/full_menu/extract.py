from pathlib import Path
import json,pickle,sys,struct
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'work/tools'))
import so1pack,tree
g=pickle.load(open(ROOT/'work/glyphs.pkl','rb'))
cat=json.loads((ROOT/'work/banks.json').read_text())
def decode(b,ids):
 out='';i=0
 while i<len(b):
  v=b[i];i+=1
  if v>=128:
   if i>=len(b):out+='{BAD}';break
   v=(v&127)+b[i]*128;i+=1
  if v>=0x4000:
   raw=bytes([(v&127)|128,v>>7])
   if v in [0x4006,0x400c] and i<len(b):raw+=b[i:i+1];i+=1
   out+='{'+raw.hex()+'}'
  elif 0<v<=len(ids):out+=g['label'].get(ids[v-1],'?')
  else:out+='?'
 return out
def parse_resource(data,m):
 t=tree.parse(data,str(m))
 if m==2353:
  n=t.kids[0];u=n.data;first=struct.unpack_from('<I',u)[0];offs=list(struct.unpack_from(f'<{first//4}I',u));kids=[];slots=[]
  for i,a in enumerate(offs):
   if not a:continue
   b=next((v for v in offs[i+1:] if v),len(u))
   if a==b:continue
   kids.append(tree.parse(u[a:b],f'{m}!/{i}'));slots.append((a,b))
  t.kids[0]=tree.Node('offtable',u,kids,slots,f'{m}!')
 return t
def extract(m,p):
 t=parse_resource(p.read(m),m);bank=next((c for c in cat if c['member']==m and (c['path']==f'{m}/1' or m==2353)),None)
 if not bank:return None
 ids=g['banks'][bank['key']]['ids'];rows=[]
 for n in tree.walk(t):
  if n.kind!='raw' or not n.path.startswith(f'{m}!/0/'):continue
  a=n.data.split(b'\0')
  while a and not a[-1]:a.pop()
  for i,b in enumerate(a):
   rows.append({'id':f"{m}:{n.path.split('/')[-1]}:{i}",'group':int(n.path.split('/')[-1]),'index':i,'jp':decode(b,ids),'hex':b.hex()})
 return {'member':m,'font_count':len(ids),'rows':rows}
if __name__=='__main__':
 p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin')
 for m in range(2328,2370):
  r=extract(m,p)
  if r:
   (Path(__file__).parent/f'{m}.json').write_text(json.dumps(r,ensure_ascii=False,indent=1),encoding='utf-8')
   print(m,r['font_count'],len(r['rows']),' | '.join(x['jp'] for x in r['rows'] if x['group'] in [1,2,3] and len(x['jp'])>2)[:220])
