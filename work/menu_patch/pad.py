import websocket,json,sys,time,uuid
w=websocket.create_connection('ws://127.0.0.1:49742/debugger',subprotocols=['debugger.ppsspp.org'],timeout=15)
def send(buttons):
 w.send(json.dumps({'event':'input.buttons.send','buttons':buttons,'ticket':'pad'}))
 while json.loads(w.recv()).get('ticket')!='pad':pass
send({b:False for b in 'up down left right circle cross triangle square start ltrigger rtrigger'.split()})
for button in sys.argv[1:]:
 ticket=str(uuid.uuid4())
 w.send(json.dumps({'event':'input.buttons.press','button':button,'duration':30 if button=='start' else 3,'ticket':ticket}))
 while json.loads(w.recv()).get('ticket')!=ticket:pass
 time.sleep(1.2)
 print(button,flush=True)
w.shutdown()





