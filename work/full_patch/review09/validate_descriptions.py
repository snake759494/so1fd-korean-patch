"""Audit every rebuilt description against reviewed glyphs and original controls."""
import json,re,sys,struct
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
import build_descriptions as b
from description_ids import font_ids
from codec import tokens
original=b.fe.p.read(3731);patched=(P/'members/member3731_korean.bin').read_bytes()
cache=b.load_cache();review=json.loads((P/'description_review09.json').read_text(encoding='utf8'))
controlled=json.loads((P/'description_control_review09.json').read_text(encoding='utf8'))
rows=json.loads((b.ROOT/'work/menu_patch/full_menu/item_descriptions.json').read_text(encoding='utf8'))
source={x['id']:x['jp'] for x in json.loads((P/'extras_source.json').read_text(encoding='utf8')) if x['kind']=='description'}
def resource(blob,at):
 md=blob[at+3];c,u=struct.unpack_from('<II',blob,at+4)
 decoded=b.fe.slz.decompress_payload(blob[at+16:at+16+c],md,u)
 root=b.tree.parse(decoded,'d');font=b.tree.find(root,'d/2').data;text=b.tree.find(root,'d/1').data
 return decoded,font,text[struct.unpack_from('<I',text)[0]:].split(b'\0')[0]
def info(raw,font):
 n=struct.unpack_from('<I',font)[0];gs=[];cs=[]
 for k,bb,v in tokens(raw,list(range(n)),{}):
  if k=='glyph':
   code=bb[0] if len(bb)==1 else (bb[0]&127)+128*bb[1];assert 1<=code<=n
   bitmap=font[8+n+(code-1)*24:8+n+code*24]
   if any(bitmap):gs.append(bitmap)
  elif k=='control':cs.append(bb)
 return gs,cs
errors=[]
for row in rows:
 at=row['offset'];u,of,raw=resource(original,at);_,nf,new=resource(patched,at)
 assert raw==bytes.fromhex(row['hex'])
 ids=font_ids(u,row['font']);plain=re.sub(r'^(?:\{[0-9a-f]+\})+','',source[at])
 assert plain in review or str(at) in controlled
 if str(at) in controlled:
  target=controlled[str(at)]['ko']
  expected=[b.glyph(ch) for ch in re.sub(r'\{[0-9a-f]+\}','',target) if any(b.glyph(ch))]
 else:
  seg=b.translate(raw,ids,cache)
  if seg is None:
   assert not b.JP.search(source[at]);seg=[('raw',raw,None)]
  expected=[bitmap for k,bb,s in seg for bitmap in ([b.glyph(ch) for ch in s if any(b.glyph(ch))] if k=='ko' else info(bb,of)[0])]
 actual,controls=info(new,nf)
 if expected!=actual:errors.append(dict(offset=at,error='glyph mismatch'))
 if controls!=info(raw,of)[1]:errors.append(dict(offset=at,error='control mismatch'))
report=dict(rows=len(rows),unique_sources=len(set(source.values())),errors=errors,member_sha256=b.hashlib.sha256(patched).hexdigest())
(P/'review09/description_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=1))
assert not errors
