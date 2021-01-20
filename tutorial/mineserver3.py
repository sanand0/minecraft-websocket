import re
import asyncio
import websockets
import json
from uuid import uuid4


# On Minecraft, when you type "/connect localhost:3000" it creates a connection
async def mineproxy(websocket, path):
    print('Connected')

    # Tell Minecraft to send all chat messages. Required once after Minecraft starts
    await websocket.send(
        json.dumps({
            "header": {
                "version": 1,                     # We're using the version 1 message protocol
                "requestId": str(uuid4()),        # A unique ID for the request
                "messageType": "commandRequest",  # This is a request ...
                "messagePurpose": "subscribe"     # ... to subscribe to ...
            },
            "body": {
                "eventName": "PlayerMessage"
            },
        }))

    def send(cmd):
        # TODO
        pass

    def draw_pyramid(size):
        # TODO
        pass

    try:
        # When MineCraft sends a message (e.g. on player chat), print it.
        async for msg in websocket:
            msg = json.loads(msg)
            if msg['body']['eventName'] == 'PlayerMessage':
                match = re.match(r'^pyramid (\d+)', msg['body']['properties']['Message'],
                                 re.IGNORECASE)
                if match:
                    draw_pyramid(int(match.group(1)))
    except websockets.exceptions.ConnectionClosedError:
        print('Disconnected from MineCraft')


start_server = websockets.serve(mineproxy, host="localhost", port=3000)
print('Ready. On MineCraft chat, type /connect localhost:3000')

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
