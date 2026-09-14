from font_bank import *
import build as menu_build
import tree
def make_menu(m,cache):
 # Rebuild from retail so old hand overrides cannot hide newly reviewed rows.
 orig=fe.p.read(m);root=fe.extract.parse_resource(orig,m)
 fontnode=tree.find(root,f'{m}!/1');font=fontnode.data
 rows=[x for x in json.loads((P/'extras_source.json').read_text(encoding='utf8')) if x['kind']=='menu' and x['member']==m]
 ids=fe.extract.g['banks'][next(c['key'] for c in fe.extract.cat if c['member']==m and(c['path']==f'{m}/1' or m==2353))]['ids']
 raws={};groups={};changes={}
 for row in rows:
  g=row['group'];i=row['index']
  if g not in groups:groups[g]=tree.find(root,f'{m}!/0/{g}').data.split(b'\0')
  raws[row['id']]=groups[g][i]
  if g==0 or (g==1 and len(groups[g])>50):continue
  assert raws[row['id']]==bytes.fromhex(row['hex'])
  s=translate(bytes.fromhex(row['hex']),ids,cache)
  if s is None and row['id'] in menu_build.T and menu_build.T[row['id']]!=row['jp']:
   target=menu_build.T[row['id']]
   assert re.findall(r'\{[0-9a-f]+\}',target)==re.findall(r'\{[0-9a-f]+\}',row['jp'])
   s=[('raw',bytes.fromhex(v[1:-1]),None) if v.startswith('{') else ('ko',b'',v) for v in re.findall(r'\{[0-9a-f]+\}|[^{}]+',target)]
  if s:changes[row['id']]=s
 newfont,newraw=remake(font,raws,changes,reserve=0 if m==2329 else 260,trim=m==2329)
 repl={fontnode.path:newfont}
 # Keep previously translated embedded texture assets, independently of text.
 legacy=ROOT/'work/menu_patch/full_menu'/f'member{m}_korean.bin'
 if legacy.exists():
  legacy_root=fe.extract.parse_resource(legacy.read_bytes(),m)
  for child in root.kids[0].kids[2:]:
   previous=tree.find(legacy_root,child.path)
   if previous is not None and previous.data!=child.data:repl[child.path]=previous.data
 for row in rows:groups[row['group']][row['index']]=newraw[row['id']]
 for g,ss in groups.items():repl[f'{m}!/0/{g}']=b'\0'.join(ss)
 inner=menu_build.repack(root.kids[0],repl)
 mode,payload=min(((md,fe.slz.compress_payload(inner,md)) for md in [1,2]),key=lambda x:len(x[1]))
 if len(payload)+16>len(orig):raise ValueError(('menu allocation overflow',m,len(payload)+16,len(orig)))
 comp=max(struct.unpack_from('<I',orig,4)[0],len(payload));out=(b'SLZ'+bytes([mode])+struct.pack('<III',comp,len(inner),0)+payload).ljust(len(orig),b'\0')
 assert len(out)==len(orig) and fe.slz.decompress(out)==inner
 (P/'members'/f'member{m}_korean.bin').write_bytes(out)
 return dict(member=m,translated=len(changes),font=struct.unpack_from('<I',newfont)[0])
if __name__=='__main__':
 cache=load_cache()
 result=[]
 for m in sorted({x['member'] for x in json.loads((P/'extras_source.json').read_text(encoding='utf8')) if x['kind']=='menu'}):
  try:r=make_menu(m,cache)
  except Exception as e:r=dict(member=m,error=repr(e))
  result.append(r);print(r,flush=True)
 (P/'menu_build_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=1),encoding='utf8')
