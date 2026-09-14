"""Reproducible, same-slot main menu proof-of-concept for ULJM05290."""
from pathlib import Path
import sys, struct, json, hashlib, shutil
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'work/tools'))
import tree, so1pack, slz, iso9660, kfont
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'Star Ocean - First Departure (Japan).iso'
TARGET = ROOT / 'Star Ocean - First Departure (Korean Menu Test 01).iso'
translations = {
 1: ['필살기·문장술','아이템','장비','스킬','상태','설정','전술','저장데이터'],
 2: ['작전','교체','진형','리더'],
 3: ['저장','로드','삭제'],
 4: ['상점','길드','장비도우미'],
 5: ['사용아이템','음식','무기','방어구','액세서리','소재','기타','귀중품','전투용','신규입수'],
 6: ['스킬습득','아이템제작','특기','합동특기','제작도감'],
 7: ['TIME','폴','전투횟수'],
}
def main():
 p=so1pack.Pack(ROOT/'work/extract/PSP_GAME/USRDIR/so1pack.bin')
 original=p.read(2329); t=tree.parse(original,'2329')
 font=bytearray(tree.find(t,'2329!/1').data)
 assert struct.unpack_from('<II',font)==(108,12)
 # Keep the common numbers, punctuation, control glyphs and TIME verbatim.
 mapping={c:v for c,v in zip('TIME',range(103,107))}
 chars=sorted(set(''.join(s for arr in translations.values() for s in arr))-set('TIME'))
 free=list(range(24,103))+[107,108]
 assert len(chars)<=len(free),(len(chars),len(free))
 mapping.update(zip(chars,free))
 for ch in chars:
  idx=mapping[ch]-1
  bits=kfont.render(ch)
  assert bits.any(),ch
  be=kfont.encode(bits)
  le=b''.join(be[j:j+2][::-1] for j in range(0,24,2))
  font[8+idx]=12 if '\uac00'<=ch<='\ud7a3' else kfont.advance(bits)
  at=8+108+idx*24
  font[at:at+24]=le
 tree.mark(t,'2329!/1',bytes(font))
 manifest=[]
 for group,strings in translations.items():
  path=f'2329!/0/{group}'; before=tree.find(t,path).data
  old=before.split(b'\0')
  assert len([x for x in old if x])==len(strings),(path,len(old),strings)
  encoded=b''.join(bytes(mapping[c] for c in s)+b'\0' for s in strings)
  assert len(encoded)<=len(before),(path,len(encoded),len(before))
  after=encoded.ljust(len(before),b'\0')
  tree.mark(t,path,after)
  manifest.extend({'group':group,'index':i,'japanese_hex':old[i].hex(),'korean':s} for i,s in enumerate(strings))
 patched=tree.build(t)
 assert len(patched)==len(original)
 assert slz.decompress(patched)==tree.build(t.kids[0])
 check=tree.parse(patched,'2329')
 for path in ['2329!/0/0','2329!/2']:
  assert tree.find(check,path).data==tree.find(tree.parse(original,'2329'),path).data
 inv={v:k for k,v in mapping.items()}
 for group,strings in translations.items():
  got=tree.find(check,f'2329!/0/{group}').data.split(b'\0')[:len(strings)]
  assert [''.join(inv[x] for x in s) for s in got]==strings
 iso=iso9660.Iso(SOURCE); entry=iso.find('/PSP_GAME/USRDIR/so1pack.bin')
 offset=entry.lba*2048+p.offsets[2329]
 iso.f.seek(offset); assert iso.f.read(len(original))==original; iso.close()
 shutil.copyfile(SOURCE,TARGET)
 with TARGET.open('r+b') as f: f.seek(offset);f.write(patched)
 h1=hashlib.sha256(); h2=hashlib.sha256(); changed=0; pos=0
 with SOURCE.open('rb') as a,TARGET.open('rb') as b:
  while True:
   x=a.read(4*1024*1024);y=b.read(len(x))
   if not x: assert not b.read(1);break
   h1.update(x);h2.update(y)
   if x!=y:
    for i,(v,w) in enumerate(zip(x,y)):
     if v!=w: assert offset<=pos+i<offset+len(original);changed+=1
   pos+=len(x)
 (OUT/'member2329_original.bin').write_bytes(original)
 (OUT/'member2329_korean.bin').write_bytes(patched)
 (OUT/'translations.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 report={'source':str(SOURCE),'target':str(TARGET),'source_sha256':h1.hexdigest(),'target_sha256':h2.hexdigest(),'member':2329,'iso_offset':offset,'slot_bytes':len(original),'changed_bytes':changed,'hangul_and_symbol_glyphs':len(chars),'available_slots':len(free),'strings':len(manifest),'mapping':mapping,'validation':'SLZ roundtrip, all strings decoded, non-target subtrees preserved, full ISO diff bounded to member 2329. Emulator validation pending.'}
 (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 kfont.sheet(chars,cols=16).save(OUT/'korean_glyphs.png')
 print(json.dumps({k:v for k,v in report.items() if k!='mapping'},ensure_ascii=False))
if __name__=='__main__':main()
