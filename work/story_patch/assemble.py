from field_extract import ROOT,OUT,p
import iso9660,shutil,re,json,hashlib
SOURCE=ROOT/'Star Ocean - First Departure (Korean Menus 04).iso'
TARGET=ROOT/'Star Ocean - First Departure (Korean Story 06).iso'
def main():
 iso=iso9660.Iso(SOURCE);base=iso.find('/PSP_GAME/USRDIR/so1pack.bin').lba*2048
 changes=[]
 for f in OUT.glob('member*_korean.bin'):
  m=int(re.search(r'member(\d+)',f.name)[1]);d=f.read_bytes();assert len(d)==p.sizes[m]
  changes.append((base+p.offsets[m],d,{'member':m,'file':str(f)}))
 for f in OUT.glob('*_korean.pmf'):
  name=f.name.replace('_korean','');e=iso.find('/PSP_GAME/USRDIR/movie/'+name);d=f.read_bytes();assert len(d)==e.size
  changes.append((e.lba*2048,d,{'movie':name,'file':str(f)}))
 iso.close();shutil.copyfile(SOURCE,TARGET)
 report=[]
 with TARGET.open('r+b') as io:
  for off,d,meta in sorted(changes):io.seek(off);io.write(d);report.append(dict(offset=off,size=len(d),sha256=hashlib.sha256(d).hexdigest(),**meta))
 with TARGET.open('rb') as io:
  for off,d,_ in changes:io.seek(off);assert io.read(len(d))==d
 (OUT/'iso_report.json').write_text(json.dumps({'source':str(SOURCE),'target':str(TARGET),'changes':report},indent=2))
 print(TARGET,len(changes),flush=True)
if __name__=='__main__':main()
