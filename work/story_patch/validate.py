from pathlib import Path
import sys,json,hashlib,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 r=json.loads((OUT/'iso_report.json').read_text());base=Path(r['source']);target=Path(r['target']);original=ROOT/'Star Ocean - First Departure (Japan).iso'
 ranges=sorted((x['offset'],x['offset']+x['size']) for x in r['changes']);cursor=0;outside=0;changed=0
 assert base.stat().st_size==target.stat().st_size
 with base.open('rb') as a,target.open('rb') as b:
  for start,end in ranges+[(base.stat().st_size,base.stat().st_size)]:
   assert start>=cursor
   while cursor<start:
    n=min(1024*1024,start-cursor);assert a.read(n)==b.read(n),cursor;cursor+=n;outside+=n
   old=a.read(end-start);new=b.read(end-start);changed+=int(np.count_nonzero(np.frombuffer(old,'u1')!=np.frombuffer(new,'u1')));cursor=end
 assert digest(base)=='aa81d19bdaa54595ee47281785e4cd58086ffe7c2aec8eb305bb94a2be805956'
 osh=digest(original);assert osh=='5a3568fc8c2d3b2fed2cd468dafcde80bad72689794812f9159bfd18554c50cc'
 tsh=digest(target);delta=OUT/'SO1_Korean_Story_06.xdelta';rt=OUT/'roundtrip_check.iso'
 subprocess.run([str(ROOT/'xdelta.exe'),'-f','-e','-s',str(original),str(target),str(delta)],check=True)
 subprocess.run([str(ROOT/'xdelta.exe'),'-f','-d','-s',str(original),str(delta),str(rt)],check=True)
 assert digest(rt)==tsh;rt.unlink()
 res={'original_sha256':osh,'patched_sha256':tsh,'base_menu_patch_unchanged':'PASS','outside_story_ranges':'IDENTICAL','outside_bytes':outside,'changed_story_bytes':changed,'delta_roundtrip':'PASS','delta_bytes':delta.stat().st_size,'patch_applies_to':'Japanese original ISO','iso_bytes':target.stat().st_size}
 (OUT/'validation.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
if __name__=='__main__':main()
