from build_fields import *
from codec import tokens
def encode_text(s,raw,mapping):
 chunks=wrap_fixed(s,raw.count(b'\x80\x80')+1)
 return b'\x80\x80'.join(b''.join(fb.enc(mapping[c]) for c in x) for x in chunks)
def remake(font,raws,changes,reserve=260,trim=False):
 n,h=struct.unpack_from('<II',font);assert h==12
 used=set(range(1,min(n,reserve)+1));widths=bytearray(font[8:8+n]);gs=[font[8+n+i*24:8+n+(i+1)*24] for i in range(n)]
 for key,raw in raws.items():
  if key in changes:continue
  for k,b,v in tokens(raw,list(range(n)),{}):
   if k=='glyph':used.add(b[0] if len(b)==1 else (b[0]&127)+128*b[1])
 chars=sorted({c for seg in changes.values() for kind,b,s in seg if kind=='ko' for c in s})
 for seg in changes.values():
  for kind,b,s in seg:
   if kind=='ko':continue
   for k,bb,v in tokens(b,list(range(n)),{}):
    if k=='glyph':used.add(bb[0] if len(bb)==1 else(bb[0]&127)+128*bb[1])
 free=[v for v in range(1,n+1) if v not in used];mapping={}
 for ch in chars:
  if free:v=free.pop(0)
  else:v=len(gs)+1;gs.append(bytes(24));widths.append(0)
  mapping[ch]=v;gs[v-1]=glyph(ch);widths[v-1]=6 if ord(ch)<128 else 12
 if trim:
  end=max(used|set(mapping.values()),default=0);gs=gs[:end];widths=widths[:end]
 while len(gs)%4:gs.append(bytes(24));widths.append(0)
 for key,seg in changes.items():raws[key]=b''.join(encode_text(s,b,mapping) if kind=='ko' else b for kind,b,s in seg)
 return struct.pack('<II',len(gs),12)+widths+b''.join(gs),raws
def translate(raw,ids,cache):
 result=[];changed=False
 for k,b,s in parts(raw,ids,field=False):
  if k=='text' and JP.search(s):result.append(('ko',b,cache[norm(s)]));changed=True
  else:result.append(('raw',b,None))
 return result if changed else None
