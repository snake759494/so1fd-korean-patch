from pathlib import Path
import json,pickle,re,collections,sys
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).parent;ROOT=P.parents[1]
g=pickle.load(open(ROOT/'work/glyphs.pkl','rb'))
d=json.loads((P/'field_unique.json').read_text(encoding='utf8'))
c=collections.Counter(int(k) for x in d for k in re.findall(r'\{g(\d+)\}',x['jp']))
order=[k for k,n in c.most_common()]
(P/'glyph_review_order.json').write_text(json.dumps(order))
for page in range((len(order)+63)//64):
 im=Image.new('RGB',(8*100,8*85),'white');dr=ImageDraw.Draw(im)
 for i,k in enumerate(order[page*64:page*64+64]):
  x=i%8*100;y=i//8*85;raw=g['glyphs'][k]
  for yy in range(12):
   v=int.from_bytes(raw[yy*2:yy*2+2],'big')
   for xx in range(12):
    if v&(1<<(15-xx)):dr.rectangle((x+xx*4,y+yy*4,x+xx*4+3,y+yy*4+3),fill='black')
  dr.text((x,y+52),str(k),fill='black')
 im.save(P/f'glyph_review_{page:02}.png')
