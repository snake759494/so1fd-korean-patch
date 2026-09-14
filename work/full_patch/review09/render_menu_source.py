"""Show original glyphs for menu catalog entries whose OCR is ambiguous."""
import json,sys,struct
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
import build_menus as b
from codec import tokens
catalog=json.loads((P/'review09/menu_audit_catalog.json').read_text(encoding='utf8'))
rows={str(x['id']):x for x in json.loads((P/'extras_source.json').read_text(encoding='utf8'))}
keys=[int(s) for s in sys.argv[1:]]
im=Image.new('RGB',(1200,44*len(keys)),'white');draw=ImageDraw.Draw(im)
for y,key in enumerate(keys):
 row=rows[str(catalog[key]['id'])];m=row['member']
 orig=b.fe.p.read(m)
 if row['kind']=='menu':
  root=b.fe.extract.parse_resource(orig,m)
  font=b.tree.find(root,f'{m}!/1').data
 else:
  if m==3320:
   o=struct.unpack_from('<I',orig,4)[0];md=orig[o+3];c,u=struct.unpack_from('<II',orig,o+4)
  else:md,c,u,_,o=b.fe.slz.parse_chain(orig)[1]
  font=b.fe.slz.decompress_payload(orig[o+16:o+16+c],md,u)
 n,h=struct.unpack_from('<II',font);x=80;y*=44
 draw.text((3,y),str(key),fill='black')
 for kind,raw,value in tokens(bytes.fromhex(row['hex']),list(range(n)),{}):
  if kind!='glyph':continue
  code=raw[0] if len(raw)==1 else (raw[0]&127)+128*raw[1]
  bitmap=font[8+n+(code-1)*24:8+n+code*24]
  for yy in range(12):
   bits=int.from_bytes(bitmap[yy*2:yy*2+2],'little')
   for xx in range(12):
    if bits&(1<<(15-xx)):draw.rectangle((x+xx*3,y+yy*3,x+xx*3+2,y+yy*3+2),fill='black')
  x+=36
im.save(P/'review09/menu_source.png')
