import asyncio
import websockets
import json                 # noqa: for later use
from uuid import uuid4      # noqa: for later use
import re                   # noqa: for later use


# On Minecraft, when you type "/connect localhost:3000" it creates a connection
async def mineproxy(websocket):
    print('Connected')


async def main():
    async with websockets.serve(mineproxy, host='localhost', port=3000):
        print('Ready. On MineCraft chat, type /connect localhost:3000. Press Ctrl+C to stop')
        await asyncio.Future()


asyncio.run(main())
