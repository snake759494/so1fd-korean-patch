from build_fields import ROOT,P,fe
import iso9660,shutil,re,json,hashlib,struct
SOURCE=ROOT/'Star Ocean - First Departure (Korean Story 06).iso'
TARGET=ROOT/'Star Ocean - First Departure (Korean Review 10).iso'
def main():
 titles=json.loads((P/'review09/item_title_build_report.json').read_text(encoding='utf8'))
 assert titles['rows']==1589 and len(titles['success'])==1589 and not titles['errors']
 assert titles['member_sha256']==hashlib.sha256((P/'members/member3731_korean.bin').read_bytes()).hexdigest()
 for name,count in [('field',974),('description',1589),('menu',16),('table',3)]:
  r=json.loads((P/f'{name}_build_report.json').read_text(encoding='utf8'))
  if isinstance(r,list):r=dict(success=[x for x in r if 'error' not in x],errors=[x for x in r if 'error' in x])
  assert not r['errors'],(name,r['errors'])
  assert len(r['success'])==count,(name,len(r['success']))
 iso=iso9660.Iso(SOURCE);base=iso.find('/PSP_GAME/USRDIR/so1pack.bin').lba*2048;changes=[]
 for f in (P/'members').glob('member*_korean.bin'):
  m=int(re.search(r'member(\d+)',f.name)[1]);d=f.read_bytes()
  if len(d)!=fe.p.sizes[m]:
   assert m==5053 and fe.p.sizes[m]<len(d)<=fe.p.offsets[m+1]-fe.p.offsets[m]
   with SOURCE.open('rb') as src:
    src.seek(base+fe.p.offsets[m]+fe.p.sizes[m]);assert not any(src.read(len(d)-fe.p.sizes[m]))
   changes.append((base+fe.p.size_tbl+4*m,struct.pack('<I',len(d)),{'size_table_member':m,'previous_size':fe.p.sizes[m]}))
  changes.append((base+fe.p.offsets[m],d,{'member':m,'file':str(f)}))
 for f in (P/'movies').glob('*_korean.pmf'):
  name=f.name.replace('_korean','');e=iso.find('/PSP_GAME/USRDIR/movie/'+name);d=f.read_bytes();assert len(d)==e.size
  changes.append((e.lba*2048,d,{'movie':name,'file':str(f)}))
 boot=P/'BOOT_names_korean.bin'
 if boot.exists():
  d=boot.read_bytes()
  for name in ('BOOT.BIN','EBOOT.BIN'):
   e=iso.find('/PSP_GAME/SYSDIR/'+name);assert len(d)<=e.size
   changes.append((e.lba*2048,d.ljust(e.size,b'\0'),{'executable':name,'file':str(boot)}))
 iso.close();shutil.copyfile(SOURCE,TARGET);report=[]
 with TARGET.open('r+b') as io:
  for off,d,meta in sorted(changes):io.seek(off);io.write(d);report.append(dict(offset=off,size=len(d),sha256=hashlib.sha256(d).hexdigest(),**meta))
 with TARGET.open('rb') as io:
  for off,d,_ in changes:io.seek(off);assert io.read(len(d))==d
 (P/'iso_report.json').write_text(json.dumps({'source':str(SOURCE),'target':str(TARGET),'changes':report},indent=2),encoding='utf8')
 print(TARGET,len(changes),flush=True)
if __name__=='__main__':main()
