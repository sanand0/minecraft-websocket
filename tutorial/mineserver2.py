import asyncio
import websockets
import json                 # noqa: for later use
from uuid import uuid4      # noqa: for later use
import re                   # noqa: for later use


# On Minecraft, when you type "/connect localhost:3000" it creates a connection
async def mineproxy(websocket):
    print('Connected')

    # Tell Minecraft to send all chat messages. Required once when Minecraft starts
    await websocket.send(
        json.dumps({
            "header": {
                "version": 1,                     # Use version 1 message protocol
                "requestId": f'{uuid4()}',        # A unique ID for the request
                "messageType": "commandRequest",  # This is a request ...
                "messagePurpose": "subscribe"     # ... to subscribe to ...
            },
            "body": {
                "eventName": "PlayerMessage"
            },
        }))

    try:
        # When MineCraft sends a message (e.g. on player chat), print it.
        async for msg in websocket:
            msg = json.loads(msg)
            print(msg)
    # When MineCraft closes a connection, it raises this Exception.
    except websockets.exceptions.ConnectionClosedError:
        print('Disconnected from MineCraft')


async def main():
    async with websockets.serve(mineproxy, host='localhost', port=3000):
        print('Ready. On MineCraft chat, type /connect localhost:3000. Press Ctrl+C to stop')
        await asyncio.Future()


asyncio.run(main())
