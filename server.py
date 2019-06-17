import logging
from websocket_server import WebsocketServer
import asyncio
import pproxy
import json
import uuid
import subprocess as sb
import socket
import base64
import threading



import sys
avs = sys.argv
print(avs)
if (len(avs) == 1):
    portoffest=0
    server_name = "ps0"
if (len(avs) == 2):
    portoffest=int(avs[1])
    server_name = "ps"+avs[1]

client_count = 0
    
proxy = sb.Popen("./run.sh -m pproxy -l socks5://0.0.0.0:{}".format(8651+(portoffest*2)+1),shell=True)
sessions = {}

def socketListenThread(client,server,session):
    try:
        while (session in sessions.keys()):
            data = sessions[session].recv(20480)
            if (data != b''):
                encoded = base64.b64encode(data).decode("UTF-8")
                #print(data)
                #print(encoded)
                server.send_message(client,json.dumps({"session":session,"type":"reply","data":encoded}))
            else:
                server.send_message(client,json.dumps({"session":session,"type":"close"}))
                sock = sessions[session]
                del sessions[session]
                sock.close()
    except BrokenPipeError:
        print("PIPE ERROR")
        sock = sessions[session]
        del sessions[session]
        sock.close()
            
def new_client(client, server):
    server.send_message(client,json.dumps({"session":None,"type":"welcome","data":None}))
    print("New Client!")
    global client_count
    client_count = client_count +1
    saveLive()
def close_client(client,server):
    global client_count
    client_count = client_count -1
    saveLive()
def message_received(client,server,msg):
    data = json.loads(msg)
    #print(msg)
    ses = data["session"]
    name = data["type"]
    raw = data["data"]
    #print(raw)
    #print(raw.encode("UTF-8"))
    #print(base64.b64decode(raw.encode("UTF-8")))
    #print(base64.b64decode(raw.encode("UTF-8")).decode("UTF-8"))
    datas = base64.b64decode(raw.encode("UTF-8"))
    print(ses+" > "+name)
    if (name == "open"):
        sessions[ses] = socket.socket()
        sessions[ses].connect(("localhost",8651+(portoffest*2)+1))
        thd = threading.Thread(target=socketListenThread,daemon=True,args=([client,server,ses]))
        thd.start()
    if (name == "request"):
        sessions[ses].send(datas)
    if (name == "close"):
        sock = sessions[ses]
        del sessions[ses]
        sock.close()
        
def saveLive():
    global client_count
    data = json.load(open("web/live.json"))
    data[server_name] = {"clients":client_count}
    raw = json.dumps(data)
    f = open("web/live.json","w")
    f.write(raw)
    f.close()
    
server = WebsocketServer(8651+(portoffest*2), host='127.0.0.1', loglevel=logging.INFO)
server.set_fn_new_client(new_client)
server.set_fn_client_left(close_client)
server.set_fn_message_received(message_received)
server.run_forever()
