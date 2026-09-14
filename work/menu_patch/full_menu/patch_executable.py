from build import *
BASE=0x08803fac
NAMES=[(bytes.fromhex('d7c3a8'),b'QJ'),(bytes.fromhex('d0d8b0'),b'YZ'),(bytes.fromhex('c4deb0dd'),b';')]
def I(op,rs,rt,imm):return op<<26|rs<<21|rt<<16|(imm&65535)
def J(op,addr):return op<<26|((addr>>2)&0x3ffffff)
def wrapper(addr,strings,tail,stolen=[]):
 words=[]
 for i,(jp,alias) in enumerate(NAMES):
  fix=[]
  for off,v in enumerate(jp+b'\0'):
   words += [I(36,5,8,off),I(9,0,9,v)]
   fix.append(len(words));words += [I(5,8,9,0),0]
  a=strings[i];words += [I(15,0,5,a>>16),I(13,5,5,a&65535)]
  endfix=len(words);words += [0,0]
  for k in fix:words[k]|=len(words)-k-1
  # Successful matches skip the remaining comparisons.
  words[endfix]=('end',)
 end=len(words)
 for k,v in enumerate(words):
  if isinstance(v,tuple):words[k]=I(4,0,0,end-k-1)
 words+=stolen+[J(2,tail),0]
 return struct.pack('<%dI'%len(words),*words)
def generic8(addr):
 words=[];labels={};fix=[]
 def emit(*xs):words.extend(xs)
 def label(n):labels[n]=len(words)
 def branch(op,rs,rt,n):fix.append((len(words),n));emit(I(op,rs,rt,0),0)
 emit(I(9,29,29,-112),I(43,29,31,108),I(43,29,5,104),I(9,5,12,0),I(9,29,13,16),I(9,0,14,0))
 label('loop')
 for i,(jp,alias) in enumerate(NAMES):
  for off,v in enumerate(jp+b'\0'):
   emit(I(36,12,8,off),I(9,0,9,v));branch(5,8,9,'next'+str(i))
  for off,v in enumerate(alias+b'\0'):emit(I(9,0,8,v),I(40,13,8,off))
  emit(I(9,29,5,16));branch(4,0,0,'draw');label('next'+str(i))
 emit(I(36,12,8,0));branch(4,8,0,'fallback');emit(I(40,13,8,0),I(9,12,12,1),I(9,13,13,1),I(9,14,14,1),I(10,14,9,60));branch(5,9,0,'loop')
 label('fallback');emit(I(35,29,5,104))
 label('draw');call=len(words);emit(0,0,I(35,29,31,108),I(9,29,29,112),0x03e00008,0)
 trampoline=addr+len(words)*4;words[call]=J(3,trampoline)
 emit(I(9,29,29,-32),I(43,29,31,12),J(2,0x0883e20c),0)
 for k,n in fix:words[k]|=(labels[n]-k-1)&65535
 return struct.pack('<%dI'%len(words),*words)

def main():
 src=ROOT/'work/extract/PSP_GAME/SYSDIR/BOOT.BIN';b=bytearray(src.read_bytes());original=bytes(b)
 first=struct.unpack_from('<8I',b,52);cave=(first[2]+first[5]+15)&~15
 fileoff=(first[1]+first[4]+15)&~15
 phoff=len(b)-64
 # Reuse the non-loadable section table area; no game code/data is discarded.
 assert fileoff>=first[1]+first[4] and fileoff+1024<=phoff
 straddr=cave;strings=[straddr,straddr+4,straddr+8];payload=bytearray(b'QJ\0\0YZ\0\0;\0\0\0');payload+=bytes(16-len(payload))
 hook8=cave+len(payload);payload+=generic8(hook8)
 hook12=cave+len(payload);off=0x0883eb20-BASE;stolen=list(struct.unpack_from('<2I',b,off));payload+=wrapper(hook12,strings,0x0883eb28,stolen)
 assert fileoff+len(payload)<=phoff
 b[fileoff:fileoff+len(payload)]=payload
 struct.pack_into('<I',b,28,phoff);struct.pack_into('<I',b,32,0);struct.pack_into('<H',b,44,2);struct.pack_into('<HH',b,48,0,0)
 struct.pack_into('<8I',b,phoff,*first);struct.pack_into('<8I',b,phoff+32,1,fileoff,cave,0,len(payload),len(payload),7,16)
 assert struct.unpack_from('<2I',b,0x0883e204-BASE)==(I(9,29,29,-32),I(43,29,31,12))
 struct.pack_into('<2I',b,0x0883e204-BASE,J(2,hook8),0);struct.pack_into('<2I',b,off,J(2,hook12),0)
 # The two menu counters use dedicated ASCII aliases in the small atlas.
 for off,jp,alias in [(0x207c0f,'ﾌｫﾙ',b'#'),(0x207c23,'ｴﾝｶｳﾝﾀｰ',b'$&=['),(0x20509a,'ｴﾝｶｳﾝﾀｰ',b'$&=[')]:
  old=jp.encode('cp932');assert b[off:off+len(old)]==old;b[off:off+len(old)]=alias.ljust(len(old),b' ')
 (OUT/'BOOT_korean.bin').write_bytes(b)
 (OUT/'executable_report.json').write_text(json.dumps({'original_sha256':hashlib.sha256(original).hexdigest(),'patched_sha256':hashlib.sha256(b).hexdigest(),'segment_address':hex(cave),'segment_file_offset':fileoff,'segment_size':len(payload),'hooks':[hex(hook8),hex(hook12)],'note':'Exact-name display aliases only; stored names unchanged.'},indent=2))
 print('ELF display hooks',hex(cave),len(payload),len(b))
if __name__=='__main__':main()
