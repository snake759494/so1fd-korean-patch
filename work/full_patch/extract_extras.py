from build_fields import *
import tree,slz
def main():
 out=[]
 for m in [10,1709,3320]:
  raw=fe.p.read(m)
  if m==3320:raw=raw[8:struct.unpack_from('<I',raw,4)[0]]
  chain=slz.parse_chain(raw);mode,comp,unp,_,at=chain[0];text=slz.decompress_payload(raw[at+16:at+16+comp],mode,unp)
  bank=next(c for c in fe.extract.cat if c['member']==m);ids=fe.extract.g['banks'][bank['key']]['ids'];pos=0
  while pos<struct.unpack_from('<H',text,2)[0] and struct.unpack_from('<H',text,pos)[0]!=65535:
   ident,off=struct.unpack_from('<HH',text,pos);pos+=4
   b=text[off:].split(b'\0')[0]
   out.append(dict(kind='table',member=m,id=ident,offset=off,hex=b.hex(),jp=''.join(s if k=='text' else '{'+raw.hex()+'}' for k,raw,s in parts(b,ids,field=False))))
 for m in range(2328,2375):
  try:r=fe.extract.extract(m,fe.p)
  except Exception:continue
  if not r:continue
  bank=next(c for c in fe.extract.cat if c['member']==m and(c['path']==f'{m}/1' or m==2353));ids=fe.extract.g['banks'][bank['key']]['ids']
  for row in r['rows']:
   try:s=''.join(s if k=='text' else '{'+b.hex()+'}' for k,b,s in parts(bytes.fromhex(row['hex']),ids,field=False))
   except Exception:continue
   out.append(dict(kind='menu',member=m,**{k:v for k,v in row.items() if k!='jp'},jp=s))
 # Descriptions have a separate font in every 2048-byte block.
 import nested
 original=fe.p.read(3731)
 for row in json.loads((ROOT/'work/menu_patch/full_menu/item_descriptions.json').read_text(encoding='utf8')):
  at=row['offset'];mode=original[at+3];comp,unp,nxt=struct.unpack_from('<III',original,at+4);u=slz.decompress_payload(original[at+16:at+16+comp],mode,unp)
  from description_ids import font_ids
  ids=font_ids(u,row['font']);b=bytes.fromhex(row['hex'])
  try:s=''.join(s if k=='text' else '{'+b.hex()+'}' for k,b,s in parts(b,ids,field=False))
  except Exception:s=row['text']
  out.append(dict(kind='description',member=3731,id=at,hex=b.hex(),jp=s))
 (P/'extras_source.json').write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf8')
 from collections import Counter
 print(Counter(x['kind'] for x in out),flush=True)
if __name__=='__main__':main()
