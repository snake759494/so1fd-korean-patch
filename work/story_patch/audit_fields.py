from field_extract import *
from field_build import T
import re
reports=[]
for m in sorted(set(mm for mm,i in T)):
 r=read(m);new=(OUT/f'member{m}_korean.bin').read_bytes();chunks,types=expand.as_typed_chunks(new);a,b=chunks[types.index(1)];c=slz.parse_chain(new[a:b]);u=slz.decompress(new[a:b]);s=u[:c[0][2]];f=u[c[0][2]:]
 assert c[0][1]==r['chain'][0][1] and c[0][3]==r['chain'][0][3]
 assert s[:16]==r['script'][:16] and s[20:r['table']]==r['script'][20:r['table']]
 n,h=struct.unpack_from('<II',f);oldn=len(r['ids'])
 assert n%4==0 and len(f)%4==0,(m,'unaligned field font')
 reserved=set(range(1,235))
 for row in r['rows']:
  if (m,row['index']) in T:continue
  d=bytes.fromhex(row['hex']);i=0
  while i<len(d):
   v=d[i];i+=1
   if v>=128:v=(v&127)+d[i]*128;i+=1
   if v in (0x4004,0x4006,0x400c,0x400e):i+=1
   elif 0<v<=oldn:reserved.add(v)
 for v in reserved:
  assert f[8+v-1]==r['font'][8+v-1]
  assert f[8+n+(v-1)*24:8+n+v*24]==r['font'][8+oldn+(v-1)*24:8+oldn+v*24]
 assert chunks==expand.as_typed_chunks(r['orig'])[0]
 offsets=list(struct.unpack_from(f'<{r["head"][3]}H',s,r['table']));offsets.append(len(s)-r['base'])
 voices=0;untouched=0
 for row in r['rows']:
  i=row['index'];old=bytes.fromhex(row['hex']);d=s[r['base']+offsets[i]:r['base']+offsets[i+1]]
  if (m,i) not in T:assert d==old;untouched+=1
  elif re.match(r'^\d{5}',row['jp']):assert d[:10]==old[:10];voices+=1
 for (a,b),typ in zip(*expand.as_typed_chunks(r['orig'])):
  if typ==1:continue
  j=types.index(typ);na,nb=chunks[j];old=r['orig'][a:b];d=new[na:nb]
  if slz.is_slz(old):assert slz.decompress(old)==slz.decompress(d)
  else:assert d[:len(old)]==old
 reports.append({'member':m,'event_code':'IDENTICAL','reserved_glyphs':'IDENTICAL','other_map_assets':'IDENTICAL','map_chunk_offsets':'IDENTICAL','first_slz_allocation_and_link':'IDENTICAL','font_four_byte_alignment':'PASS','voice_ids_preserved':voices,'untouched_messages':untouched})
(OUT/'field_audit.json').write_text(json.dumps(reports,indent=2));print('PASS',len(reports),'maps')
