import emitter from '@adonisjs/core/services/emitter'
import server from '@adonisjs/core/services/server'
import { WebSocketServer } from 'ws'
import { activeShare } from '#services/shares'
import { byId } from '#services/articles'
import { admit, ready } from '#services/live'

const sockets = new WebSocketServer({ noServer: true })
emitter.on('http:server_ready', () => {
  const node = server.getNodeServer()
  if (!node) return
  node.on('upgrade', (request, socket, head) => {
    const match = /^\/api\/shares\/([0-9a-f-]+)\/live$/.exec(request.url ?? '')
    if (!match) {
      socket.destroy()
      return
    }
    sockets.handleUpgrade(request, socket, head, (ws) => sockets.emit('connection', ws, match[1]))
  })
})
sockets.on('connection', (socket, id: string) => {
  const timer = setTimeout(() => socket.close(), 5000)
  let subscribed = false
  socket.once('message', async (data) => {
    if (subscribed) return
    subscribed = true
    clearTimeout(timer)
    try {
      const message: unknown = JSON.parse(data.toString())
      if (
        !message ||
        typeof message !== 'object' ||
        !('type' in message) ||
        message.type !== 'subscribe' ||
        !('key' in message) ||
        typeof message.key !== 'string'
      )
        throw Error('invalid')
      const link = await activeShare(id, message.key)
      if (socket.readyState !== socket.OPEN) return
      const member = admit(id, link.article_id, socket)
      if (!member) {
        socket.send(JSON.stringify({ type: 'room_full', limit: 100 }))
        socket.close()
        return
      }
      const article = await byId(link.article_id, { kind: 'anonymous' })
      await activeShare(id, message.key)
      if (!article || socket.readyState !== socket.OPEN) return
      ready(member, article)
    } catch {
      if (socket.readyState === socket.OPEN) {
        socket.send(JSON.stringify({ type: 'invalid_link' }))
        socket.close()
      }
    }
  })
  socket.once('close', () => clearTimeout(timer))
})
