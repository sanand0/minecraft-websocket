import asyncio
import websockets
import json                 # noqa: for later use
from uuid import uuid4      # noqa: for later use
import re                   # noqa: for later use


# On Minecraft, when you type "/connect localhost:3000" it creates a connection
async def mineproxy(websocket, path):
    print('Connected')

# Create a new websocket server on port 3000
start_server = websockets.serve(mineproxy, host="localhost", port=3000)
print('Ready. On MineCraft chat, type /connect localhost:3000')

# Run the websocket server forever. Stop it with Ctrl+C or killing the process
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
