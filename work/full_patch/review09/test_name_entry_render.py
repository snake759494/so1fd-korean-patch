"""Exercise all 14 names in the transient editor buffer; restore it afterwards."""
import sys,time,base64,json,struct,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from ppsspp_rpc import Debugger
from name_encoding import NAMES,encode
from PIL import Image,ImageDraw,ImageFont
d=Debugger();widget=0x09917f00;records=[]
def read(a,n):return base64.b64decode(d.call('memory.read',address=a,size=n,replacements=False)['base64'])
def write(a,b):d.call('memory.write',address=a,base64=base64.b64encode(b).decode())
assert d.call('cpu.status').get('stepping')
cells=read(widget+0x48,36);cursor=read(widget+0x24,4)
assert cells[:24]==b''.join(bytes([c]).ljust(6,b'\0') for c in encode('라티크스'))
try:
 for jp,short,full in NAMES:
  raw=encode(short);write(widget+0x48,b''.join(bytes([c]).ljust(6,b'\0') for c in raw).ljust(36,b'\0'))
  write(widget+0x24,struct.pack('<I',len(raw)));d.call('cpu.resume');time.sleep(.15)
  path=P/'review09'/f'name_render_{len(records):02}.png';d.frame(path)
  records.append(dict(name=short,full=full,screenshot=str(path),fixture='Transient protagonist name editor; not a character recruitment test'))
  print(short,flush=True)
finally:
 if not d.call('cpu.status').get('stepping'):d.call('cpu.stepping')
 write(widget+0x48,cells);write(widget+0x24,cursor)
 d.call('cpu.resume');time.sleep(.15);d.frame(P/'review09/runtime_names_entry_restored.png');d.close()
sheet=Image.new('RGB',(550,len(records)*64),(16,26,35));draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype('D:/nds/files (1)/Galmuri11.ttf',16)
for i,r in enumerate(records):
 draw.text((8,i*64+15),r['name'],font=font,fill='white')
 im=Image.open(r['screenshot']);sheet.paste(im.crop((545,98,755,148)),(265,i*64+4))
sheet.save(P/'review09/name_render_contact_sheet.png')
(P/'review09/name_entry_render_report.json').write_text(json.dumps(dict(tests=records,editor_restored=True,visual_review_pending=True),ensure_ascii=False,indent=1),encoding='utf8')
