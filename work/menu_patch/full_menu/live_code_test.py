from patch_executable import *
import websocket,base64,time
w=websocket.create_connection('ws://127.0.0.1:49742/debugger',subprotocols=['debugger.ppsspp.org'],timeout=10)
def req(e,**kw):
 w.send(json.dumps(dict(event=e,ticket=e,**kw)))
 while True:
  r=json.loads(w.recv())
  if r.get('ticket')==e:
   assert r.get('event')!='error',r
   return r
b=(OUT/'BOOT_korean.bin').read_bytes();ph=struct.unpack_from('<I',b,28)[0];s=struct.unpack_from('<8I',b,ph+32)
try:
 w.send(json.dumps({'event':'cpu.stepping'}))
 while json.loads(w.recv()).get('event')!='cpu.stepping':pass
 for addr,data in [(s[2],b[s[1]:s[1]+s[4]])]+[(a,b[a-BASE:a-BASE+8]) for a in [0x0883e204,0x0883eb20,0x0891518c]]:
  print(hex(addr),len(data),req('memory.write',address=addr,base64=base64.b64encode(data).decode()))
finally:
 w.send(json.dumps({'event':'cpu.resume'}));w.shutdown()
