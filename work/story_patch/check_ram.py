from field_extract import *
import capstone
ram=(ROOT/'work/menu_patch/full_menu'/sys.argv[1]).read_bytes()
md=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
for addr in [0x088049b4,144090276-40]:
 print('DIS',hex(addr))
 for x in md.disasm(ram[addr-0x08100000:addr-0x08100000+160],addr):print(hex(x.address),x.mnemonic,x.op_str)
for m in [2425]:
 r=read(m);new=(OUT/f'member{m}_korean.bin').read_bytes();c,t=expand.as_typed_chunks(new);a,b=c[t.index(1)];ch=slz.parse_chain(new[a:b]);d=slz.decompress(new[a:b]);s=d[:ch[0][2]];f=d[ch[0][2]:]
 at=ram.find(f[:8]);print('font',m,hex(at),len(f),'equal',ram[at:at+len(f)]==f,'after',ram[at+len(f):at+len(f)+48].hex());print('script exact',hex(ram.find(s)))
 dif=[i for i,(x,y) in enumerate(zip(f,ram[at:at+len(f)])) if x!=y];print('dif',dif[:30],len(dif))
