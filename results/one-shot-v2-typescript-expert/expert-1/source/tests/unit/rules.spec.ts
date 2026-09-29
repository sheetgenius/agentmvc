import { test } from '@japa/runner'
import { canRead, assertOwner, assertPublicInteraction } from '#services/article_policy'
import { password, revision } from '#services/inputs'
import { admit, revokeRoom } from '#services/live'
import type { Viewer } from '#services/auth'
import { EventEmitter } from 'node:events'
import type { WebSocket } from 'ws'

const author: Viewer = {
  kind: 'user',
  user: {
    id: 1,
    username: 'author',
    email: 'a@example.test',
    password_hash: '',
    bio: null,
    image: null,
  },
}
const stranger: Viewer = {
  kind: 'user',
  user: {
    id: 2,
    username: 'stranger',
    email: 'b@example.test',
    password_hash: '',
    bio: null,
    image: null,
  },
}

test.group('shared product rules', () => {
  test('draft visibility and public interaction remain separate', ({ assert }) => {
    const draft = { id: 1, author_id: 1, status: 'draft' as const }
    assert.isTrue(canRead(draft, author))
    assert.isFalse(canRead(draft, stranger))
    assert.isFalse(canRead(draft, { kind: 'anonymous' }))
    assert.throws(() => assertOwner(draft, 2))
    assert.throws(() => assertPublicInteraction(draft))
    assert.isTrue(canRead({ ...draft, status: 'published' }, stranger))
  })
  test('password and revision reject short or coerced inputs', ({ assert }) => {
    assert.throws(() => password('short7'))
    assert.equal(password('a'.repeat(64)), 'a'.repeat(64))
    assert.throws(() => revision('1'))
    assert.equal(revision(1), 1)
  })
  test('room admission is capped and closing a socket frees a slot', ({ assert }) => {
    class FakeSocket extends EventEmitter {
      readyState = 1
      send() {}
      close() {
        this.readyState = 3
        this.emit('close')
      }
    }
    const id = 'test-room-cap'
    const clients = Array.from({ length: 100 }, () => new FakeSocket())
    for (const client of clients) assert.isDefined(admit(id, 1, client as unknown as WebSocket))
    assert.isUndefined(admit(id, 1, new FakeSocket() as unknown as WebSocket))
    clients[0].close()
    assert.isDefined(admit(id, 1, new FakeSocket() as unknown as WebSocket))
    revokeRoom(id)
  })
})
