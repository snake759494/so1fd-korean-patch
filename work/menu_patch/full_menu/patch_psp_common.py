from patch_common import *
def main():
 p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin');b=p.read(5053);n,ot,st,start=struct.unpack_from('<4I',b);offs=struct.unpack_from(f'<{n}I',b,ot);sizes=struct.unpack_from(f'<{n}I',b,st);parts=[b[o:o+s] for o,s in zip(offs,sizes)]
 from PIL import Image,ImageDraw,ImageChops
 for i,label in {1:'새 게임',2:'이어 하기',3:'동영상 감상',4:'음성 감상'}.items():
  assert len(parts[i])==1088
  im=Image.new('L',(128,16))
  x=0
  for ch in label:
   if ch==' ':x+=5;continue
   bits=kfont.render(ch)
   for yy,xx in zip(*bits.nonzero()):im.putpixel((x+int(xx),2+int(yy)),11)
   x+=12
  # The title renderer filters textures: use two-pixel strokes for contrast.
  thick=Image.new('L',im.size)
  for dx,dy in [(0,0),(1,0),(0,1),(1,1)]:
   layer=Image.new('L',im.size);layer.paste(im,(dx,dy));thick=ImageChops.lighter(thick,layer)
  im=thick
  vals=im.tobytes();parts[i]=parts[i][:64]+bytes(vals[j]|vals[j+1]<<4 for j in range(0,len(vals),2))
 patched,_=patch_chain(parts[9]);compact=bytearray()
 for mode,comp,unp,nxt,o in slz.parse_chain(patched):
  u=slz.decompress_payload(patched[o+16:o+16+comp],mode,unp);payload=u if mode==0 else slz.compress_payload(u,mode);link=(16+len(payload)+3)&~3 if nxt else 0
  compact+=b'SLZ'+bytes([mode])+struct.pack('<III',len(payload),len(u),link)+payload
  if nxt:compact+=bytes(link-16-len(payload))
 assert slz.decompress(compact)==slz.decompress(patched);parts[9]=bytes(compact)
 out=bytearray(b[:start])
 for i,part in enumerate(parts):
  struct.pack_into('<I',out,ot+4*i,len(out));struct.pack_into('<I',out,st+4*i,len(part));out+=part;out+=bytes(-len(out)%16)
 assert len(out)<=len(b),(len(out),len(b));out=out.ljust(len(b),b'\0');(OUT/'member5053_korean.bin').write_bytes(out);print('PSP name tabs',len(compact),'fixed member',len(out))
if __name__=='__main__':main()

