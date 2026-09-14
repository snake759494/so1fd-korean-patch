from build import *
from textures import tim
from PIL import Image,ImageDraw
def patch_tim(data,labels):
 im,at=tim(data);idx=Image.frombytes('L',im.size,bytes(v//17 for v in im.tobytes()))
 for x,y,w,h,text in labels:
  ImageDraw.Draw(idx).rectangle((x,y,x+w-1,y+h-1),fill=0)
  for i,ch in enumerate(text):
   bits=kfont.render(ch)
   for yy,xx in zip(*bits.nonzero()):
    if xx+i*12<w and yy<h:idx.putpixel((x+i*12+int(xx),y+int(yy)),15)
 vals=idx.tobytes();packed=bytes(vals[i]|vals[i+1]<<4 for i in range(0,len(vals),2));out=bytearray(data);out[at:at+len(packed)]=packed
 return bytes(out),idx.point(lambda v:v*17)
def main():
 p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin')
 for m in [2326,2330,2334,2338,2342,2372]:
  orig=p.read(m);t=tree.parse(orig,str(m));path=f'{m}!/0';leaf=tree.find(t,path)
  # Standalone atlas labels, separate from icons and equipment category words.
  data,im=patch_tim(leaf.data,[(0,72,48,14,'종합속성'),(160,96,40,16,'습득도')]);tree.mark(t,path,data)
  patched=tree.build(t);(OUT/f'member{m}_korean.bin').write_bytes(patched)
  if m==2330:im.resize((1024,512),Image.Resampling.NEAREST).save(OUT/'common_ui_korean.png')
 # Item resource contains the six elemental labels shared by equipment/status.
 source=(OUT/'member2346_korean.bin').read_bytes();t=tree.parse(source,'2346');leaf=tree.find(t,'2346!/9!')
 labels=[(i*16+2,4,12,12,ch) for i,ch in [(0,'땅'),(1,'물'),(2,'불'),(3,'풍'),(7,'빛'),(8,'암')]]
 data,im=patch_tim(leaf.data,labels);tree.mark(t,leaf.path,data)
 patched=tree.build(t);(OUT/'member2346_korean.bin').write_bytes(patched)
 im.resize((1024,256),Image.Resampling.NEAREST).save(OUT/'elements_korean.png')
 print('shared atlas and elemental labels built')
if __name__=='__main__':main()
