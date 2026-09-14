from pathlib import Path
import sys,json,re,struct,hashlib,functools,time,traceback
P=Path(__file__).parent;ROOT=P.parents[1]
sys.path.insert(0,str(ROOT/'work/story_patch'))
import field_extract as fe
import field_build as fb
from codec import field_tokens as tokens,tokens as common_tokens
from glyph_labels_reviewed import load
from translate_local import norm
from layout import wrap_fixed,wrap_dialogue
from tagged_dialogue import replacement,control_signature
labels=dict(fe.extract.g['label']);labels.update(load())
from extra_labels import load as extra_load
labels.update(extra_load())
labels.update({2328:'褒',1859:'員',655:'負',1431:'聞',911:'実',749:'裏',694:'章',307:'思',251:'使',872:'吽',1616:'釈'})
labels.update({1302:'状',2834:'新',1311:'0'})
if (P/'label_corrections.json').exists():labels.update({int(k):v for k,v in json.loads((P/'label_corrections.json').read_text(encoding='utf8')).items()})
JP=re.compile(r'[\u3040-\u30ff\u3400-\u9fff]')
def load_cache():
 out=json.loads((P/'translation_cache.json').read_text(encoding='utf8'))
 for name in ['name_transliterations.json','reviewed_translations.json']:
  if (P/name).exists():out.update({norm(k):v for k,v in json.loads((P/name).read_text(encoding='utf8')).items()})
 from description_overrides import overrides
 out.update({norm(k):v for k,v in overrides().items()})
 if (P/'segment_catalog.json').exists():
  catalog={x['id']:x['jp'] for x in json.loads((P/'segment_catalog.json').read_text(encoding='utf8'))}
  for f in sorted((P/'hand_translations').glob('*.tsv')):
   for line in f.read_text(encoding='utf8').splitlines():
    if not line.strip():continue
    key,value=line.split('\t',1);out[catalog[int(key)]]=value
 terminology=P/'terminology_review09.json'
 if terminology.exists():
  out.update({norm(k):v for k,v in json.loads(terminology.read_text(encoding='utf8')).items()})
 descriptions=P/'description_review09.json'
 menu_review=P/'menu_review09.json'
 if menu_review.exists():
  out.update({norm(k):v for k,v in json.loads(menu_review.read_text(encoding='utf8')).items()})
 if descriptions.exists():
  out.update({norm(k):v for k,v in json.loads(descriptions.read_text(encoding='utf8')).items()})
 from canonical_names import canonicalize
 return {k:canonicalize(v) for k,v in out.items()}

@functools.lru_cache(None)
def glyph(ch):
 b=fb.kfont.encode(fb.kfont.render(ch))
 return b''.join(b[j:j+2][::-1] for j in range(0,24,2))

def parts(raw,ids,field=True):
 out=[];buf='';saved=b''
 for kind,b,value in (tokens if field else common_tokens)(raw,ids,labels):
  if kind=='glyph':buf+=value;saved+=b
  elif kind=='control' and value==0x4000: saved+=b
  else:
   if saved:out.append(('text',saved,buf));buf='';saved=b''
   out.append((kind,b,value))
 if saved:out.append(('text',saved,buf))
 return out

