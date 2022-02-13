import asyncio
import websockets
import json  # noqa: for later use
from uuid import uuid4  # noqa: for later use
import re  # noqa: for later use


# On Minecraft, when you type "/connect localhost:3000" it creates a connection
async def mineproxy(websocket):
    print('Connected')
    send_queue = []         # Queue of commands to be sent
    awaited_queue = {}      # Queue of responses awaited from Minecraft

    async def send(cmd):
        '''Send a command "cmd" to MineCraft'''
        msg = {
            "header": {
                "version": 1,
                "requestId": f'{uuid4()}',        # A unique ID for the request
                "messagePurpose": "commandRequest",
                "messageType": "commandRequest"
            },
            "body": {
                "version": 1,
                "commandLine": cmd,               # Define the command
                "origin": {
                    "type": "player"              # Message comes from player
                }
            }
        }
        send_queue.append(msg)                    # Add the message to the queue

    async def draw_pyramid(size):
        '''Draw a pyramid of size "size" around the player.'''
        # y is the height of the pyramid. Start with y=0, and keep building up
        for y in range(0, size + 1):
            # At the specified y, place blocks in a rectangle of size "side"
            side = size - y
            for x in range(-side, side + 1):
                await send(f'setblock ~{x} ~{y} ~{-side} glowstone')
                await send(f'setblock ~{x} ~{y} ~{+side} glowstone')
                await send(f'setblock ~{-side} ~{y} ~{x} glowstone')
                await send(f'setblock ~{+side} ~{y} ~{x} glowstone')

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
            if msg['body'].get('eventName', None) == 'PlayerMessage':
                match = re.match(r'^pyramid (\d+)', msg['body']['properties']['Message'],
                                 re.IGNORECASE)
                if match:
                    await draw_pyramid(int(match.group(1)))
            # If we get a command response, act on it
            if msg['header']['messagePurpose'] == 'commandResponse':
                # ... and it's for an awaited command
                if msg['header']['requestId'] in awaited_queue:
                    # Print errors (if any)
                    if msg['body']['statusCode'] < 0:
                        print(awaited_queue[msg['header']['requestId']]['body']['commandLine'],
                              msg['body']['statusMessage'])
                    # ... and delete it from the awaited queue
                    del awaited_queue[msg['header']['requestId']]
            # Now, we've cleared all completed commands from the awaited_queue.

            # We can send new commands from the send_queue -- up to a maximum of 100.
            count = 100 - len(awaited_queue)
            for command in send_queue[:count]:
                # Send the command in send_queue, and add it to the awaited_queue
                await websocket.send(json.dumps(command))
                awaited_queue[command['header']['requestId']] = command
            send_queue = send_queue[count:]
            # Now we've sent as many commands as we can. Wait till the next message
    # When MineCraft closes a connection, it raises this Exception.
    except websockets.exceptions.ConnectionClosedError:
        print('Disconnected from MineCraft')


async def main():
    async with websockets.serve(mineproxy, host='localhost', port=3000):
        print('Ready. On MineCraft chat, type /connect localhost:3000. Press Ctrl+C to stop')
        await asyncio.Future()


asyncio.run(main())
