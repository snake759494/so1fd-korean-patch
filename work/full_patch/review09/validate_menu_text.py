"""Compare built menu/table glyphs and controls to the reviewed target, not just counts."""
import json,sys,struct,collections,re
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
import build_menus as b
from codec import tokens
cache=b.load_cache();rows=json.loads((P/'extras_source.json').read_text(encoding='utf8'))
review={b.norm(k):b.canonicalize(v) if hasattr(b,'canonicalize') else v for k,v in json.loads((P/'menu_review09.json').read_text(encoding='utf8')).items()}
def chunks(blob,m):
 if m==3320:
  pos=[8,struct.unpack_from('<I',blob,4)[0]]
  chain=[(blob[o+3],*struct.unpack_from('<III',blob,o+4),o) for o in pos]
 else:chain=b.fe.slz.parse_chain(blob)
 return [b.fe.slz.decompress_payload(blob[o+16:o+16+c],md,u) for md,c,u,_,o in chain]
def glyphs(raw,font):
 n,h=struct.unpack_from('<II',font)
 result=[]
 for kind,bb,v in tokens(raw,list(range(n)),{}):
  if kind!='glyph':continue
  code=bb[0] if len(bb)==1 else (bb[0]&127)+128*bb[1]
  assert 1<=code<=n
  result.append(font[8+n+(code-1)*24:8+n+code*24])
 return result
def controls(raw,font):
 n=struct.unpack_from('<I',font)[0]
 return [bb.hex() for k,bb,v in tokens(raw,list(range(n)),{}) if k=='control']
good=[];errors=[];gaps={};widths=[]
for m in sorted({x['member'] for x in rows if x['kind'] in ('menu','table')}):
 selected=[x for x in rows if x['member']==m and x['kind'] in ('menu','table')]
 kind=selected[0]['kind'];original=b.fe.p.read(m);patched=(P/f'members/member{m}_korean.bin').read_bytes()
 if kind=='menu':
  rt=b.fe.extract.parse_resource(original,m);pt=b.fe.extract.parse_resource(patched,m)
  of=b.tree.find(rt,f'{m}!/1').data;nf=b.tree.find(pt,f'{m}!/1').data
  groups={g:b.tree.find(pt,f'{m}!/0/{g}').data.split(b'\0') for g in {x['group'] for x in selected}}
 else:
  ot,of,*_=chunks(original,m);nt,nf,*_=chunks(patched,m)
 ids=b.fe.extract.g['banks'][next(c['key'] for c in b.fe.extract.cat if c['member']==m and(kind=='table' or c['path']==f'{m}/1' or m==2353))]['ids']
 for i,row in enumerate(selected):
  if kind=='menu' and row['group']==1 and len(groups[1])>50:continue
  raw=bytes.fromhex(row['hex'])
  if kind=='menu':actual=groups[row['group']][row['index']]
  else:
   at=struct.unpack_from('<H',nt,i*4+2)[0];actual=nt[at:nt.index(b'\0',at)]
  seg=None if kind=='menu' and row['group']==0 else b.translate(raw,ids,cache)
  if seg is None and kind=='menu' and row['id'] in b.menu_build.T and b.menu_build.T[row['id']]!=row['jp']:
   target=b.menu_build.T[row['id']]
   seg=[('raw',bytes.fromhex(v[1:-1]),None) if v.startswith('{') else ('ko',b'',v) for v in re.findall(r'\{[0-9a-f]+\}|[^{}]+',target)]
  expected=glyphs(raw,of) if seg is None else [bitmap for k,bb,s in seg for bitmap in ([b.glyph(c) for c in s] if k=='ko' else glyphs(bb,of))]
  # wrap_fixed may move/remove spaces at line edges.
  strip=lambda xs:[x for x in xs if any(x)]
  if strip(expected)!=strip(glyphs(actual,nf)):errors.append(dict(id=row['id'],type='glyph content mismatch'))
  if controls(raw,of)!=controls(actual,nf):errors.append(dict(id=row['id'],type='control mismatch'))
  if not(kind=='menu' and row['group']==0):
   for k,bb,s in b.parts(raw,ids,field=False):
    if k=='text' and b.JP.search(s) and b.norm(s) not in review:gaps[s]=cache.get(b.norm(s))
  n=struct.unpack_from('<I',nf)[0];line=0;maximum=0
  for k,bb,v in tokens(actual,list(range(n)),{}):
   if k=='glyph':
    code=bb[0] if len(bb)==1 else(bb[0]&127)+128*bb[1];line+=nf[7+code]
   elif k=='control' and v==0x4000:maximum=max(maximum,line);line=0
  maximum=max(maximum,line)
  if maximum>456:widths.append(dict(id=row['id'],pixels=maximum,jp=row['jp']))
  good.append(row['id'])
result=dict(audited=len(good),errors=errors,unreviewed_segments=gaps,over_screen_width=widths)
(P/'review09/menu_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=1),encoding='utf8')
print(json.dumps(dict(audited=len(good),errors=errors[:12],error_count=len(errors),unreviewed_segments=gaps,over_screen_width=len(widths)),ensure_ascii=False,indent=1))
if errors or gaps:raise SystemExit(1)
