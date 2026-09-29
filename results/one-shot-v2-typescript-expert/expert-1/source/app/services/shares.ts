import { createHash, randomBytes, randomUUID, timingSafeEqual } from 'node:crypto'
import { one, rows } from './store.js'
import { absent } from './errors.js'
import type { ArticleRow } from './articles.js'
import { revokeRoom } from './live.js'
import db from '@adonisjs/lucid/services/db'

type ShareRow = { id: string; article_id: number; key_hash: string }
const digest = (key: string) => createHash('sha256').update(key).digest('hex')
export async function activeShare(id: string, key: string | undefined): Promise<ShareRow> {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id))
    throw absent('share')
  const row = await one<ShareRow>(
    'select id,article_id,key_hash from shares where id = ? and revoked_at is null',
    [id]
  )
  if (!row || !key) throw absent('share')
  const expected = Buffer.from(row.key_hash, 'hex')
  const actual = Buffer.from(digest(key), 'hex')
  if (expected.length !== actual.length || !timingSafeEqual(expected, actual)) throw absent('share')
  return row
}
export async function rotateShare(article: ArticleRow) {
  const id = randomUUID()
  const key = randomBytes(32).toString('base64url')
  const old = await db.transaction(async (trx) => {
    const links = await trx.rawQuery(
      'update shares set revoked_at = now() where article_id = ? and revoked_at is null returning id',
      [article.id]
    )
    await trx.rawQuery('insert into shares (id,article_id,key_hash) values (?,?,?)', [
      id,
      article.id,
      digest(key),
    ])
    return links.rows as { id: string }[]
  })
  for (const link of old) revokeRoom(link.id)
  return { id, key }
}
export async function revokeShare(article: ArticleRow) {
  const old = await rows<{ id: string }>(
    'update shares set revoked_at = now() where article_id = ? and revoked_at is null returning id',
    [article.id]
  )
  for (const link of old) revokeRoom(link.id)
}
