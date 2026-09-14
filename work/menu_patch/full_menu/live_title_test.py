from build import *
import websocket,base64
w=websocket.create_connection('ws://127.0.0.1:49742/debugger',subprotocols=['debugger.ppsspp.org'],timeout=10)
b=(OUT/'member5053_korean.bin').read_bytes();n,ot,st,start=struct.unpack_from('<4I',b);ram=(OUT/'title04_ram.bin').read_bytes()
for i in range(1,5):
 old=(OUT/f'title{i}_before.bin').read_bytes();addr=ram.find(old)+0x08000000;assert addr>0x08000000
 o=struct.unpack_from('<I',b,ot+4*i)[0];size=struct.unpack_from('<I',b,st+4*i)[0];new=b[o:o+size];w.send(json.dumps(dict(event='memory.write',ticket=str(i),address=addr,base64=base64.b64encode(new).decode())))
 while json.loads(w.recv()).get('ticket')!=str(i):pass
 print(i,hex(addr))
w.shutdown()
