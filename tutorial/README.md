# Programming Minecraft with Websockets

Minecraft lets you connect to a websocket server when you're in a game. The server can receive and send any commands. This lets you build a bot that you can ... (well, I don't know what it can do, let's explore.)

Minecraft has [commands](https://minecraft.gamepedia.com/Commands) you can type on a chat window. For example, type `/` to start a command and type `setblock ~1 ~0 ~0 grass` changes the block 1 north of you into grass. (`~` means relative to you. Coordinates are specified as X, Y and Z.)

![Minecraft grass block](img/minecraft-grass-block.png)

- [Programming Minecraft with Websockets](#programming-minecraft-with-websockets)
  - [Connect to Minecraft](#connect-to-minecraft)
  - [Subscribe to chat messages](#subscribe-to-chat-messages)
  - [Build structures using chat](#build-structures-using-chat)
  - [Understand Minecraft's responses](#understand-minecrafts-responses)
  - [Wait for commands to be done](#wait-for-commands-to-be-done)

Note:

- These instructions were tested on Minecraft Bedrock 1.16, 1.17 & 1.18. I haven't tested them on the Java Edition.

## Connect to Minecraft

You can send any command to Minecraft from a websocket server.

### Connect to Minecraft - JavaScript

On [Node.js](https://nodejs.org/) 10.0+, run `npm install ws uuid`. (We need [`ws`](https://npmjs.com/package/ws) for websockets and [`uuid`](https://npmjs.com/package/uuid) to generate unique IDs.)

Then create this [`mineserver1.js`](mineserver1.js):

```js
const WebSocket = require('ws')
const uuid = require('uuid')        // For later use

// Create a new websocket server on port 3000
console.log('Ready. On MineCraft chat, type /connect localhost:3000')
const wss = new WebSocket.Server({ port: 3000 })

// On Minecraft, when you type "/connect localhost:3000" it creates a connection
wss.on('connection', socket => {
  console.log('Connected')
})
```

Run `node mineserver1.js`. Then type `/connect localhost:3000` in a Minecraft chat window. You'll see 2 things:

1. MineCraft says "Connection established to server: ws://localhost:3000"
2. Node prints "Connected"

Now, our program is connected to Minecraft, and can send/receive messages.

[Check the troubleshooting guide if this doesn't work](#connect-to-minecraft-troubleshooting).

![Minecraft chat connect](img/minecraft-chat-connected.png)

### Connect to Minecraft - Python

On [Python](https://www.python.org/) 3.7+, run `pip install websockets`. (This installs the [`websockets`](https://pypi.org/project/websockets/) package.)

Then create this [`mineserver1.py`](mineserver1.py):

```py
import asyncio
import websockets
import json                 # noqa: for later use
from uuid import uuid4      # noqa: for later use


# On Minecraft, when you type "/connect localhost:3000" it creates a connection
async def mineproxy(websocket, path):
    print('Connected')

start_server = websockets.serve(mineproxy, host="localhost", port=3000)
print('Ready. On MineCraft chat, type /connect localhost:3000')

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
```

Run `python mineserver1.py`. Then type `/connect localhost:3000` in a Minecraft chat window. You'll see 2 things:

1. MineCraft says "Connection established to server: ws://localhost:3000"
2. Python prints "Connected"

Now, our program is connected to Minecraft, and can send/receive messages.

[Check the troubleshooting guide if this doesn't work](#connect-to-minecraft-troubleshooting).

![Minecraft chat connect](img/minecraft-chat-connected.png)

### Connect to Minecraft - Troubleshooting

- If Node says `Uncaught Error: Cannot find module 'ws'`, make sure you ran `npm install ws uuid`.
- If Python says `ModuleNotFoundError: No module named 'websockets'`, make sure you ran `pip install websockets`.
- If Node says `Error: listen EADDRINUSE: address already in use :::3000` or Python says`OSError: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 3000): only one usage of each socket address (protocol/network address/port) is normally permitted`, another process is using port 3000. Restart your machine, or use `netstat -ano` to see which process is using port 3000 and kill it.
- If MineCraft says `Could not connect to server: ws://localhost:3000`,
  - Go to [WebSocketKing.com](https://websocketking.com/) and connect to `ws://localhost:3000`. Check that it says "Connected to ws://localhost:3000" and Node prints "Connected".
  - [Minecraft might not connect to localhost](https://doc.pmmp.io/en/rtfd/faq/connecting/win10localhostcantconnect.html). find your IP address with [`ipconfig`](https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/ipconfig) or [`ifconfig`](https://en.wikipedia.org/wiki/Ifconfig). Replace `localhost:3000` with your IP address, e.g. `192.168.1.2:3000`).
- To disconnect, type `/connect off` in Minecraft. Or press Ctrl+C on Node / Python to stop the server.

## Subscribe to chat messages

Now let's listen to the players' chat.

A connected websocket server can send a "subscribe" message to Minecraft saying it wants to
"listen" to specific actions. For example, you can subscribe to "PlayerMessage". Whenever a player
sents a chat message, Minecraft will notify the websocket client.

Notes:

- The official Minecraft docs say that the [MCWSS protocol is outdated](https://minecraft.gamepedia.com/Commands/wsserver#Uses).
  But it seems to work.
- The full list of things we can subscribe to is undocumented, but
  [@jocopa3](https://gist.github.com/jocopa3/) has reverse-engineered a
  [list of messages](https://gist.github.com/jocopa3/5f718f4198f1ea91a37e3a9da468675c)
  we can subscribe to, and they're somewhat meaningful.
- [This Go package](https://github.com/Sandertv/mcwss/) has code that explores the
  [protocol](https://github.com/Sandertv/mcwss/tree/master/protocol) further.
- This [chat](https://www.reddit.com/r/MCPE/comments/5ta719/mcpewin10_global_chat_using_websockets/)
  has more details. There's also an
  [outdated list of JSON messages](https://gist.github.com/jocopa3/54b42fb6361952997c4a6e38945e306f)
  from [@jocopa3](https://gist.github.com/jocopa3/).
- Here's a sample program that
  [places a block in Minecraft](https://gist.github.com/pirosuke/1ca2aa4d8920f41dfbabcbc7dc2a669f)
- The `requestId` needs to be a UUID -- at least for block commands. I tried unique `requestId`
  values like 1, 2, 3 etc. That didn't work.


## Subscribe to chat messages - JavaScript

Add this code inside the `wss.on('connection', socket => { ... })` function.

```js
  // Tell Minecraft to send all chat messages. Required once when Minecraft starts
  socket.send(JSON.stringify({
    "header": {
      "version": 1,                     // Use version 1 message protocol
      "requestId": uuid.v4(),           // A unique ID for the request
      "messageType": "commandRequest",  // This is a request ...
      "messagePurpose": "subscribe"     // ... to subscribe to ...
    },
    "body": {
      "eventName": "PlayerMessage"      // ... all player messages.
    },
  }))
```

Now, every time a player types something in the chat window, the socket will receive it.

Add this code after the above code:

```js
  // When MineCraft sends a message (e.g. on player chat), print it.
  socket.on('message', packet => {
    const msg = JSON.parse(packet)
    console.log(msg)
  })
```

This code parses all the messages it receives and prints them.

This code in is [`mineserver2.js`](mineserver2.js).

- Run `node mineserver2.js`.
- Then type `/connect localhost:3000` in a Minecraft chat window.
- Then type a message (e.g. "alpha") in the chat window.
- You'll see a message like this in the console.

```js
{
  header: {
    messagePurpose: 'event',        // This is an event
    requestId: '00000000-0000-0000-0000-000000000000',
    version: 1                      // using version 1 message protocol
  },
  body: {
    eventName: 'PlayerMessage',
    measurements: null,
    properties: {
      AccountType: 1,
      ActiveSessionID: 'e0afde71-9a15-401b-ba38-82c64a94048d',
      AppSessionID: 'b2f5dddc-2a2d-4ec1-bf7b-578038967f9a',
      Biome: 1,                     // Plains Biome. https://minecraft.gamepedia.com/Biome
      Build: '1.16.201',            // That's my build
      BuildNum: '5131175',
      BuildPlat: 7,
      Cheevos: false,
      ClientId: 'fcaa9859-0921-348e-bc7c-1c91b72ccec1',
      CurrentNumDevices: 1,
      DeviceSessionId: 'b2f5dddc-2a2d-4ec1-bf7b-578038967f9a',
      Difficulty: 'NORMAL',         // I'm playing on normal difficulty
      Dim: 0,
      GlobalMultiplayerCorrelationId: '91967b8c-01c6-4708-8a31-f111ddaa8174',
      Message: 'alpha',             // This is the message I typed
      MessageType: 'chat',          // It's of type "chat"
      Mode: 1,
      NetworkType: 0,
      Plat: 'Win 10.0.19041.1',
      PlayerGameMode: 1,            // Creative. https://minecraft.gamepedia.com/Commands/gamemode
      Sender: 'Anand',              // That's me
      Seq: 497,
      WorldFeature: 0,
      WorldSessionId: '8c9b4d3b-7118-4324-ba32-c357c709d682',
      editionType: 'win10',
      isTrial: 0,
      locale: 'en_IN',
      vrMode: false
    }
  }
}
```

## Subscribe to chat messages - Python

Add this code inside the `async def mineproxy(websocket, path):` function.

```py
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
```

Now, every time a player types something in the chat window, the socket will receive it.

Add this code after the above code:

```py
    try:
        # When MineCraft sends a message (e.g. on player chat), print it.
        async for msg in websocket:
            msg = json.loads(msg)
            print(msg)
    # When MineCraft closes a connection, it raises this Exception.
    except websockets.exceptions.ConnectionClosedError:
        print('Disconnected from MineCraft')
```

This code parses all the messages it receives and prints them.

This code in is [`mineserver2.py`](mineserver2.py).

- Run `python mineserver2.py`.
- Then type `/connect localhost:3000` in a Minecraft chat window.
- Then type a message (e.g. "alpha") in the chat window.
- You'll see a message like this in the console.

```py
{
  "body": {
    "eventName": "PlayerMessage",
    "measurements": None,
    "properties": {
      "AccountType": 1,
      "ActiveSessionID": "da2210c5-564f-4657-8b77-4eb8eba7b6b1",
      "AppSessionID": "b2920a67-f639-4164-a9ce-60b613331289",
      "Biome": 1,               # Plains Biome. https://minecraft.gamepedia.com/Biome
      "Build": "1.18.2",        # That's my build
      "BuildNum": "7966245",
      "BuildPlat": 7,
      "Cheevos": False,
      "ClientId": "fcaa9859-0921-348e-bc7c-1c91b72ccec1",
      "CurrentNumDevices": 1,
      "DeviceSessionId": "b2920a67-f639-4164-a9ce-60b613331289",
      "Difficulty": "NORMAL",   # I'm playing on normal difficulty
      "Dim": 0,
      "DnAPlat": "Win,D,,UWP",
      "GlobalMultiplayerCorrelationId": "757aeca7-5664-4a03-880f-abe10ecbcd7f",
      "Message": "alpha",       # This is the message I typed
      "MessageType": "chat",    # It's of type "chat"
      "Mode": 1,
      "NetworkType": 0,
      "Plat": "Win 10.0.19041.1",
      "PlayerGameMode": 1,      # Creative. https://minecraft.gamepedia.com/Commands/gamemode
      "Sender": "sanand0",      # That's me
      "Seq": 90,
      "ServerId": "raknet:12172568328544955244",
      "UserId": "2535429213968507",
      "WorldFeature": 0,
      "WorldSessionId": "346f0991-8c84-460b-b42f-8696ce8c8a18",
      "editionType": "win10",
      "isTrial": 0,
      "isUnderground": False,
      "locale": "en_IN",
      "vrMode": False
    }
  },
  "header": {
    "messagePurpose": "event",    # This is an event
    "requestId": "00000000-0000-0000-0000-000000000000",
    "version": 1                  # using version 1 message protocol
  }
}
```

## Build structures using chat

Let's create a pyramid of size `10` around us when we type `pyramid 10` in the chat window.

### Build structures using chat - JavaScript

Check if the player sent a chat message like `pyramid 10` (or another number).
Replace the `console.log(msg)` line in [`mineserver2.js`](mineserver2.js) with this code:

```js
    // If this is a chat window
    if (msg.body.eventName === 'PlayerMessage') {
      // ... and it's like "pyramid 10" (or some number), draw a pyramid
      const match = msg.body.properties.Message.match(/^pyramid (\d+)/i)
      if (match)
        draw_pyramid(+match[1])
    }
```

If the user types "pyramid 3" on the chat window, `draw_pyramid(3)` is called.

In `draw_pyramid()`, let's send commands to build a pyramid. To send a command, we need to create a
JSON with the command (e.g. `setblock ~1 ~0 ~0 grass`).
Add this code under `console.log('Connected')` in [`mineserver2.js`](mineserver2.js):

```js
  // Send a command "cmd" to MineCraft
  function send(cmd) {
    const msg = {
      "header": {
        "version": 1,
        "requestId": uuid.v4(),     // Send unique ID each time
        "messagePurpose": "commandRequest",
        "messageType": "commandRequest"
      },
      "body": {
        "version": 1,
        "commandLine": cmd,         // Define the command
        "origin": {
          "type": "player"          // Message comes from player
        }
      }
    }
    socket.send(JSON.stringify(msg))  // Send the JSON string
  }
```

Let's write `draw_pyramid()` to create a pyramid using glowstone by adding this code below the
above code:

```js
  // Draw a pyramid of size "size" around the player.
  function draw_pyramid(size) {
    // y is the height of the pyramid. Start with y=0, and keep building up
    for (let y = 0; y < size + 1; y++) {
      // At the specified y, place blocks in a rectangle of size "side"
      let side = size - y;
      for (let x = -side; x < side + 1; x++) {
        send(`setblock ~${x} ~${y} ~${-side} glowstone`)
        send(`setblock ~${x} ~${y} ~${+side} glowstone`)
        send(`setblock ~${-side} ~${y} ~${x} glowstone`)
        send(`setblock ~${+side} ~${y} ~${x} glowstone`)
      }
    }
  }
```

This code in is [`mineserver3.js`](mineserver3.js).

- Run `node mineserver3.js`.
- Then type `/connect localhost:3000` in a Minecraft chat window.
- Then type `pyramid 3` in the chat window.
- You'll be surrounded by a glowstone pyramid.

![Minecraft glowstone pyramid](img/minecraft-glowstone-pyramid.png)

### Build structures using chat - Python

Check if the player sent a chat message like `pyramid 10` (or another number).
Replace the `print(msg)` line in [`mineserver2.py`](mineserver2.py) with with this code:

```py
            if msg['body'].get('eventName', None) == 'PlayerMessage':
                match = re.match(r'^pyramid (\d+)', msg['body']['properties']['Message'],
                                 re.IGNORECASE)
                if match:
                    await draw_pyramid(int(match.group(1)))
```

If the user types "pyramid 3" on the chat window, `draw_pyramid(3)` is called.

In `draw_pyramid()`, let's send commands to build a pyramid. To send a command, we need to create a
JSON with the command (e.g. `setblock ~1 ~0 ~0 grass`). Add this code below the above code:

```py
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
        await websocket.send(json.dumps(msg))     # Send the JSON string
```

Let's write `draw_pyramid()` to create a pyramid using glowstone by adding this code below the
above code:

```py
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
```

This code in is [`mineserver3.py`](mineserver3.py).

- Run `python mineserver3.py`.
- Then type `/connect localhost:3000` in a Minecraft chat window.
- Then type `pyramid 3` in the chat window.
- You'll be surrounded by a glowstone pyramid.

![Minecraft glowstone pyramid](img/minecraft-glowstone-pyramid.png)

## Understand Minecraft's responses

For every command you send, Minecraft sends a response. It's "header" looks like this:

```jsonc
{
  "header": {
    "version": 1,
    "messagePurpose": "commandResponse",                  // Response to your command
    "requestId": "97dee9a3-a716-4caa-aef9-ddbd642f2650"   // ... and your requestId
  }
}
```

If the command is successful, the response has `body.statusCode == 0`. For example:

```jsonc
{
  "body": {
    "statusCode": 0,                  // No error
    "statusMessage": "Block placed",  // It placed the block you wanted
    "position": { "x": 0, "y": 64, "z": 0 }   // ... at this location
  },
}
```

If the command failed, the response has a negative `body.statusCode`. For example:

```jsonc
{
  "body": {
    "statusCode": -2147352576,        // This is an error
    "statusMessage": "The block couldn't be placed"
  },
}
```

Some common error messages are:

- `The block couldn't be placed` (-2147352576):
  The same block was already at that location.
- `Syntax error: Unexpected "xxx": at "~0 ~9 ~-1 >>xxx<<"` (-2147483648):
  You gave wrong arguments to the command.
- `Too many commands have been requested, wait for one to be done` (-2147418109):
  Minecraft only allows 100 commands can be executed without waiting for their response.
- [More error messages here](https://github.com/CloudburstMC/Language/blob/master/en_GB.lang).

## Understand Minecraft's responses - JavaScript

To print these, add this to the end of `socket.on('message', ...)`:

```js
    // If we get a command response, print it
    if (msg.header.messagePurpose == 'commandResponse')
      console.log(msg)
```

This code in is [`mineserver4.js`](mineserver4.js).

- Run `node mineserver4.js`.
- Then type `/connect localhost:3000` in a Minecraft chat window.
- Then type `pyramid 3` in the chat window.
- You'll be surrounded by a glowstone pyramid, and the *console will show every command response*.

## Understand Minecraft's responses - Python

To print these, add this to the end of `socket.on('message', ...)`:

```js
    // If we get a command response, print it
    if (msg.header.messagePurpose == 'commandResponse')
      console.log(msg)
```

This code in is [`mineserver4.js`](mineserver4.js).

- Run `node mineserver4.js`.
- Then type `/connect localhost:3000` in a Minecraft chat window.
- Then type `pyramid 3` in the chat window.
- You'll be surrounded by a glowstone pyramid, and the *console will show every command response*.

## Wait for commands to be done

Typing "pyramid 3" works just fine. But try "pyramid 5" and your pyramid is incomplete.

![Minecraft incomplete pyramid](img/minecraft-incomplete-pyramid.png)

That's because Minecraft only allows up to 100 messages in its queue. On the 101st message, you get
a `Too many commands have been requested, wait for one to be done` error.

```json
{
  "header": {
    "version": 1,
    "messagePurpose": "error",
    "requestId": "a5051664-e9f4-4f9f-96b8-a56b5783117b"
  },
  "body": {
    "statusCode": -2147418109,
    "statusMessage": "Too many commands have been requested, wait for one to be done"
  }
}
```

So let's modify `send()` to add to a queue and send in batches.

## Wait for commands to be done -- JavaScript

We'll create two queues, one for commands yet to be sent, and another for commends sent - whose
response we're awaiting from MineCraft.

Add this code under `console.log('Connected')` in [`mineserver4.js`](mineserver4.js):

```js
  const sendQueue = []        // Queue of commands to be sent
  const awaitedQueue = {}     // Queue of responses awaited from Minecraft
```

Now, let's do 2 things:

1. When Minecraft sends a command response, we'll remove it from the `awaitedQueue`. (If
   the command has an error, we'll report it.)
2. Then, after processing Minecraft's command response, we'll send pending messages from
   `sendQueue`, upto 100 at a time, and add them to the `awaitedQueue`.

Replace the `if (msg.header.messagePurpose == 'commandResponse')` block in [`mineserver4.js`](mineserver4.js) with this:

```js
    // If we get a command response
    if (msg.header.messagePurpose == 'commandResponse') {
      // ... and it's for an awaited command
      if (msg.header.requestId in awaitedQueue) {
        // Print errors (if any)
        if (msg.body.statusCode < 0)
          console.log(awaitedQueue[msg.header.requestId].body.commandLine, msg.body.statusMessage)
        // ... and delete it from the awaited queue
        delete awaitedQueue[msg.header.requestId]
      }
    }
    // Now, we've cleared all completed commands from the awaitedQueue.

    // We can send new commands from the sendQueue -- up to a maximum of 100.
    let count = Math.min(100 - Object.keys(awaitedQueue).length, sendQueue.length)
    for (let i = 0; i < count; i++) {
      // Each time, send the first command in sendQueue, and add it to the awaitedQueue
      let command = sendQueue.shift()
      socket.send(JSON.stringify(command))
      awaitedQueue[command.header.requestId] = command
    }
    // Now we've sent as many commands as we can. Wait till the next message
```

Finally, in `function send()`, instead of `socket.send(JSON.stringify(msg))`, use:

```js
    sendQueue.push(msg)            // Add the message to the queue
```

This code in is [`mineserver5.js`](mineserver5.js).

- Run `node mineserver5.js`.
- Then type `/connect localhost:3000` in a Minecraft chat window.
- Then type `pyramid 6` in the chat window.
- You'll be surrounded by a large glowstone pyramid.
- The console will print messages like `setblock ~0 ~6 ~0 glowstone The block couldn't be placed`
  because we're trying to place duplicate blocks.

![Minecraft glowstone pyramid](img/minecraft-glowstone-pyramid-large.png)

## Wait for commands to be done -- Python

We'll create two queues, one for commands yet to be sent, and another for commends sent - whose
response we're awaiting from MineCraft.

Add this code under `print('Connected')` in [`mineserver4.py`](mineserver4.py):

```py
    send_queue = []         # Queue of commands to be sent
    awaited_queue = {}      # Queue of responses awaited from Minecraft
```

Now, let's do 2 things:

1. When Minecraft sends a command response, we'll remove it from the `awaited_queue`. (If
   the command has an error, we'll report it.)
2. Then, after processing Minecraft's command response, we'll send pending messages from
   `send_queue`, upto 100 at a time, and add them to the `awaited_queue`.

Replace the `if (msg.header.messagePurpose == 'commandResponse')` block in [`mineserver4.js`](mineserver4.js) with this:

```py
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
```

Finally, in `async def send()`, instead of `await websocket.send(json.dumps(msg))`, use:

```py
        send_queue.append(msg)          # Add the message to the queue
```

This code in is [`mineserver5.js`](mineserver5.js).

- Run `node mineserver5.js`.
- Then type `/connect localhost:3000` in a Minecraft chat window.
- Then type `pyramid 6` in the chat window.
- You'll be surrounded by a large glowstone pyramid.
- The console will print messages like `setblock ~0 ~6 ~0 glowstone The block couldn't be placed`
  because we're trying to place duplicate blocks.

![Minecraft glowstone pyramid](img/minecraft-glowstone-pyramid-large.png)
