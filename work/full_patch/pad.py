from ppsspp_rpc import Debugger
import time,sys
d=Debugger()
try:
 if d.call('cpu.status').get('stepping'):d.call('cpu.resume')
 d.call('input.buttons.send',buttons={x:False for x in 'up down left right circle cross triangle square start ltrigger rtrigger'.split()})
 for button in sys.argv[1:]:
  parts=button.split(':');duration=int(parts[1]) if len(parts)>1 else 3
  d.call('input.buttons.press',button=parts[0],duration=duration)
  time.sleep(duration/30+.25)
  print(button,flush=True)
finally:
 if not d.call('cpu.status').get('stepping'):d.call('cpu.stepping')
 d.close()
