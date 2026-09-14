from pathlib import Path
import json
from PIL import Image,ImageDraw
P=Path(__file__).parent
data=json.loads((P/'description_unknown_bitmaps.json').read_text())
for page in range((len(data)+63)//64):
 im=Image.new('RGB',(800,680),'white');dr=ImageDraw.Draw(im)
 for i,(raw,count) in enumerate(data[page*64:page*64+64]):
  x=i%8*100;y=i//8*85;raw=bytes.fromhex(raw)
  for yy in range(12):
   v=int.from_bytes(raw[yy*2:yy*2+2],'little')
   for xx in range(12):
    if v&(1<<(15-xx)):dr.rectangle((x+8+xx*4,y+yy*4,x+11+xx*4,y+yy*4+3),fill='black')
  dr.text((x+8,y+52),str(page*64+i)+' x'+str(count),fill='black')
 im.save(P/f'desc_glyph_{page:02}.png')
