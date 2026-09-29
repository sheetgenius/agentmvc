import type { ArticleRow } from './articles.js'
import { sharedArticle } from './articles.js'
import { WebSocket } from 'ws'

type Member = {
  socket: WebSocket
  shareId: string
  ready: boolean
  lastRevision: number
  buffered?: ReturnType<typeof sharedArticle>
}
type Room = { members: Set<Member>; active: boolean }
const rooms = new Map<string, Room>()
export const ROOM_LIMIT = 100
function send(socket: WebSocket, event: object) {
  if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify(event))
}
function presence(room: Room) {
  for (const member of room.members)
    if (member.ready) send(member.socket, { type: 'presence', count: room.members.size })
}
export function admit(shareId: string, articleId: number, socket: WebSocket): Member | undefined {
  const room = rooms.get(shareId) ?? { members: new Set<Member>(), active: true }
  if (!room.active || room.members.size >= ROOM_LIMIT) return undefined
  rooms.set(shareId, room)
  roomArticle.set(shareId, articleId)
  const member: Member = { socket, shareId, ready: false, lastRevision: 0 }
  room.members.add(member)
  socket.once('close', () => remove(member))
  return member
}
export function ready(member: Member, article: ArticleRow) {
  const room = rooms.get(member.shareId)
  if (!room?.active || !room.members.has(member) || member.socket.readyState !== WebSocket.OPEN)
    return
  const snapshot = sharedArticle(article)
  member.ready = true
  member.lastRevision = snapshot.revision
  send(member.socket, { type: 'ready', article: snapshot, presence: room.members.size })
  if (member.buffered && member.buffered.revision > member.lastRevision) {
    member.lastRevision = member.buffered.revision
    send(member.socket, { type: 'updated', article: member.buffered })
  }
  presence(room)
}
function remove(member: Member) {
  const room = rooms.get(member.shareId)
  if (!room?.members.delete(member)) return
  if (room.members.size) presence(room)
  else {
    rooms.delete(member.shareId)
    roomArticle.delete(member.shareId)
  }
}
export function broadcastUpdate(articleId: number, article: ArticleRow) {
  const event = sharedArticle(article)
  for (const room of rooms.values())
    for (const member of room.members) {
      // A link remains attached to its article through slug changes.
      if (
        member.socket.readyState !== WebSocket.OPEN ||
        roomArticle.get(member.shareId) !== articleId
      )
        continue
      if (!member.ready) {
        if (!member.buffered || member.buffered.revision < event.revision) member.buffered = event
        continue
      }
      if (event.revision > member.lastRevision) {
        member.lastRevision = event.revision
        send(member.socket, { type: 'updated', article: event })
      }
    }
}
const roomArticle = new Map<string, number>()
export function revokeRoom(shareId: string) {
  const room = rooms.get(shareId)
  roomArticle.delete(shareId)
  if (!room) return
  room.active = false
  rooms.delete(shareId)
  for (const member of room.members) {
    send(member.socket, { type: 'revoked' })
    member.socket.close()
  }
}
