const WebSocket = require('ws')
const uuid = require('uuid')

// Create a new websocket server on port 3000
console.log('Ready. On MineCraft chat, type /connect localhost:3000')
const wss = new WebSocket.Server({ port: 3000 })

// On Minecraft, when you type "/connect localhost:3000" it creates a connection
wss.on('connection', socket => {
  console.log('Connected')

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

  // When MineCraft sends a message (e.g. on player chat), act on it.
  socket.on('message', packet => {
    const msg = JSON.parse(packet)
    // If this is a chat window
    if (msg.body.eventName === 'PlayerMessage') {
      // ... and it's like "pyramid 10" (or some number), draw a pyramid
      const match = msg.body.properties.Message.match(/^pyramid (\d+)/i)
      if (match)
        draw_pyramid(+match[1])
    }
  })
})
