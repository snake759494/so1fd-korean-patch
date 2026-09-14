from build import *
LABELS={120:'히라',121:'카타',122:'ABC',123:'확인',124:'삭제',125:'뒤로'}
def patch_chain(blob):
 chain=slz.parse_chain(blob);parts=[slz.decompress_payload(blob[o+16:o+16+c],m,u) for m,c,u,_,o in chain]
 text,font=parts[:2];n,h=struct.unpack_from('<II',font);assert (n,h)==(240,12)
 widths=bytearray(font[8:248]);glyphs=[font[248+i*24:248+(i+1)*24] for i in range(240)]
 chars=sorted(set(''.join(LABELS.values()))-set('ABC'));free=list(range(231,241));mapping={ch:ord(ch)-31 for ch in 'ABC'}
 for ch in chars:
  if free:v=free.pop(0)
  else:v=len(glyphs)+1;glyphs.append(bytes(24));widths.append(12)
  mapping[ch]=v;bits=kfont.render(ch);b=kfont.encode(bits);glyphs[v-1]=b''.join(b[j:j+2][::-1] for j in range(0,24,2));widths[v-1]=12
 parts[1]=struct.pack('<II',len(glyphs),12)+widths+b''.join(glyphs)
 entries=[];pos=0
 while struct.unpack_from('<H',text,pos)[0]!=0xffff:
  ident,off=struct.unpack_from('<HH',text,pos);entries.append((ident,off));pos+=4
 prefix=bytearray(text[:pos+2]);body=bytearray()
 for i,(ident,off) in enumerate(entries):
  s=text[off:].split(b'\0')[0]
  if ident in LABELS:s=b''.join(enc(mapping[ch]) for ch in LABELS[ident])
  struct.pack_into('<H',prefix,i*4+2,len(prefix)+len(body));body+=s+b'\0'
 parts[0]=bytes(prefix+body)
 out=bytearray()
 for i,((mode,comp,unp,nxt,off),data) in enumerate(zip(chain,parts)):
  payload=data if mode==0 else slz.compress_payload(data,mode)
  size=max(comp,len(payload));link=(16+size+3)&~3 if i<len(parts)-1 else 0
  out+=b'SLZ'+bytes([mode])+struct.pack('<III',size,len(data),link)+payload.ljust(size,b'\0')
  if link:out+=bytes(link-16-size)
 assert slz.decompress(out)==b''.join(parts)
 return bytes(out),mapping
def main():
 p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin');orig=p.read(2371);u=slz.decompress(orig);chain,mapping=patch_chain(u[4:]);inner=u[:4]+chain
 assert orig[3]==0
 patch=b'SLZ\0'+struct.pack('<III',len(inner),len(inner),0)+inner
 assert len(patch)<=len(orig),(len(patch),len(orig))
 patch=patch.ljust(len(orig),b'\0');assert slz.decompress(patch)==inner
 (OUT/'member2371_korean.bin').write_bytes(patch)
 (OUT/'common_mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=1),encoding='utf8')
 print('common labels',len(LABELS),'glyphs',mapping,'slot',len(patch),'used',16+len(inner))
if __name__=='__main__':main()
