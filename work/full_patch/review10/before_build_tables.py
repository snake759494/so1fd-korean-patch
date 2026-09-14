from build_fields import *
from codec import tokens
def build(m,cache):
 orig=fe.p.read(m)
 if m==3320:
  positions=[8,struct.unpack_from('<I',orig,4)[0]]
  chain=[(orig[o+3],*struct.unpack_from('<III',orig,o+4),o) for o in positions]
 else:chain=fe.slz.parse_chain(orig)
 ps=[fe.slz.decompress_payload(orig[o+16:o+16+c],md,u) for md,c,u,_,o in chain]
 text,font=ps[:2];n,h=struct.unpack_from('<II',font);assert h==12
 ids=fe.extract.g['banks'][next(c['key'] for c in fe.extract.cat if c['member']==m)]['ids']
 rows=[x for x in json.loads((P/'extras_source.json').read_text(encoding='utf8')) if x['kind']=='table' and x['member']==m]
 used=set(range(1,261));prepared=[]
 for row in rows:
  raw=bytes.fromhex(row['hex']);out=[]
  for k,b,s in parts(raw,ids,field=False):
   if k=='text' and JP.search(s):out.append(('ko',cache[norm(s)]))
   else:
    out.append(('raw',b))
    if k=='text':
     for kk,bb,vv in tokens(b,ids,labels):
      if kk=='glyph':used.add(bb[0] if len(bb)==1 else(bb[0]&127)+128*bb[1])
  prepared.append(out)
 chars=sorted({c for row in prepared for k,s in row if k=='ko' for c in s});widths=bytearray(font[8:8+n]);gs=[font[8+n+i*24:8+n+(i+1)*24] for i in range(n)]
 free=[v for v in range(261,n+1) if v not in used];mapping={}
 for ch in chars:
  if free:v=free.pop(0)
  else:v=len(gs)+1;gs.append(bytes(24));widths.append(0)
  mapping[ch]=v;gs[v-1]=glyph(ch);widths[v-1]=6 if ord(ch)<128 else 12
 while len(gs)%4:gs.append(bytes(24));widths.append(0)
 ps[1]=struct.pack('<II',len(gs),12)+widths+b''.join(gs)
 prefix=bytearray(text[:rows[0]['offset']]);data=bytearray();shared={}
 for i,(row,seg) in enumerate(zip(rows,prepared)):
  encoded=b''.join(b''.join(fb.enc(mapping[ch]) for ch in s) if kind=='ko' else s for kind,s in seg)+b'\0'
  if encoded not in shared:shared[encoded]=len(prefix)+len(data);data+=encoded
  struct.pack_into('<H',prefix,i*4+2,shared[encoded])
 ps[0]=bytes(prefix+data);body=bytearray(orig);sizes=[]
 for i,((mode,comp,unp,link,o),part) in enumerate(zip(chain,ps)):
  if part==fe.slz.decompress_payload(orig[o+16:o+16+comp],mode,unp):continue
  payload=fe.slz.compress_payload(part,mode)
  if len(payload)>comp and mode==1:
   alt=fe.slz.compress_payload(part,2)
   if len(alt)<len(payload):mode=2;payload=alt
  if len(payload)>comp:raise ValueError((m,i,'chain allocation overflow',len(payload),comp))
  body[o:o+16+comp]=b'SLZ'+bytes([mode])+struct.pack('<III',comp,len(part),link)+payload.ljust(comp,b'\0');sizes.append(len(payload))
 if m==3320:
  for (md,c,u,_,o),part in zip(chain,ps):assert fe.slz.decompress(body[o:])==part
 else:assert fe.slz.decompress(body)==b''.join(ps)
 dest=P/'members';dest.mkdir(exist_ok=True);(dest/f'member{m}_korean.bin').write_bytes(body)
 return dict(member=m,strings=len(rows),glyphs=len(gs),compressed=sizes)
if __name__=='__main__':
 cache=load_cache()
 good=[];bad=[]
 for m in [10,1709,3320]:
  try:r=build(m,cache);good.append(r);print(r,flush=True)
  except Exception as e:bad.append(dict(member=m,error=repr(e)));print(repr(e),flush=True)
 (P/'table_build_report.json').write_text(json.dumps(dict(success=good,errors=bad),indent=1),encoding='utf8')
