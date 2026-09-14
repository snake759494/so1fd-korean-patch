from build import *
import subprocess

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 report=json.loads((OUT/'iso_report.json').read_text());source=Path(report['source']);target=Path(report['target']);iso=iso9660.Iso(source);ranges=[(x['offset'],x['offset']+x['size']) for x in report['members']]
 for name in report['executable']:
  e=iso.find('/PSP_GAME/SYSDIR/'+name);ranges.append((e.lba*2048,e.lba*2048+e.size))
 iso.close();ranges.sort();cursor=0;outside=0;changed=0
 with source.open('rb') as a,target.open('rb') as b:
  for start,end in ranges+[(source.stat().st_size,source.stat().st_size)]:
   assert start>=cursor
   while cursor<start:
    count=min(1024*1024,start-cursor);assert a.read(count)==b.read(count),('outside allowed ranges',cursor);outside+=count;cursor+=count
   old=a.read(end-start);new=b.read(end-start);changed+=sum(x!=y for x,y in zip(old,new));cursor=end
 srcsha=digest(source);assert srcsha=='5a3568fc8c2d3b2fed2cd468dafcde80bad72689794812f9159bfd18554c50cc'
 targetsha=digest(target);delta=OUT/'SO1_Korean_Menus_04.xdelta';roundtrip=OUT/'roundtrip_check.iso'
 subprocess.run([str(ROOT/'xdelta.exe'),'-f','-e','-s',str(source),str(target),str(delta)],check=True)
 subprocess.run([str(ROOT/'xdelta.exe'),'-f','-d','-s',str(source),str(delta),str(roundtrip)],check=True)
 assert digest(roundtrip)==targetsha;roundtrip.unlink()
 result={'original_sha256':srcsha,'patched_sha256':targetsha,'iso_bytes':target.stat().st_size,'modified_members':len(report['members']),'all_changed_bytes':changed,'unchanged_bytes_outside_allocated_ranges':outside,'delta_bytes':delta.stat().st_size,'delta_roundtrip':'PASS','outside_ranges':'IDENTICAL','original_unchanged':'PASS'}
 (OUT/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
