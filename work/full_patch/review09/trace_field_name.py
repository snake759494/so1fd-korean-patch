import sys,time,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P))
from ppsspp_rpc import Debugger
d=Debugger();address=int(sys.argv[1],0) if len(sys.argv)>1 else 0x094a5ca4;size=4
addresses=[address] if len(sys.argv)>1 else [0x08a04c40,0x08a0b380,0x094a6e5c,0x094a76c4]
try:
 for address in addresses:print(d.call('memory.breakpoint.add',address=address,size=size,enabled=True,read=True,write=False,change=False))
 if d.call('cpu.status').get('stepping'):d.call('cpu.resume')
 for _ in range(3):
  d.call('input.buttons.send',buttons={'circle':True});time.sleep(.2)
  d.call('input.buttons.send',buttons={'circle':False});time.sleep(.2)
  if d.call('cpu.status').get('stepping'):break
 status=d.call('cpu.status');print(status)
 if not status.get('stepping'):d.call('cpu.stepping')
 regs=d.call('cpu.getAllRegs');(P/'review09/field_name_trace.json').write_text(json.dumps(dict(status=status,regs=regs),indent=1))
 r=regs['categories'][0];print(dict(zip(r['registerNames'],[hex(v) for v in r['uintValues']])))
finally:
 for address in addresses:print(d.call('memory.breakpoint.remove',address=address,size=size))
 d.close()
