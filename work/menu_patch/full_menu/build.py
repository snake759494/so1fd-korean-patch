from pathlib import Path
import sys,json,struct,re,shutil,hashlib
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'work/tools'))
sys.path.insert(0,str(Path(__file__).parent))
import tree,slz,so1pack,kfont,iso9660
from extract import g,cat,parse_resource
from translations import T
OUT=Path(__file__).parent
def codes(b):
 i=0
 while i<len(b):
  v=b[i];i+=1
  if v>=128:v=(v&127)+128*b[i];i+=1
  if v in (0x4006,0x400c):i+=1
  if 0<v<0x4000:yield v
def enc(v):return bytes([v]) if v<128 else bytes([(v&127)|128,v>>7])
def repack(n,replacements):
 if n.path in replacements:return replacements[n.path]
 if n.kind=='offtable':
  chunks=[repack(k,replacements) for k in n.kids]
  if all(c==k.data for c,k in zip(chunks,n.kids)):return n.data
  prefix=bytearray(n.data[:n.slots[0][0]]);body=bytearray()
  relocated={}
  for c,(a,b) in zip(chunks,n.slots):
   relocated[a]=len(prefix)+len(body);body.extend(c);body.extend(b'\0'*(-len(body)%4))
   relocated[b]=len(prefix)+len(body)
  for i in range(len(prefix)//4):
   old=struct.unpack_from('<I',n.data,i*4)[0]
   struct.pack_into('<I',prefix,i*4,relocated[old] if old else 0)
  return bytes(prefix+body)
 if n.kind=='raw':return n.data
 if not any(k.startswith(n.path) for k in replacements):return n.data
 raise ValueError(('unhandled',n.kind,n.path))
def make(m,p):
 orig=p.read(m);root=parse_resource(orig,m);top=root.kids[0]
 assert root.kind=='slz' and len(slz.parse_chain(orig))==1
 rows=json.loads((OUT/f'{m}.json').read_text(encoding='utf8'))['rows']
 changes={r['id']:T[r['id']] for r in rows if r['id'] in T and r['jp']!=T[r['id']]}
 ids=g['banks'][next(c['key'] for c in cat if c['member']==m and (c['path']==f'{m}/1' or m==2353))]['ids']
 used=set(range(1,234))
 for r in rows:
  if r['id'] not in changes:used.update(codes(bytes.fromhex(r['hex'])))
 font=tree.find(root,f'{m}!/1').data;n,h=struct.unpack_from('<II',font);assert n==len(ids) and h==12
 widths=bytearray(font[8:8+n]);glyphs=[font[8+n+i*24:8+n+(i+1)*24] for i in range(n)]
 chars=sorted(set(''.join(re.sub(r'\{[0-9a-f]+\}','',s) for s in changes.values())))
 mapping={}
 # Exact ASCII and punctuation reuse; OCR is never used to encode Japanese.
 for ch in chars:
  if ord(ch)<128 or ch in '　·♥':
   match=next((i+1 for i,u in enumerate(ids) if g['label'].get(u)==ch),None)
   if match:mapping[ch]=match;used.add(match)
 free=[v for v in range(234,n+1) if v not in used]
 for ch in chars:
  if ch in mapping:continue
  if free:v=free.pop(0)
  else:v=len(glyphs)+1;glyphs.append(bytes(24));widths.append(12)
  mapping[ch]=v;bits=kfont.render(ch);assert bits.any() or ch in '　 ',repr(ch)
  b=kfont.encode(bits);glyphs[v-1]=b''.join(b[j:j+2][::-1] for j in range(0,24,2));widths[v-1]=12 if '\uac00'<=ch<='\ud7a3' else kfont.advance(bits)
 newfont=struct.pack('<II',len(glyphs),12)+widths+b''.join(glyphs)
 replacements={f'{m}!/1':newfont}
 for group in sorted(set(r['group'] for r in rows if r['id'] in changes)):
  leaf=tree.find(root,f'{m}!/0/{group}');strings=leaf.data.split(b'\0')
  for r in rows:
   if r['group']!=group or r['id'] not in changes:continue
   s=changes[r['id']];out=bytearray()
   for token in re.findall(r'\{[0-9a-f]+\}|.',s):
    out.extend(bytes.fromhex(token[1:-1]) if token.startswith('{') else enc(mapping[token]))
   strings[r['index']]=bytes(out)
  after=b'\0'.join(strings)
  replacements[leaf.path]=after
 inner=repack(top,replacements)
 mode=orig[3];payload=slz.compress_payload(inner,mode)
 if len(payload)>len(orig)-16 and mode==1:
  alt=slz.compress_payload(inner,2)
  if len(alt)<len(payload):mode=2;payload=alt
 # Keep original member allocation and compressed size where possible; decoded
 # allocation and internal offsets reflect the explicit font/table expansion.
 oldcomp,oldunp,nxt=struct.unpack_from('<III',orig,4);assert nxt==0
 print(m,'strings',len(changes),'font',n,'->',len(glyphs),'payload',len(payload),'retail',oldcomp,'slot',len(orig),flush=True)
 assert len(payload)<=len(orig)-16,(m,'compressed slot overflow')
 comp=max(oldcomp,len(payload));patched=b'SLZ'+bytes([mode])+struct.pack('<III',comp,len(inner),0)+payload
 patched=patched.ljust(16+comp,b'\0')+orig[16+comp:]
 assert len(patched)==len(orig) and slz.decompress(patched)==inner
 check=parse_resource(patched,m)
 for path,data in replacements.items():assert tree.find(check,path).data.startswith(data),(m,path)
 (OUT/f'member{m}_korean.bin').write_bytes(patched)
 return patched,{'member':m,'strings':len(changes),'old_font':n,'new_font':len(glyphs),'mapping':mapping,'translations':changes,'unpacked_before':oldunp,'unpacked_after':len(inner)}
def main():
 p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin');patches={};reports=[]
 for m in sorted(set(int(k.split(':')[0]) for k in T)):
  patched,report=make(m,p);patches[m]=patched;reports.append(report)
 (OUT/'build_report.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
 if '--iso' in sys.argv:
  source=ROOT/'Star Ocean - First Departure (Japan).iso';target=ROOT/'Star Ocean - First Departure (Korean Menus 02).iso'
  patches[2329]=(OUT.parent/'member2329_korean.bin').read_bytes()
  iso=iso9660.Iso(source);base=iso.find('/PSP_GAME/USRDIR/so1pack.bin').lba*2048;iso.close()
  shutil.copyfile(source,target)
  with target.open('r+b') as f:
   for m,data in patches.items():f.seek(base+p.offsets[m]);f.write(data)
  print(target)
if __name__=='__main__':main()
