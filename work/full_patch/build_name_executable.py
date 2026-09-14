"""Build default-name and lowercase name-renderer support in the existing ELF cave."""
import struct,json,hashlib
from pathlib import Path
from name_encoding import defaults,ALIASES
P=Path(__file__).resolve().parent;ROOT=P.parents[1];BASE=0x08803fac
def I(op,rs,rt,imm):return op<<26|rs<<21|rt<<16|(imm&65535)
def J(op,addr):return op<<26|((addr>>2)&0x3ffffff)
def pack(words):return struct.pack('<%dI'%len(words),*words)

def main():
 src=ROOT/'work/extract/PSP_GAME/SYSDIR/BOOT.BIN';b=bytearray(src.read_bytes())
 first=struct.unpack_from('<8I',b,52);cave=(first[2]+first[5]+15)&~15
 fileoff=(first[1]+first[4]+15)&~15;phoff=len(b)-64
 payload=bytearray();hooks=[]
 # Display adapters recognize only exact original default names. Custom names
 # remain untouched; legacy saves need no on-disk modification.
 pairs=defaults()+[('ﾗﾃｨ'.encode('cp932'),defaults()[0][1])]
 for jp,alias in pairs:
  assert len(jp)<10 and len(alias)<6
  payload.extend(jp.ljust(10,b'\0')+alias.ljust(6,b'\0'))
 normalize=cave+len(payload)
 w=[];labels={};fixups=[]
 def emit(*xs):w.extend(xs)
 def label(name):labels[name]=len(w)
 def branch(op,rs,rt,name):fixups.append((len(w),name));emit(I(op,rs,rt,0),0)
 emit(I(15,0,8,cave>>16),I(13,8,8,cave&65535),I(9,0,9,len(pairs)))
 label('row');emit(I(9,5,10,0),I(9,8,11,0))
 label('char');emit(I(36,10,12,0),I(36,11,13,0));branch(5,12,13,'next')
 branch(4,12,0,'match');emit(I(9,10,10,1),I(9,11,11,1));branch(4,0,0,'char')
 label('next');emit(I(9,8,8,16),I(9,9,9,-1));branch(5,9,0,'row');emit(0x03e00008,0)
 label('match');emit(I(9,8,5,10),0x03e00008,0)
 for index,name in fixups:w[index]|=(labels[name]-index-1)&65535
 payload.extend(pack(w))
 def hook(addr,words,expected):
  off=addr-BASE;assert list(struct.unpack_from('<2I',b,off))==expected,(hex(addr),'unexpected instructions')
  dest=cave+len(payload);payload.extend(pack(words));struct.pack_into('<2I',b,off,J(2,dest),0)
  hooks.append(dict(address=hex(addr),target=hex(dest),bytes=len(words)*4))
 for addr,stack,raoff in [(0x0883e204,32,12),(0x0883eb20,416,28)]:
  stolen=[I(9,29,29,-stack),I(43,29,31,raoff)]
  hook(addr,stolen+[J(3,normalize),0,J(2,addr+8),0],stolen)
 # The field renderer uses a transient 20-byte name cache. Normalize an old
 # default there before the shared width/draw pass, leaving save files alone.
 words=[I(9,16,5,0),J(3,normalize),0,I(4,5,16,9),0,I(9,16,9,0),
        I(36,5,8,0),I(40,9,8,0),I(4,8,0,4),0,
        I(9,5,5,1),I(9,9,9,1),I(4,0,0,-7),0,
        I(36,16,2,0),I(9,0,19,0),J(2,0x08949e40),0]
 hook(0x08949e38,words,[I(36,2,2,0x31c),0x00009821])
 # a0 points to a name character, result is its field-font slot; other bytes
 # use the original kana/Latin converter. Lowercase aliases occupy a..x only.
 words=[I(35,4,3,0),I(9,3,7,-97),I(11,7,7,24),I(4,7,0,5),0,
        I(9,3,3,111),I(43,4,3,0),0x03e00008,I(9,0,2,0),
        I(10,3,7,0xa6),J(2,0x08949ef4),0]
 hook(0x08949eec,words,[I(35,4,3,0),I(10,3,7,0xa6)])
 # The menu converter searches a kana table. Handle a..x directly before
 # that search, producing dedicated table indices 1..24.
 # Preserve v1 (the next-source-byte pointer) on the fallback path.
 words=[I(9,11,14,-97),I(11,14,1,24),I(4,1,0,4),0,
        (5<<21)|(15<<16)|(3<<11)|0x21,J(2,0x0883b900),0,
        I(36,3,6,0),I(9,6,3,-0xde),J(2,0x0883b8b0),0]
 hook(0x0883b8a8,words,[I(36,3,6,0),I(9,6,3,-0xde)])
 # PSP name-entry conversion uses its own font and normally folds lowercase
 # to uppercase. Emit the appended Hangul slots directly for a..x only.
 words=[I(9,16,8,-97),I(11,8,9,24),I(4,9,0,11),0,
        I(9,16,8,144),I(12,8,9,127),I(13,9,9,128),I(40,18,9,0),
        (8<<16)|(9<<11)|(7<<6)|2,I(40,18,9,1),I(9,18,18,2),J(2,0x0884bac4),0,
        I(15,0,2,0x08a3),I(35,2,4,-0x2ef0),J(2,0x0884bb3c),0]
 # Branch target is the original two-instruction prologue at index 13.
 words[2]=I(4,9,0,10)
 hook(0x0884bb34,words,[I(15,0,2,0x08a3),I(35,2,4,-0x2ef0)])
 # Battle HUD has another conversion table which folds a..z to uppercase.
 # Send the name aliases directly to the patched 8x8 atlas cells instead.
 words=[I(9,16,8,-97),I(11,8,9,24),I(4,9,0,4),0,
        I(9,16,2,-32),J(2,0x0884b950),0,
        I(15,0,2,0x08a3),I(35,2,4,-0x2ef0),J(2,0x0884b938),0]
 hook(0x0884b930,words,[I(15,0,2,0x08a3),I(35,2,4,-0x2ef0)])
 changes=[]
 for jp,alias in defaults():
  assert len(alias)<=len(jp)
  needle=jp+b'\0';start=0;hits=[]
  while True:
   off=b.find(needle,start)
   if off<0:break
   assert off>=0x1f0000,(jp,off)
   b[off:off+len(jp)]=alias.ljust(len(jp),b'\0');hits.append(off);start=off+len(needle)
  assert hits,(jp,'default absent')
  changes.append(dict(jp=jp.decode('cp932'),alias=alias.decode(),offsets=hits))
 # The protagonist's unit template uses the short Japanese nickname in a
 # verified 16-byte name field, unlike the 20-byte default-name table.
 off=2100228;old='ﾗﾃｨ'.encode('cp932')
 assert b[off:off+16]==old.ljust(16,b'\0')
 b[off:off+16]=defaults()[0][1].ljust(16,b'\0')
 changes[0]['unit_template_offset']=off
 for off,jp,alias in [(0x207c0f,'ﾌｫﾙ',b'#'),(0x207c23,'ｴﾝｶｳﾝﾀｰ',b'$&=['),(0x20509a,'ｴﾝｶｳﾝﾀｰ',b'$&=[')]:
  old=jp.encode('cp932');assert b[off:off+len(old)]==old;b[off:off+len(old)]=alias.ljust(len(old),b' ')
 assert fileoff+len(payload)<=phoff
 b[fileoff:fileoff+len(payload)]=payload
 struct.pack_into('<II',b,28,phoff,0);struct.pack_into('<H',b,44,2);struct.pack_into('<HH',b,48,0,0)
 struct.pack_into('<8I',b,phoff,*first)
 struct.pack_into('<8I',b,phoff+32,1,fileoff,cave,0,len(payload),len(payload),7,16)
 (P/'BOOT_names_korean.bin').write_bytes(b)
 report=dict(sha256=hashlib.sha256(b).hexdigest(),defaults=changes,hooks=hooks,
             aliases=ALIASES,note='New-game defaults and exact legacy-default display adapters. Custom names and saved files are preserved.')
 (P/'review09/name_executable_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf8')
 print('Name executable built:',len(changes),'defaults;',len(payload),'hook bytes')
if __name__=='__main__':main()
