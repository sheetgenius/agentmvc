import { WebSocketServer, WebSocket } from 'ws'
import type { Server } from 'node:http'
import type { IncomingMessage } from 'node:http'
import { shareArticle } from './shares.js'
import { sharedArticle, type ArticleRow } from './articles.js'

interface Member {
  articleId: number
  socket: WebSocket
  ready: boolean
  revision: number
  pending?: ArticleRow
}
const rooms = new Map<string, Set<Member>>()
const attached = new WeakSet<Server>()
const send = (socket: WebSocket, event: object) => {
  if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify(event))
}
function presence(room: Set<Member>) {
  for (const member of room)
    if (member.ready) send(member.socket, { type: 'presence', count: room.size })
}
export function publishUpdate(article: ArticleRow) {
  for (const room of rooms.values())
    for (const member of room) {
      if (member.articleId !== article.id) continue
      if (member.ready && article.revision > member.revision) {
        member.revision = article.revision
        send(member.socket, { type: 'updated', article: sharedArticle(article) })
      } else if (!member.ready && (!member.pending || article.revision > member.pending.revision))
        member.pending = article
    }
}
export function revokeRoom(id: string) {
  const room = rooms.get(id)
  if (!room) return
  rooms.delete(id)
  for (const member of room) {
    send(member.socket, { type: 'revoked' })
    member.socket.close()
  }
}
export function attachLive(server: Server) {
  if (attached.has(server)) return
  attached.add(server)
  const wss = new WebSocketServer({ noServer: true })
  server.on('upgrade', (request: IncomingMessage, socket, head) => {
    const match = /^\/api\/shares\/([^/]+)\/live$/.exec(request.url?.split('?')[0] || '')
    if (!match) {
      socket.destroy()
      return
    }
    wss.handleUpgrade(request, socket, head, (ws) => {
      const id = match[1]
      let admitted: Member | undefined
      const timer = setTimeout(() => ws.close(), 5000)
      ws.once('message', async (bytes) => {
        clearTimeout(timer)
        let message: unknown
        try {
          message = JSON.parse(bytes.toString())
        } catch {
          message = null
        }
        const input =
          message && typeof message === 'object'
            ? (message as { type?: unknown; key?: unknown })
            : null
        if (input?.type !== 'subscribe') {
          send(ws, { type: 'invalid_link' })
          ws.close()
          return
        }
        try {
          const article = await shareArticle(id, input.key)
          let room = rooms.get(id)
          if (!room) {
            room = new Set()
            rooms.set(id, room)
          }
          if (room.size >= 100) {
            send(ws, { type: 'room_full', limit: 100 })
            ws.close()
            return
          }
          admitted = { articleId: article.id, socket: ws, ready: false, revision: article.revision }
          room.add(admitted)
          // Recheck after admission so a concurrent commit appears in ready or updated.
          const latest = await shareArticle(id, input.key)
          const snapshot =
            admitted.pending && admitted.pending.revision > latest.revision
              ? admitted.pending
              : latest
          admitted.revision = snapshot.revision
          admitted.ready = true
          send(ws, { type: 'ready', article: sharedArticle(snapshot), presence: room.size })
          if (admitted.pending && admitted.pending.revision > snapshot.revision) {
            admitted.revision = admitted.pending.revision
            send(ws, { type: 'updated', article: sharedArticle(admitted.pending) })
          }
          presence(room)
        } catch {
          send(ws, { type: 'invalid_link' })
          ws.close()
        }
      })
      ws.on('close', () => {
        clearTimeout(timer)
        if (!admitted) return
        const room = rooms.get(id)
        if (!room) return
        room.delete(admitted)
        if (room.size) presence(room)
        else rooms.delete(id)
      })
    })
  })
}
