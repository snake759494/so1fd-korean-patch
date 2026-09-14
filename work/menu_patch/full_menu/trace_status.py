import websocket,json,time
w=websocket.create_connection('ws://127.0.0.1:49742/debugger',subprotocols=['debugger.ppsspp.org'],timeout=5)
def req(e,**kw):
 w.send(json.dumps(dict(event=e,ticket=e,**kw)))
 while True:
  r=json.loads(w.recv())
  if r.get('ticket')==e:return r
try:
 print(req('memory.breakpoint.add',address=0x094a5ca4,size=4,enabled=True,read=True,write=False,change=False))
 req("input.buttons.send",buttons={"circle":True})
 time.sleep(.15)
 req("input.buttons.send",buttons={"circle":False})
 time.sleep(.2)
 print(req('cpu.status'))
 r=req('cpu.getAllRegs')['categories'][0];print(dict(zip(r['registerNames'],[hex(v) for v in r['uintValues']])))
finally:
 print(req('memory.breakpoint.remove',address=0x094a5ca4,size=4))
 w.send(json.dumps({'event':'cpu.resume'}));w.shutdown()

