from build import *
from PIL import Image,ImageDraw
def main():
 p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin')
 for m in range(5039,5053):
  d=bytearray(p.read(m));assert d[:11]==b'MIG.00.1PSP'
  assert struct.unpack_from('<HH',d,72)==(512,512)
  im=Image.frombytes('P',(512,512),bytes(d[128:262272]));palette=[tuple(d[262352+i*4:262352+i*4+4]) for i in range(256)]
  bg=im.getpixel((254,25));white=min((i for i,c in enumerate(palette) if c[3]>=128),key=lambda i:sum((v-255)**2 for v in palette[i][:3]))
  ImageDraw.Draw(im).rectangle((252,24,404,44),fill=bg)
  x=256
  for ch in '이름을 정해 주세요':
   if ch==' ':x+=5;continue
   bits=kfont.render(ch)
   for yy,xx in zip(*bits.nonzero()):im.putpixel((x+int(xx),28+int(yy)),white)
   x+=12
  assert x<=404
  d[128:262272]=im.tobytes();(OUT/f'member{m}_korean.bin').write_bytes(d)
  if m==5039:
   im.putpalette([v for c in palette for v in c[:3]]);im.convert('RGB').save(OUT/'name_background_korean.png')
 print('14 name entry backgrounds built')
if __name__=='__main__':main()
