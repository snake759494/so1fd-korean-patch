"""Install the shared default-name alphabet in menu and small HUD fonts."""
from build_menus import *
from name_encoding import ALIASES
from PIL import Image,ImageDraw
import patch_small_font as small

# Seven visible rows plus an empty baseline; glyphs are drawn at native size.
ROWS={
 '크':['01111100','00000100','01111100','00000100','00000000','01111100','00000000'],
 '스':['00010000','00101000','01000100','00000000','00000000','01111100','00000000'],
 '로':['11111000','00001000','11111000','10000000','11111000','00100000','11111000'],
 '닉':['11100100','10000100','10000100','11100100','00000000','01111100','00000100'],
 '시':['01000100','01000100','10100100','10100100','00000100','00000100','00000100'],
 '우':['00111000','01000100','00111000','00000000','01111100','00010000','00010000'],
 '이':['01000100','10100100','10100100','10100100','01000100','00000100','00000100'],
 '아':['01000100','10100100','10100100','10100111','01000100','00000100','00000100'],
 '요':['00111000','01000100','00111000','00000000','00101000','00101000','01111100'],
 '슈':['00010000','00101000','01000100','00000000','01111100','00101000','00101000'],
 '피':['11100100','10100100','10100100','10100100','11100100','00000100','00000100'],
 '마':['11100100','10100100','10100100','10100111','11100100','00000100','00000100'],
 '벨':['10100101','11111101','11100101','00000000','01111100','01000000','01111100'],
 '레':['11100101','00100101','11111101','10000101','11100101','00000101','00000101'],
 '니':['10000100','10000100','10000100','11100100','00000100','00000100','00000100'],
 '페':['11100101','10100101','10111101','10100101','11100101','00000101','00000101'],
 '웰':['01000101','10100101','01000101','11111101','01000101','01111100','01111100'],
 '치':['01000100','11100100','01000100','10100100','00000100','00000100','00000100'],
 '에':['01000101','10100101','10111101','10100101','01000101','00000101','00000101'],
}
PATTERNS={**small.PATTERNS,**{k:v+['00000000'] for k,v in ROWS.items()}}

def patch_common_chain(blob):
 chain=fe.slz.parse_chain(blob)
 pieces=[fe.slz.decompress_payload(blob[o+16:o+16+c],md,u) for md,c,u,link,o in chain]
 font=pieces[1];n,h=struct.unpack_from('<II',font);assert (n,h)==(240,12)
 widths=font[8:8+n]+bytes([12]*24)
 pieces[1]=struct.pack('<II',264,12)+widths+font[8+n:]+b''.join(glyph(ch) for ch in ALIASES.values())
 result=bytearray()
 for i,data in enumerate(pieces):
  md,comp=min(((md,data if md==0 else fe.slz.compress_payload(data,md)) for md in (0,1,2)),key=lambda x:len(x[1]))
  link=(16+len(comp)+3)&~3 if i<len(pieces)-1 else 0
  result+=b'SLZ'+bytes([md])+struct.pack('<III',len(comp),len(data),link)+comp
  if link:result+=bytes(link-16-len(comp))
 assert fe.slz.decompress(result)==b''.join(pieces)
 return bytes(result)

