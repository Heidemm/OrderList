import json
import os
import threading
import time
import asyncio
import uvicorn
from fastapi import FastAPI, Body, Request, WebSocket
from typing import List
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.websockets import WebSocketDisconnect

app = FastAPI()
templates = Jinja2Templates("templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

connected_clients = []
orders = []


freshlist = []


waitlistOrders = []
inProgresslistOrders = []
readyOrders = []


lists_changed = False
delayTime = 30


def check_orders():
    while True:
        haveChanges = False
        removeArray = []
        for order in readyOrders:
            if order["time"] + delayTime <= time.time():
                haveChanges = True
                removeArray.append(order)
        for order in removeArray:
            readyOrders.remove(order)

        if haveChanges:
            asyncio.run(send_data())

        time.sleep(30)

threadCheckOrders = threading.Thread(target=check_orders)
threadCheckOrders.start()


async def send_data(haveNewPosition = False):
    data = json.dumps({'readylist' : readyOrders, 
                       'freshlist' : freshlist, 
                       'waitlistOrders' : waitlistOrders, 
                       'inProgresslistOrders' : inProgresslistOrders, 
                       'pictures' : [],
                       'haveNewPosition' : haveNewPosition})

    for client in connected_clients:
        try:
            await client["websocket"].send_text(data)       
        except WebSocketDisconnect:
            connected_clients.remove({"websocket": client["websocket"]})
    freshlist.clear()

async def recieve_data(textData):
    
    data = json.loads(textData)
    
    if data["action"] == "remove":
        if data["position"] == "0":
            for order in waitlistOrders:
                if order["orderNumber"] == data["orderNumber"]:
                    waitlistOrders.remove(order)
        else:
            for order in waitlistOrders:
                if order["orderNumber"] == data["orderNumber"]:
                    for position in order["positions"]:
                        if position["positionNumber"] == data["position"]:
                           order["positions"].remove(position)
                    if len(order["positions"]) == 0:
                                waitlistOrders.remove(order)
                

    if data["action"] == "moveToInProgress":
        if data["position"] == "0":
            for order in waitlistOrders:
                if order["orderNumber"] == data["orderNumber"]:
                    inProgresslistOrders.append(order)
                    waitlistOrders.remove(order)
        else:
            for order in waitlistOrders:
                if order["orderNumber"] == data["orderNumber"]:
                    for position in order["positions"]:
                        if position["positionNumber"] == data["position"]:
                            orderInProgress = False
                            for inProgressOrder in inProgresslistOrders:
                                if inProgressOrder["orderNumber"] == data["orderNumber"]:
                                    orderInProgress = True
                                    inProgressOrder["positions"].append(position)
                                    order["positions"].remove(position)
                            if orderInProgress == False:
                                orderCopy = {"orderNumber" : order["orderNumber"], "positions" : []}
                                orderCopy["positions"].append(position)
                                inProgresslistOrders.append(orderCopy)
                                order["positions"].remove(position)
                            if len(order["positions"]) == 0:
                                waitlistOrders.remove(order)

    if data["action"] == "done":
        if data["position"] == "0":
            for order in inProgresslistOrders:
                if order["orderNumber"] == data["orderNumber"]:
                    orderCopy = {"orderNumber" : order["orderNumber"], "time" : time.time()}
                    readyOrders.append(orderCopy)
                    freshlist.append(orderCopy["orderNumber"])
                    inProgresslistOrders.remove(order)        
        else:
            for order in inProgresslistOrders:
                if order["orderNumber"] == data["orderNumber"]:
                    for position in order["positions"]:
                        if position["positionNumber"] == data["position"]:
                           order["positions"].remove(position)
                    orderReady = False
                    for readyOrder in readyOrders:
                        if order["orderNumber"] == readyOrder["orderNumber"]:
                            orderReady = True
                    if orderReady == False:
                        orderCopy = {"orderNumber" : order["orderNumber"], "time" : time.time()}
                        readyOrders.append(orderCopy)
                        freshlist.append(orderCopy["orderNumber"])
                    if len(order["positions"]) == 0:
                        inProgresslistOrders.remove(order)

    await send_data()


@app.post("/SetOrderList")
async def set_order_list(data = Body()):
    for order in data["wait_orders"]:
        for waitlistOrder in waitlistOrders:
            if order["orderNumber"] == waitlistOrder["orderNumber"]:
                return {"status": "error", "text": "Заказ уже существует!"}      
        waitlistOrders.append(order)

    await send_data()

    return {"status": "ok"}

@app.post("/AddToOrderList")
async def add_to_order_list(data = Body()):
    for order in data["wait_orders"]:
        for waitlistOrder in waitlistOrders:
            if order["orderNumber"] == waitlistOrder["orderNumber"]:
                return {"status": "error", "text": "Заказ уже существует!"}      
        waitlistOrders.append(order)

    await send_data(True)

    return {"status": "ok"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    connected_clients.append({"websocket": websocket})
    
    #pictures = os.listdir(os.listdir(os.getcwd()+'\\static\\pictures'))
    pictures = []
    i = 0
    for data in os.walk("static/pictures"):
        for picture in data[2]:
            pictures.append({'src' : "static/pictures/"+picture, 'alt' : i})
            i += 1


    data = json.dumps({'readylist' : readyOrders, 
                       'freshlist' : freshlist, 
                       'waitlistOrders' : waitlistOrders, 
                       'inProgresslistOrders' : inProgresslistOrders, 
                       'pictures' : pictures,
                       'haveNewPosition' : False})
    try:
        await websocket.send_text(data)       
    except WebSocketDisconnect:
            connected_clients.remove({"websocket": websocket})
    
    try:
        while True:
            data = await websocket.receive_text()
            await recieve_data(data)
    except WebSocketDisconnect:
        connected_clients.remove({"websocket": websocket})

@app.get("/orders", response_class=HTMLResponse)
async def get_interface(request: Request):
    return templates.TemplateResponse(request = request, name = "orders.html", context={"hostname" : request.base_url.hostname, "port" : request.base_url.port})

@app.get("/", response_class=HTMLResponse)
async def get_intece(request: Request):
    return templates.TemplateResponse(request = request, name = "list.html", context={"hostname" : request.base_url.hostname, "port" : request.base_url.port})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")

#pip install fastapi
#pip install uvicorn[standard]
#pip install jinja2
#uvicorn main:app --host 0.0.0.0 --port 8000