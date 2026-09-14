import websocket,json,sys,uuid,time
w=websocket.create_connection('ws://127.0.0.1:49742/debugger',subprotocols=['debugger.ppsspp.org'],timeout=20)
try:
 ticket=str(uuid.uuid4());button=sys.argv[1];duration=int(sys.argv[2])
 assert 1<=duration<=600
 w.send(json.dumps({'event':'input.buttons.press','button':button,'duration':duration,'ticket':ticket}))
 while json.loads(w.recv()).get('ticket')!=ticket:pass
 time.sleep(.7);print(button,duration)
finally:w.shutdown()