def main():
 report=[]
 for row in json.loads((P/'menu_build_report.json').read_text(encoding='utf8')):
  m=row['member'];path=P/'members'/f'member{m}_korean.bin';source=path.read_bytes()
  root=fe.extract.parse_resource(source,m);group=tree.find(root,f'{m}!/0/1');strings=group.data.split(b'\0')
  if len(strings)<50:continue
  node=tree.find(root,f'{m}!/1');font=node.data;n,h=struct.unpack_from('<II',font)
  widths=bytearray(font[8:8+n]);gs=[font[8+n+i*24:8+n+(i+1)*24] for i in range(n)]
  for alias,ch in ALIASES.items():
   bitmap=glyph(ch)
   v=next((i+1 for i,g in enumerate(gs) if g==bitmap and widths[i]==12),None)
   if v is None:gs.append(bitmap);widths.append(12);v=len(gs)
   strings[ord(alias)-96]=fb.enc(v)
  repl={group.path:b'\0'.join(strings),node.path:struct.pack('<II',len(gs),12)+widths+b''.join(gs)}
  inner=menu_build.repack(root.kids[0],repl)
  mode,comp=min(((md,fe.slz.compress_payload(inner,md)) for md in (1,2)),key=lambda x:len(x[1]))
  assert len(comp)+16<=len(source),(m,len(comp)+16,len(source))
  patch=(b'SLZ'+bytes([mode])+struct.pack('<III',len(comp),len(inner),0)+comp).ljust(len(source),b'\0')
  assert fe.slz.decompress(patch)==inner;path.write_bytes(patch)
  report.append(dict(member=m,type='menu',glyphs=len(gs),used=len(comp)+16,slot=len(source)))
 # Start with the existing translated texture to retain all menu labels.
 for m in (2326,2330,2334,2338,2342,2372):
  source=ROOT/'work/menu_patch/full_menu'/f'member{m}_korean.bin';root=tree.parse(source.read_bytes(),str(m))
  leaf=tree.find(root,f'{m}!/1');im,at=small.tim(leaf.data)
  idx=Image.frombytes('L',im.size,bytes(v//17 for v in im.tobytes()))
  original=tree.parse(fe.p.read(m),str(m));orig_im,_=small.tim(tree.find(original,f'{m}!/1').data)
  orig_idx=Image.frombytes('L',orig_im.size,bytes(v//17 for v in orig_im.tobytes()))
  for a in 'QJYZ;':
   cell=ord(a)-32;x=cell%32*8;y=cell//32*8;idx.paste(orig_idx.crop((x,y,x+8,y+8)),(x,y))
  for a,ch in ALIASES.items():
   cell=ord(a)-32;x=cell%32*8;y=cell//32*8
   for yy,bits in enumerate(PATTERNS[ch]):
    for xx,v in enumerate(bits):idx.putpixel((x+xx,y+yy),15*int(v))
  vals=idx.tobytes();data=bytearray(leaf.data)
  data[at:at+len(vals)//2]=bytes(vals[i]|vals[i+1]<<4 for i in range(0,len(vals),2))
  tree.mark(root,leaf.path,bytes(data));(P/'members'/f'member{m}_korean.bin').write_bytes(tree.build(root))
  report.append(dict(member=m,type='small',aliases=len(ALIASES)))
  if m==2330:idx.point(lambda v:v*17).resize((im.width*4,im.height*4),Image.Resampling.NEAREST).save(P/'review09/name_small_atlas.png')
 folder=ROOT/'work/menu_patch/full_menu'
 old=(folder/'member2371_korean.bin').read_bytes();u=fe.slz.decompress(old)
 inner=u[:4]+patch_common_chain(u[4:]);md,comp=min(((md,inner if md==0 else fe.slz.compress_payload(inner,md)) for md in (0,1,2)),key=lambda x:len(x[1]))
 assert len(comp)+16<=len(old)
 out=(b'SLZ'+bytes([md])+struct.pack('<III',len(comp),len(inner),0)+comp).ljust(len(old),b'\0')
 assert fe.slz.decompress(out)==inner;(P/'members/member2371_korean.bin').write_bytes(out)
 old=(folder/'member5053_korean.bin').read_bytes();n,ot,st,start=struct.unpack_from('<4I',old)
 offs=struct.unpack_from(f'<{n}I',old,ot);sizes=struct.unpack_from(f'<{n}I',old,st)
 pieces=[old[o:o+s] for o,s in zip(offs,sizes)];pieces[9]=patch_common_chain(pieces[9]);out=bytearray(old[:start])
 for i,data in enumerate(pieces):
  struct.pack_into('<I',out,ot+4*i,len(out));struct.pack_into('<I',out,st+4*i,len(data));out+=data;out+=bytes(-len(out)%16)
 allocated=fe.p.offsets[5054]-fe.p.offsets[5053]
 assert len(out)<=allocated,(len(out),allocated)
 with Path(fe.p.path).open('rb') as f:
  f.seek(fe.p.offsets[5053]+len(old));assert not any(f.read(allocated-len(old)))
 (P/'members/member5053_korean.bin').write_bytes(out.ljust(max(len(old),len(out)),b'\0'))
 report.append(dict(member=5053,original_bytes=len(old),new_bytes=len(out),allocation=allocated,extra_bytes=max(0,len(out)-len(old))))
 report.extend([dict(member=m,type='name_entry',glyphs=264) for m in (2371,5053)])
 (P/'review09/name_font_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf8')
 print('Name fonts built:',len(report),'banks')
if __name__=='__main__':main()
