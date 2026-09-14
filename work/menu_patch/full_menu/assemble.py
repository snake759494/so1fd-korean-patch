from build import *
def main():
 source=ROOT/'Star Ocean - First Departure (Japan).iso';target=ROOT/'Star Ocean - First Departure (Korean Menus 04).iso';p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin');iso=iso9660.Iso(source);base=iso.find('/PSP_GAME/USRDIR/so1pack.bin').lba*2048;entries=[iso.find('/PSP_GAME/SYSDIR/'+n) for n in ['BOOT.BIN','EBOOT.BIN']];iso.close();patches={int(re.search(r'member(\d+)',q.name)[1]):q.read_bytes() for q in OUT.glob('member*_korean.bin')};patches[2329]=(OUT.parent/'member2329_korean.bin').read_bytes();shutil.copyfile(source,target)
 report=[]
 with target.open('r+b') as f:
  for m,d in sorted(patches.items()):
   assert len(d)==p.sizes[m],(m,len(d),p.sizes[m]);at=base+p.offsets[m];f.seek(at);old=f.read(len(d));f.seek(at);f.write(d);report.append({'member':m,'offset':at,'size':len(d),'changed_bytes':sum(a!=b for a,b in zip(old,d))})
  boot=(OUT/'BOOT_korean.bin').read_bytes()
  for e in entries:
   assert len(boot)<=e.size;f.seek(e.lba*2048);f.write(boot.ljust(e.size,b'\0'))
 with target.open('rb') as f:
  for m,d in patches.items():f.seek(base+p.offsets[m]);assert f.read(len(d))==d
 (OUT/'iso_report.json').write_text(json.dumps({'source':str(source),'target':str(target),'members':report,'executable':['BOOT.BIN','EBOOT.BIN']},indent=2));print(target,len(patches),'members',sum(x['changed_bytes'] for x in report),'changed member bytes')
if __name__=='__main__':main()
