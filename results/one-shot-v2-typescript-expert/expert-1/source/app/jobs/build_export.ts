import { Job } from '@adonisjs/queue'
import type { JobOptions } from '@adonisjs/queue/types'
import { one, rows } from '#services/store'

export default class BuildExport extends Job<{ exportId: number }> {
  static options: JobOptions = { queue: 'default', maxRetries: 3 }
  async execute() {
    const pending = await one<{ id: number; user_id: number }>(
      'select id,user_id from exports where id = ? and status = ?',
      [this.payload.exportId, 'pending']
    )
    if (!pending) return
    const articles = await rows<{
      slug: string
      title: string
      description: string
      body: string
      tagList: string[]
      status: string
      commentsCount: number
    }>(
      `
      select a.slug,a.title,a.description,a.body,a.tag_list as "tagList",a.status,
      (select count(*)::int from comments c where c.article_id = a.id) as "commentsCount"
      from articles a where a.author_id = ? order by a.created_at,a.id`,
      [pending.user_id]
    )
    await rows(
      'update exports set status = ?, articles = ?::jsonb, completed_at = now() where id = ? and status = ?',
      ['done', JSON.stringify(articles), pending.id, 'pending']
    )
  }
}
