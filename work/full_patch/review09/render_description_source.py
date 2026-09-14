"""Render original description font bytes, not OCR text."""
import json,sys,struct
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
import build_descriptions as b
from codec import tokens
rows={x['id']:x for x in json.loads((P/'extras_source.json').read_text(encoding='utf8')) if x['kind']=='description'}
keys=[int(s) for s in sys.argv[1:]]
orig=b.fe.p.read(3731)
im=Image.new('RGB',(1400,190*len(keys)),'white');draw=ImageDraw.Draw(im)
for row,key in enumerate(keys):
 mode=orig[key+3];comp,unp,nxt=struct.unpack_from('<III',orig,key+4)
 u=b.fe.slz.decompress_payload(orig[key+16:key+16+comp],mode,unp)
 tree=b.tree.parse(u,'d');font=b.tree.find(tree,'d/2').data
 n,h=struct.unpack_from('<II',font);x=100;y=190*row+5
 draw.text((3,y),str(key),fill='black')
 for kind,raw,value in tokens(bytes.fromhex(rows[key]['hex']),list(range(n)),{}):
  if kind=='control':
   if value==0x4000:x=100;y+=38
   continue
  if kind!='glyph':continue
  code=raw[0] if len(raw)==1 else (raw[0]&127)+128*raw[1]
  bitmap=font[8+n+(code-1)*24:8+n+code*24]
  for yy in range(12):
   bits=int.from_bytes(bitmap[yy*2:yy*2+2],'little')
   for xx in range(12):
    if bits&(1<<(15-xx)):draw.rectangle((x+xx*3,y+yy*3,x+xx*3+2,y+yy*3+2),fill='black')
  x+=36
im.save(P/'review09/description_source.png')
