from field_extract import *
import re,hashlib,textwrap
import kfont
import importlib.util
spec=importlib.util.spec_from_file_location('story_translations',OUT/'translations.py')
translation_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(translation_module)
T=translation_module.T
def enc(v):return bytes([v]) if v<128 else bytes([(v&127)|128,v>>7])
def wrap(s):
 lines=[]
 for part in s.replace('\\n','\n').split('\n'):
  # Count Hangul at full advance, keeping a conservative 300 px line.
  buf='';width=0
  for ch in re.findall(r'\{[0-9a-f]+\}|.',part):
   if ch.startswith('{'):buf+=ch;continue
   w=12 if ord(ch)>127 and ch!=' ' else 6
   if width+w>300:lines.append(buf);buf='';width=0
   buf+=ch;width+=w
  lines.append(buf)
 return ''.join((('{8180}' if i%3==0 else '{8080}') if i else '')+s for i,s in enumerate(lines))
def make(m):
 r=read(m);changes={i:s for (mm,i),s in T.items() if mm==m}
 n,h=struct.unpack_from('<II',r['font']);assert (n,h)==(len(r['ids']),12)
 widths=bytearray(r['font'][8:8+n]);glyphs=[r['font'][8+n+i*24:8+n+(i+1)*24] for i in range(n)]
 mapping={}
 used=set(range(1,235))
 for row in r['rows']:
  if row['index'] in changes:continue
  d=bytes.fromhex(row['hex']);i=0
  while i<len(d):
   v=d[i];i+=1
   if v>=128:v=(v&127)+d[i]*128;i+=1
   if v in (0x4004,0x4006,0x400c,0x400e):i+=1
   elif 0<v<=n:used.add(v)
 free=[v for v in range(235,n+1) if v not in used]
 strings={i:wrap(s) for i,s in changes.items()}
 chars=sorted(set(''.join(re.sub(r'\{[0-9a-f]+\}','',s) for s in strings.values())))
 for ch in chars:
  if free:v=free.pop(0)
  else:v=len(glyphs)+1;glyphs.append(bytes(24));widths.append(12)
  mapping[ch]=v;b=kfont.encode(kfont.render(ch))
  glyphs[v-1]=b''.join(b[j:j+2][::-1] for j in range(0,24,2))
  widths[v-1]=6 if ord(ch)<128 or ch==' ' else 12
 # Keep the retail four-byte font payload alignment, including mode-2 decoding.
 while len(glyphs)%4:glyphs.append(bytes(24));widths.append(0)
 font=struct.pack('<II',len(glyphs),12)+widths+b''.join(glyphs)
 data=bytearray();offsets=[];report=[]
 for row in r['rows']:
  i=row['index'];old=bytes.fromhex(row['hex']);new=old;offsets.append(len(data))
  if i in strings:
   # Five font-coded digits carry the dialogue/voice identifier.
   prefix=old[:10] if re.match(r'^\d{5}',row['jp']) else b''
   if old.startswith(b'\x85\x80'):prefix+=b'\x85\x80'
   if old.endswith(b'\x86\x80\x78\x00\x00'):end=b'\x86\x80\x78\x00\x00'
   elif old.endswith(b'\x86\x80\x00\x00\x00'):end=b'\x86\x80\x00\x00\x00'
   elif old.endswith(b'\x81\x80\x00'):end=b'\x81\x80\x00'
   else:assert old.endswith(b'\x82\x80\x00'),(m,i,old[-12:].hex());end=b'\x82\x80\x00'
   payload=b''.join(bytes.fromhex(t[1:-1]) if t.startswith('{') else enc(mapping[t]) for t in re.findall(r'\{[0-9a-f]+\}|.',strings[i]))
   new=prefix+payload+end
   report.append({'index':i,'jp':row['jp'],'ko':changes[i],'old_bytes':len(old),'new_bytes':len(new)})
  data+=new
 assert len(data)<65536
 script=bytearray(r['script'][:r['table']]);struct.pack_into('<I',script,16,len(data))
 script+=struct.pack(f'<{len(offsets)}H',*offsets)+data
 parts=[bytes(script),font];blob=bytearray()
 for i,part in enumerate(parts):
  mode=r['chain'][i][0];payload=slz.compress_payload(part,mode)
  if i==0:
   original_comp=r['chain'][i][1];link=r['chain'][i][3]
   assert len(payload)<=original_comp,(m,len(payload),original_comp)
   payload=payload.ljust(original_comp,b'\0')
  else:link=0
  blob+=b'SLZ'+bytes([mode])+struct.pack('<III',len(payload),len(part),link)+payload
  if link:blob+=bytes(link-16-len(payload))
 assert slz.decompress(blob)==b''.join(parts)
 # Preserve every map chunk offset and its sector-sized allocation.
 assert len(blob)<=r['b']-r['a'],(m,len(blob),r['b']-r['a'])
 body=bytearray(r['orig']);body[r['a']:r['b']]=blob.ljust(r['b']-r['a'],b'\0');used=len(blob)
 # Reparse the written typed container and check the exact script/font streams.
 c,t=expand.as_typed_chunks(body);a,b=c[t.index(1)];assert slz.decompress(body[a:b])==b''.join(parts)
 (OUT/f'member{m}_korean.bin').write_bytes(body)
 result={'member':m,'strings':report,'glyphs_before':n,'glyphs_after':len(glyphs),'used':used,'slot':len(body),'sha256':hashlib.sha256(body).hexdigest()}
 (OUT/f'{m}_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=1),encoding='utf8')
 print(m,len(changes),n,'->',len(glyphs),used,'/',len(body),flush=True)
 return result
if __name__=='__main__':
 for m in sorted(set(m for m,i in T)):make(m)
