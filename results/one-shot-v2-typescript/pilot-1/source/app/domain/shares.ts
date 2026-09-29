import db from '@adonisjs/lucid/services/db'
import { randomBytes, createHash, timingSafeEqual } from 'node:crypto'
import type { User } from './auth.js'
import { articleById, owned, type ArticleRow } from './articles.js'
import { fail } from './common.js'
import { revokeRoom } from './live.js'

const digest = (key: string) => createHash('sha256').update(key).digest('hex')
export async function shareArticle(id: string, key: unknown, viewer: User | null = null) {
  const share = await db.from('shares').where('id', id).first()
  const given = typeof key === 'string' ? Buffer.from(digest(key), 'hex') : Buffer.alloc(32)
  const expected = share ? Buffer.from(share.key_hash, 'hex') : Buffer.alloc(32)
  if (!share || !timingSafeEqual(given, expected)) fail(404, 'share', 'not found')
  return articleById(share.article_id, viewer)
}
export async function rotateShare(article: ArticleRow, viewer: User) {
  owned(article, viewer)
  const id = randomBytes(18).toString('base64url')
  const key = randomBytes(32).toString('base64url')
  const old = await db.from('shares').where('article_id', article.id).first()
  await db.transaction(async (trx) => {
    await trx.from('shares').where('article_id', article.id).delete()
    await trx.table('shares').insert({ id, article_id: article.id, key_hash: digest(key) })
  })
  if (old) revokeRoom(old.id)
  return { id, key }
}
export async function removeShare(article: ArticleRow, viewer: User) {
  owned(article, viewer)
  const old = await db.from('shares').where('article_id', article.id).first()
  await db.from('shares').where('article_id', article.id).delete()
  if (old) revokeRoom(old.id)
}
