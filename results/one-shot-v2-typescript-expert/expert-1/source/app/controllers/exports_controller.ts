import type { HttpContext } from '@adonisjs/core/http'
import { requireUser } from '#services/auth'
import { one } from '#services/store'
import { absent } from '#services/errors'
import BuildExport from '#jobs/build_export'

type ExportRow = {
  id: number
  status: string
  created_at: Date
  completed_at: Date | null
  articles: unknown
}
const representation = (row: ExportRow) => ({
  id: row.id,
  status: row.status,
  createdAt: row.created_at,
  completedAt: row.completed_at,
  articles: row.articles,
})
export default class ExportsController {
  async create(ctx: HttpContext) {
    const user = await requireUser(ctx)
    const created = await one<ExportRow>('insert into exports (user_id) values (?) returning *', [
      user.id,
    ])
    await BuildExport.dispatch({ exportId: created!.id })
    return ctx.response.status(202).send({ export: representation(created!) })
  }
  async show(ctx: HttpContext) {
    const user = await requireUser(ctx)
    const id = Number(ctx.params.id)
    if (!Number.isSafeInteger(id)) throw absent('export')
    const row = await one<ExportRow>('select * from exports where id = ? and user_id = ?', [
      id,
      user.id,
    ])
    if (!row) throw absent('export')
    return ctx.response.send({ export: representation(row) })
  }
}
