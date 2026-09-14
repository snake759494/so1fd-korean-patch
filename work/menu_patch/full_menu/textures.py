from nested import *
from PIL import Image,ImageDraw
def tim(d):
 if len(d)<32 or struct.unpack_from('<I',d)[0] not in [16,17]:return
 flags=struct.unpack_from('<I',d,4)[0];cl=struct.unpack_from('<I',d,8)[0]
 at=8+cl
 if at+12>len(d):return
 size,x,y,w,h=struct.unpack_from('<I4H',d,at)
 if w<1 or h<1 or w*h>512*512 or size<12 or at+size>len(d):return
 b=d[at+12:at+size];bpp=[4,8,16,24][flags&3]
 if bpp!=4:return
 width=w*4;im=Image.new('L',(width,h));vals=[v*17 for a in b for v in [a&15,a>>4]]
 if len(vals)<width*h:return
 im.putdata(vals[:width*h]);return im,at+12
def main():
 p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin');out=OUT/'textures';out.mkdir(exist_ok=True);seen={};report=[]
 for m in range(2328,2375):
  for n in tree.walk(tree.parse(p.read(m),str(m))):
   if n.kind!='raw':continue
   r=tim(n.data)
   if not r:continue
   im,at=r;key=hash(n.data)
   name=n.path.replace('!','').replace('/','_')
   report.append({'member':m,'path':n.path,'image':seen.get(key,name)+'.png','pixel_offset':at,'size':im.size})
   if key in seen:continue
   seen[key]=name;im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST).save(out/(name+'.png'))
 (out/'index.json').write_text(json.dumps(report,indent=1),encoding='utf8');print(report)
if __name__=='__main__':main()
