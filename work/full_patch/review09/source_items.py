"""Render uncertain source text from original glyph bitmaps for visual review."""
import json,pickle,sys
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];ROOT=P.parents[1]
sys.path[:0]=[str(P),str(ROOT/'work/story_patch')]
import field_extract as fe
from codec import field_tokens
c=json.loads((P/'context_review_catalog.json').read_text(encoding='utf8'))
g=pickle.load(open(ROOT/'work/glyphs.pkl','rb'))
keys=[4242,4379,5524,5652,7984,7993,8005,8640,515,3462,3826]
im=Image.new('RGB',(1500,68*len(keys)),'white');dr=ImageDraw.Draw(im)
for row,k in enumerate(keys):
 m,i=c[k]['locations'][0];r=fe.read(m);x=65;y=row*68+7
 dr.text((4,y+15),str(k),fill='black')
 for kind,b,v in field_tokens(bytes.fromhex(r['rows'][i]['hex']),r['ids'],{}):
  if kind!='glyph':continue
  local=b[0] if len(b)==1 else (b[0]&127)+128*b[1]
  raw=g['glyphs'][r['ids'][local-1]]
  for yy in range(12):
   bits=int.from_bytes(raw[yy*2:yy*2+2],'big')
   for xx in range(12):
    if bits&(1<<(15-xx)):dr.rectangle((x+xx*3,y+yy*3,x+xx*3+2,y+yy*3+2),fill='black')
  x+=39
  if x>1450:break
im.save(P/'review09'/'source_items.png')
print(P/'review09'/'source_items.png')
