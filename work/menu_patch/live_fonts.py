from pathlib import Path
import sys,ctypes,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ramsearch import k32,regions,read
from fieldbank import fonts
import so1pack,tree
k32.OpenProcess.restype=ctypes.c_void_p
k32.VirtualQueryEx.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t]
k32.ReadProcessMemory.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p]
h=k32.OpenProcess(0x410,False,int(sys.argv[1]))
base,size=next((b,s) for b,s in regions(h) if s==0x1f00000)
d=read(h,base,size)
tag=sys.argv[2];out=Path(__file__).parent/'full_menu';out.mkdir(exist_ok=True)
(out/f'{tag}_ram.bin').write_bytes(d)
fs=fonts(d);cat=json.loads((Path(__file__).resolve().parents[1]/'banks.json').read_text())
p=so1pack.Pack(Path(__file__).resolve().parents[1]/'extract/PSP_GAME/USRDIR/so1pack.bin')
cache={};rows=[]
for f in fs:
 matches=[]
 for c in cat:
  if c['count']!=f['count']:continue
  m=c['member']
  if m not in cache:cache[m]=tree.parse(p.read(m),str(m))
  path=c['path'].replace(str(m)+'/',str(m)+'!/',1)
  leaf=tree.find(cache[m],path) or tree.find(cache[m],c['path'])
  if leaf and d[f['hdr']:f['hdr']+8+f['count']*25]==leaf.data[c['hdr']:c['hdr']+8+c['count']*25]:matches.append(c['key'])
 rows.append({**f,'matches':matches})
(out/f'{tag}_fonts.json').write_text(json.dumps(rows,indent=2))
print(json.dumps({'hostbase':hex(base),'fonts':rows}))
