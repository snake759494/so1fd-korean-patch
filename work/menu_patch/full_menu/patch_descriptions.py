from build import *
DESCS={2529280:'길이1미터의 일반적인 검',2867200:'나무를 깎아 만든 평범한 지팡이',3368960:'동물 가죽으로 만든{8080}간단한 갑옷',3391488:'문장술사가 즐겨 입는 수수한 옷',3524608:'나무로 만든 간단한 방패',3629056:'나무로 만든 간단한 샌들',3633152:'동물 가죽으로 만든 간단한 각반'}
def make_descriptions(p):
 original=p.read(3731);data=bytearray(original);reports=[]
 for off,text in DESCS.items():
  mode=original[off+3];comp,unp,nxt=struct.unpack_from('<III',original,off+4);assert nxt==0
  old=slz.decompress_payload(original[off+16:off+16+comp],mode,unp);t=tree.parse(old,'d');f=tree.find(t,'d/2').data
  count,height=struct.unpack_from('<II',f);assert height==12
  chars=sorted(set(re.sub(r'\{[0-9a-f]+\}','',text)));mapping={c:i+1 for i,c in enumerate(chars)}
  newcount=max(count,len(chars));widths=bytearray(newcount);glyphs=[]
  for ch in chars:
   bits=kfont.render(ch);b=kfont.encode(bits);widths[mapping[ch]-1]=12 if '\uac00'<=ch<='\ud7a3' else kfont.advance(bits)
   glyphs.append(b''.join(b[j:j+2][::-1] for j in range(0,24,2)))
  font=struct.pack('<II',newcount,12)+widths+b''.join(glyphs)+bytes(24*(newcount-len(chars)))
  encoded=b''.join(bytes.fromhex(c[1:-1]) if c.startswith('{') else enc(mapping[c]) for c in re.findall(r'\{[0-9a-f]+\}|.',text))
  inner=repack(t,{'d/1':struct.pack('<I',4)+encoded+b'\0','d/2':font})
  payload=slz.compress_payload(inner,mode);newcomp=max(comp,len(payload));assert newcomp+16<=2048,(off,newcomp)
  # Only zero padding between this block and the next sector is consumed.
  assert not any(original[off+16+comp:off+16+newcomp])
  patch=b'SLZ'+bytes([mode])+struct.pack('<III',newcomp,len(inner),0)+payload.ljust(newcomp,b'\0')
  assert slz.decompress(patch)==inner
  data[off:off+len(patch)]=patch;reports.append({'offset':off,'korean':text,'font_before':count,'font_after':newcount})
 assert len(data)==len(original)
 (OUT/'member3731_korean.bin').write_bytes(data);(OUT/'description_translations.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
 return bytes(data)
if __name__=='__main__':
 p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin');make_descriptions(p);print('7 descriptions built')
