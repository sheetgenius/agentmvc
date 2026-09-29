import db from '@adonisjs/lucid/services/db'
import { Job } from '@adonisjs/queue'
import type { User } from './auth.js'
import { fail, iso } from './common.js'

export interface ExportRow {
  id: number
  user_id: number
  status: 'pending' | 'done'
  created_at: Date
  completed_at: Date | null
  articles: object[] | null
}
export function formatExport(row: ExportRow) {
  return {
    id: row.id,
    status: row.status,
    createdAt: iso(row.created_at),
    completedAt: iso(row.completed_at),
    articles: row.articles,
  }
}
export async function createExport(user: User) {
  const [row] = await db.table('exports').insert({ user_id: user.id }).returning('*')
  await BuildExport.dispatch({ exportId: row.id })
  return row as ExportRow
}
export async function getExport(id: string, user: User) {
  if (!/^\d+$/.test(id)) fail(404, 'export', 'not found')
  const row = await db
    .from('exports')
    .where({ id: Number(id), user_id: user.id })
    .first()
  if (!row) fail(404, 'export', 'not found')
  return row as ExportRow
}
export class BuildExport extends Job<{ exportId: number }> {
  async execute() {
    const entry = await db.from('exports').where('id', this.payload.exportId).first()
    if (!entry || entry.status === 'done') return
    const result = await db.rawQuery(
      `select a.slug, a.title, a.description, a.body, a.status,
      coalesce((select json_agg(t.tag order by t.position) from article_tags t where t.article_id=a.id), '[]'::json) as "tagList",
      (select count(*)::int from comments c where c.article_id=a.id) as "commentsCount"
      from articles a where a.author_id=? order by a.created_at asc, a.id asc`,
      [entry.user_id]
    )
    await db
      .from('exports')
      .where({ id: entry.id, status: 'pending' })
      .update({ status: 'done', articles: JSON.stringify(result.rows), completed_at: new Date() })
  }
}
