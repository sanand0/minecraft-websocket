const WebSocket = require('ws')
const uuid = require('uuid')

// Create a new websocket server on port 3000
console.log('Ready. On MineCraft chat, type /connect localhost:3000')
console.log('Then type "blocks 5" to save count of blocks by level into blocks.json')
const wss = new WebSocket.Server({ port: 3000 })

// On Minecraft, when you type "/connect localhost:3000" it creates a connection
wss.on('connection', socket => {
  console.log('Connected')
  const sendQueue = []        // Queue of commands to be sent
  const awaitedQueue = {}     // Queue of responses awaited from Minecraft
  const blocks = {}           // blocks[block][level] = count of blocks at that level

  // Tell Minecraft to send all chat messages. Required once after Minecraft starts
  socket.send(JSON.stringify({
    "header": {
      "version": 1,                     // We're using the version 1 message protocol
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
    // If this is a chat message
    if (msg.body.eventName === 'PlayerMessage') {
      // ... and it's like "blocks 10" (or some y-level), count # of blocks at that y-level
      const match = msg.body.properties.Message.match(/^blocks (\d+)/i)
      if (match)
        for (let y = 0; y > -match[1]; y--)
          for (let x = -30; x <= 30; x++)
            for (let z = -30; z <= 30; z++)
              send(`testforblock ~${x} ~${y} ~${z} air`)
    }
    // If we get a command response
    if (msg.header.messagePurpose == 'commandResponse') {
      // ... and it's for an awaited command
      if (msg.header.requestId in awaitedQueue) {
        // ... and it's like "... is Air (expected: ...)"
        const blockMatch = msg.body.statusMessage.match(/is (.*?) \(expected:/)
        if (blockMatch) {
          // We know what the block is, so add it to the block count
          let blockCount = blocks[blockMatch[1]] = blocks[blockMatch[1]] || {}
          blockCount[msg.body.position.y] = 1 + (blockCount[msg.body.position.y] || 0)
        }
        // ... and delete it from the awaited queue
        delete awaitedQueue[msg.header.requestId]
      }
    }
    // Now, we've cleared all completed commands from the awaitedQueue.
    // We can send new commands from the sendQueue -- up to a maximum of 100.
    const awaitedLength = Object.keys(awaitedQueue).length
    const count = Math.min(100 - awaitedLength, sendQueue.length)
    for (let i = 0; i < count; i++) {
      // Each time, send the first command in sendQueue, and add it to the awaitedQueue
      let command = sendQueue.shift()
      socket.send(JSON.stringify(command))
      awaitedQueue[command.header.requestId] = command
    }
    // If the queue is empty, save the block stats
    if (!sendQueue.length && !awaitedLength) {
      const fs = require('fs')
      fs.writeFileSync('blockcount.json', JSON.stringify(blocks, null, 2))
    }
    // Otherwise, print progress every 1000 commands
    else if (sendQueue.length % 1000 == 0)
      console.log(`Queue: ${sendQueue.length} Awaited: ${awaitedLength}`)
    // Now we've sent as many commands as we can. Wait till the next PlayerMessage/commandResponse
  })

  // Send a command to MineCraft
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
    sendQueue.push(msg)            // Add the message to the queue
  }
})
