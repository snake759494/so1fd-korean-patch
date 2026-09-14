from nested import *
from PIL import Image,ImageDraw
def main():
 p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin');d=p.read(5053);count,tab,siztab,start=struct.unpack_from('<4I',d);offs=list(struct.unpack_from(f'<{count}I',d,tab));sizes=list(struct.unpack_from(f'<{count}I',d,siztab));out=OUT/'psp_text';out.mkdir(exist_ok=True);ims=[];report=[]
 ram=(OUT/'status_v2_ram.bin').read_bytes()
 for i,(off,size) in enumerate(zip(offs,sizes)):
  if i<32:continue
  b=d[off:off+size];w,h=struct.unpack_from('<HH',b)
  if w*h//2+4!=len(b):continue
  im=Image.new('L',(w,h));im.putdata([v*17 for x in b[4:] for v in [x&15,x>>4]])
  im.save(out/f'{i}.png');ims.append((i,im));report.append({'child':i,'offset':off,'size':size,'width':w,'height':h,'ram':ram.find(b)})
 sheet=Image.new('L',(650,len(ims)*28));draw=ImageDraw.Draw(sheet)
 for y,(i,im) in enumerate(ims):draw.text((0,y*28),str(i),fill=255);sheet.paste(im,(36,y*28))
 sheet.resize((1300,sheet.height*2),Image.Resampling.NEAREST).save(out/'sheet.png');(out/'index.json').write_text(json.dumps(report,indent=1));print(report)
if __name__=='__main__':main()
