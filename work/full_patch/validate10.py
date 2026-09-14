from build_fields import *
import subprocess
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 r=json.loads((P/'iso_report.json').read_text(encoding='utf8'));source=Path(r['source']);target=Path(r['target'])
 assert digest(source)=='b252819da7507303ded9903a77fce879548e740e2e46acf27e23237e74246b50'
 original=ROOT/'Star Ocean - First Departure (Japan).iso'
 assert digest(original)=='5a3568fc8c2d3b2fed2cd468dafcde80bad72689794812f9159bfd18554c50cc'
 assert source.stat().st_size==target.stat().st_size
 cursor=0;outside=0
 with source.open('rb') as a,target.open('rb') as b:
  for x in sorted(r['changes'],key=lambda x:x['offset'])+[dict(offset=target.stat().st_size,size=0)]:
   start=x['offset'];assert start>=cursor
   while cursor<start:
    n=min(1024*1024,start-cursor);assert a.read(n)==b.read(n),cursor;cursor+=n;outside+=n
   a.seek(x['size'],1);data=b.read(x['size']);cursor+=x['size']
   if x['size']:assert hashlib.sha256(data).hexdigest()==x['sha256']
 audit=[]
 for q in json.loads((P/'field_build_report.json').read_text(encoding='utf8'))['success']:
  m=q['member'];old=fe.read(m);body=(P/f'members/member{m}_korean.bin').read_bytes()
  chunks,types=fe.expand.as_typed_chunks(body);assert chunks==fe.expand.as_typed_chunks(old['orig'])[0]
  a,b=chunks[types.index(1)];chain=fe.slz.parse_chain(body[a:b]);u=fe.slz.decompress(body[a:b]);s=u[:chain[0][2]];font=u[chain[0][2]:]
  assert chain[0][1]==old['chain'][0][1] and chain[0][3]==old['chain'][0][3]
  assert s[:16]==old['script'][:16] and s[20:old['table']]==old['script'][20:old['table']]
  n,h=struct.unpack_from('<II',font);assert n%4==0 and h==12 and len(font)==8+n*25
  original_n=struct.unpack_from('<I',old['font'])[0];shared=min(260,original_n)
  from name_encoding import FIELD_SLOTS
  names_by_slot={v:k for k,v in FIELD_SLOTS.items()}
  for slot in range(1,shared+1):
   expected=glyph(names_by_slot[slot]) if slot in names_by_slot else old['font'][8+original_n+(slot-1)*24:8+original_n+slot*24]
   width=12 if slot in names_by_slot else old['font'][7+slot]
   assert font[7+slot]==width,(m,slot,'shared width mismatch')
   assert font[8+n+(slot-1)*24:8+n+slot*24]==expected,(m,slot,'shared glyph mismatch')
  head=struct.unpack_from('<7I',s);table=head[0]+28;base=table+head[3]*2;offs=list(struct.unpack_from(f'<{head[3]}H',s,table))+[head[4]]
  assert base+head[4]==len(s) and offs==sorted(offs)
  for i in range(head[3]):list(tokens(s[base+offs[i]:base+offs[i+1]],list(range(n)),{}))
  for row in old['rows']:
   i=row['index'];before=bytes.fromhex(row['hex']);after=s[base+offs[i]:base+offs[i+1]]
   if any(k=='control' and v==0x400d for k,d,v in tokens(before,old['ids'],{})):
    assert control_signature(before,old['ids'])[2]==control_signature(after,list(range(n)))[2],(m,i,'special symbol changed')
  audit.append(m)
 print('Field audit PASS',len(audit),flush=True)
 delta=P/'SO1_Korean_Review_10.xdelta';rt=P/'roundtrip_check_10.iso'
 subprocess.run([str(ROOT/'xdelta.exe'),'-f','-e','-s',str(original),str(target),str(delta)],check=True)
 subprocess.run([str(ROOT/'xdelta.exe'),'-f','-d','-s',str(original),str(delta),str(rt)],check=True)
 sha=digest(target);assert digest(rt)==sha;rt.unlink()
 result=dict(iso=str(target),sha256=sha,iso_bytes=target.stat().st_size,field_banks_audited=len(audit),outside_patched_ranges='IDENTICAL',outside_bytes=outside,delta_roundtrip='PASS',delta_bytes=delta.stat().st_size,runtime='Runtime10 must be checked against this exact hash separately',translation_quality='8730 whole-message reviews; menus, layout and runtime require separate quality verification')
 (P/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
