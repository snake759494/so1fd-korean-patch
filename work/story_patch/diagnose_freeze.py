from field_extract import *
import capstone
ram=(ROOT/'work/menu_patch/full_menu/house_freeze06_ram.bin').read_bytes()
md=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
def dis(a,n):
 for x in md.disasm(ram[a-0x08800000:a-0x08800000+n],a):print(hex(x.address),x.mnemonic,x.op_str)
dis(143914008-40,100)
for m in [2415,2417,2419,2425,2427]:
 r=read(m);new=(OUT/f'member{m}_korean.bin').read_bytes();c,t=expand.as_typed_chunks(new);a,b=c[t.index(1)];ch=slz.parse_chain(new[a:b]);print(m,'old',r['chain'],'new',ch)
print('font RAM',hex(0x08800000+22393408))
