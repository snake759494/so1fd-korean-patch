import websocket,json,sys,uuid
w=websocket.create_connection('ws://127.0.0.1:49742/debugger',subprotocols=['debugger.ppsspp.org'],timeout=5)
try:
 req=json.loads(sys.argv[1]);req['ticket']=str(uuid.uuid4());w.send(json.dumps(req))
 while True:
  r=json.loads(w.recv())
  if r.get('ticket')==req['ticket']:
   if req['event']=='memory.disasm':print('\n'.join(hex(x['address'])+' '+x['name']+' '+x['params'] for x in r.get('lines',[])))
   elif req['event']=='cpu.getAllRegs':print(dict(zip(r['categories'][0]['registerNames'],map(hex,r['categories'][0]['uintValues']))))
   else:print(json.dumps(r))
   break
finally:w.shutdown()