def make(m,cache,glyph_order=0,custom_order=None):
 compact=P/'compact_system_translations.json'
 if compact.exists():
  short=json.loads(compact.read_text(encoding='utf8')).get(str(m))
  if short:cache={**cache,**{norm(k):v for k,v in short.items()}}
 tuning=P/'font_order_overrides.json'
 if glyph_order==0 and tuning.exists():
  tuned=json.loads(tuning.read_text(encoding='utf8')).get(str(m))
  if tuned is not None:glyph_order=66;custom_order=tuned
 r=fe.read(m);n=struct.unpack_from('<I',r['font'])[0];font=r['font'];protected={}
 oldpatch=ROOT/'work/story_patch'/f'member{m}_korean.bin'
 if oldpatch.exists():
  protected={i:None for mm,i in fb.T if mm==m}
 nbase=struct.unpack_from('<I',font)[0]
 widths=bytearray(font[8:8+nbase]);glyphs=[font[8+nbase+i*24:8+nbase+(i+1)*24] for i in range(nbase)]
 if protected:
  for i in protected:
   old=bytes.fromhex(r['rows'][i]['hex']);text=wrap_dialogue(fb.T[m,i])
   prefix=old[:10] if re.match(r'^\d{5}',r['rows'][i]['jp']) else b''
   if old.startswith(b'\x85\x80'):prefix+=b'\x85\x80'
   endings=[b'\x86\x80\x78\x00\x00',b'\x86\x80\x00\x00\x00',b'\x81\x80\x00',b'\x82\x80\x00']
   end=next(e for e in endings if old.endswith(e))
   payload=[('raw',bytes.fromhex(t[1:-1]),None) if t.startswith('{') else ('ko',b'',t) for t in re.findall(r'\{[0-9a-f]+\}|[^{}]+',text)]
   protected[i]=[('raw',prefix,None)]+payload+[('raw',end,None)]
 # Slots 235..260 are shared punctuation too, including interpreter-significant
 # quote and bracket codes. Reusing them can change wrapping/name behavior.
 used=set(range(1,261));newrows=[];changed=[];missing=set();whole_messages=[]
 for row in r['rows']:
  i=row['index'];raw=bytes.fromhex(row['hex'])
  whole=replacement(m,i,raw,r['ids'],labels)
  if whole is not None:
   newrows.append(whole);changed.append(i);whole_messages.append(i)
   continue
  if i in protected:
   newrows.append(protected[i]);changed.append(i)
   continue
  seg=parts(raw,r['ids']);result=[];did=False
  for j,(kind,b,s) in enumerate(seg):
   if kind=='text':
    prefix=b''
    if j==0 and re.match(r'^\d{5}',s):prefix=b[:10];s=s[5:];b=b[10:]
    if prefix:result.append(('raw',prefix,None))
    if JP.search(s):
     key=norm(s)
     if key not in cache:missing.add(key)
     else:result.append(('ko',b,cache[key]));did=True;continue
   result.append(('raw',b,None))
   if kind=='text':
    for kk,bb,vv in tokens(b,r['ids'],labels):
     if kk=='glyph':used.add(bb[0] if len(bb)==1 else (bb[0]&127)+128*bb[1])
  newrows.append(result)
  if did:changed.append(i)
 if missing:raise ValueError(('missing translations',len(missing),list(missing)[:3]))
 # Shared lowercase slots form the name alphabet. Literal Latin letters in
 # unmodified scripts must move to normal translated slots before replacement.
 from name_encoding import FIELD_SLOTS,ALIASES
 slots=set(FIELD_SLOTS.values())
 for row_index,row in enumerate(newrows):
  revised=[]
  for kind,raw,value in row:
   if kind=='ko':revised.append((kind,raw,value));continue
   for tk,bb,vv in tokens(raw,r['ids'],labels):
    slot=(bb[0] if len(bb)==1 else (bb[0]&127)+128*bb[1]) if tk=='glyph' else -1
    revised.append(('ko',b'',vv) if slot in slots else ('raw',bb,None))
  newrows[row_index]=revised
 chars=sorted({ch for row in newrows for kind,b,s in row if kind=='ko' for ch in s})
 shared_mapping=dict(FIELD_SLOTS)
 for alias,ch in ALIASES.items():
  slot=FIELD_SLOTS[ch];assert labels.get(r['ids'][slot-1])==alias,(m,slot)
  glyphs[slot-1]=glyph(ch);widths[slot-1]=12
 if glyph_order>=33:
  for ch in chars:
   if ch in ' .()･':
    source='\u3000' if ch==' ' else ch
    candidates=[i+1 for i,gid in enumerate(r['ids'][:260]) if labels.get(gid)==source]
    if candidates:shared_mapping[ch]=candidates[0]
 chars=[ch for ch in chars if ch not in shared_mapping]
 order_id=glyph_order%33
 if order_id==1:chars.sort(key=lambda ch:(glyph(ch),ch))
 elif order_id==2:chars.sort(key=lambda ch:(glyph(ch)[::-1],ch))
 elif 3<=order_id<=26:
  shift=2*((order_id-3)%12)
  def row_key(ch):
   bitmap=glyph(ch);rotated=bitmap[shift:]+bitmap[:shift]
   return (rotated[::-1] if order_id>=15 else rotated,ch)
  chars.sort(key=row_key)
 elif order_id>=27:
  orders=[(0,1,2),(0,2,1),(1,0,2),(1,2,0),(2,0,1),(2,1,0)]
  order=orders[order_id-27]
  def jamo_key(ch):
   v=ord(ch)-0xac00
   if not 0<=v<11172:return (-1,ord(ch),0)
   jamo=(v//588,(v//28)%21,v%28)
   return tuple(jamo[i] for i in order)
  chars.sort(key=jamo_key)
 if custom_order is not None:
  if set(chars)==set(custom_order) and len(chars)==len(custom_order):chars=list(custom_order)
  else:custom_order=None;glyph_order=33
 mapping=dict(shared_mapping);free=[v for v in range(261,nbase+1) if v not in used]
 for ch in chars:
  if free:v=free.pop(0)
  else:v=len(glyphs)+1;glyphs.append(bytes(24));widths.append(0)
  mapping[ch]=v;glyphs[v-1]=glyph(ch);widths[v-1]=6 if ord(ch)<128 else 12
 while len(glyphs)%4:glyphs.append(bytes(24));widths.append(0)
 font=struct.pack('<II',len(glyphs),12)+widths+b''.join(glyphs)
 data=bytearray();offs=[]
 for row in newrows:
  offs.append(len(data))
  for kind,b,s in row:
   if kind!='ko':data.extend(b);continue
   # Redistribute translated text over the original line breaks, keeping all control bytes.
   chunks=wrap_fixed(s,b.count(b'\x80\x80')+1,fixed_cells=True)
   data.extend(b'\x80\x80'.join(b''.join(fb.enc(mapping[ch]) for ch in chunk) for chunk in chunks))
 if len(data)>=65536:raise ValueError(('text offset overflow',len(data)))
 script=bytearray(r['script'][:r['table']]);struct.pack_into('<I',script,16,len(data));script+=struct.pack(f'<{len(offs)}H',*offs)+data
 blob=bytearray();sizes=[]
 for i,part in enumerate([bytes(script),font]):
  mode,comp,unp,link,_=r['chain'][i];payload=part if mode==0 else fe.slz.compress_payload(part,mode)
  if (i==0 and len(payload)>comp and mode in (0,1)) or (i==1 and mode==0):
   alt=fe.slz.compress_payload(part,2)
   if len(alt)<len(payload):mode=2;payload=alt
  if i==1 and mode!=2 and len(blob)+16+len(payload)>r['b']-r['a']:
   alt=fe.slz.compress_payload(part,2)
   if len(alt)<len(payload):mode=2;payload=alt
  if i==0 and len(payload)>comp:raise ValueError(('script allocation overflow',len(payload),comp))
  if i==0:payload=payload.ljust(comp,b'\0')
  else:link=0
  sizes.append(len(payload));blob+=b'SLZ'+bytes([mode])+struct.pack('<III',len(payload),len(part),link)+payload
  if link:blob+=bytes(link-16-len(payload))
 if len(blob)>r['b']-r['a']:
  if glyph_order<65:return make(m,cache,glyph_order+1)
  if custom_order is None:
   from font_packing import optimize
   limit=r['b']-r['a']-r['chain'][0][3]-16
   order=optimize(chars,mapping,glyphs,widths,limit,fe.slz.compress_payload,glyph)
   return make(m,cache,66,order)
  raise ValueError(('map slot overflow',len(blob),r['b']-r['a']))
 assert fe.slz.decompress(blob)==bytes(script)+font
 body=bytearray(r['orig']);body[r['a']:r['b']]=blob.ljust(r['b']-r['a'],b'\0')
 assert body[:r['a']]==r['orig'][:r['a']] and body[r['b']:]==r['orig'][r['b']:]
 # Control byte streams and metadata remain byte-for-byte unchanged outside protected Story06 rows.
 offs.append(len(data))
 for row in r['rows']:
  i=row['index']
  if i in protected and i not in whole_messages:continue
  before=bytes.fromhex(row['hex']);after=bytes(data[offs[i]:offs[i+1]])
  if i in whole_messages:
   assert control_signature(before,r['ids'])==control_signature(after,list(range(len(glyphs)))),(m,i,'whole message control mismatch')
   if re.match(r'^\d{5}',row['jp']):assert before[:10]==after[:10]
   continue
  cb=lambda d,ids:[b for kind,b,v in tokens(d,ids,{}) if kind!='glyph']
  assert cb(before,r['ids'])==cb(after,list(range(len(glyphs)))),(m,i,'control mismatch')
  if re.match(r'^\d{5}',row['jp']):assert before[:10]==after[:10]
 dest=P/'members';dest.mkdir(exist_ok=True);(dest/f'member{m}_korean.bin').write_bytes(body)
 if custom_order is not None:
  saved=json.loads(tuning.read_text(encoding='utf8')) if tuning.exists() else {}
  saved[str(m)]=custom_order
  tuning.write_text(json.dumps(saved,ensure_ascii=False,indent=1),encoding='utf8')
 return dict(member=m,translated=len(changed),total=len(newrows),reviewed_whole_messages=len(whole_messages),preserved_story06=len(protected),glyph_order=glyph_order,font_before=n,font_after=len(glyphs),slot=r['b']-r['a'],used=len(blob),sha256=hashlib.sha256(body).hexdigest())

def main():
 cache=load_cache();ms=[x['member'] for x in json.loads((P/'inventory.json').read_text(encoding='utf8'))['banks']]
 if len(sys.argv)>1:ms=list(map(int,sys.argv[1:]))
 good=[];bad=[];start=time.time()
 for m in ms:
  try:good.append(make(m,cache))
  except Exception as e:bad.append(dict(member=m,error=repr(e)))
  if (len(good)+len(bad))%20==0:print(len(good),'ok',len(bad),'failed',round(time.time()-start),'s',flush=True)
  (P/'field_build_report.json').write_text(json.dumps(dict(success=good,errors=bad),ensure_ascii=False,indent=1),encoding='utf8')
 print('DONE',len(good),len(bad),bad[:8],flush=True)
if __name__=='__main__':main()
