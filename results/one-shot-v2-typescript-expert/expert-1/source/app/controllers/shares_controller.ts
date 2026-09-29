import type { HttpContext } from '@adonisjs/core/http'
import { requireUser } from '#services/auth'
import { owned, byId, sharedArticle, commitEdit } from '#services/articles'
import { object, text, revision } from '#services/inputs'
import { activeShare, rotateShare, revokeShare } from '#services/shares'
import { ApiError, invalid } from '#services/errors'
import { broadcastUpdate } from '#services/live'

export default class SharesController {
  async create(ctx: HttpContext) {
    const user = await requireUser(ctx)
    const current = await owned(ctx.params.slug, { kind: 'user', user })
    return ctx.response.status(201).send({ share: await rotateShare(current) })
  }
  async destroy(ctx: HttpContext) {
    const user = await requireUser(ctx)
    const current = await owned(ctx.params.slug, { kind: 'user', user })
    await revokeShare(current)
    return ctx.response.status(204).send(null)
  }
  async show(ctx: HttpContext) {
    const share = await activeShare(ctx.params.id, ctx.request.header('x-share-key'))
    const current = await byId(share.article_id, { kind: 'anonymous' })
    return ctx.response.send({ article: sharedArticle(current!) })
  }
  async update(ctx: HttpContext) {
    const share = await activeShare(ctx.params.id, ctx.request.header('x-share-key'))
    const current = (await byId(share.article_id, { kind: 'anonymous' }))!
    const input = object(ctx.request.body(), 'article')
    const expected = revision(input.revision, true)!
    if (expected !== current.revision)
      throw new ApiError(409, 'revision', 'is stale', sharedArticle(current))
    if (Object.keys(input).some((key) => !['title', 'body', 'revision'].includes(key)))
      throw invalid('article')
    const title = text('title', input.title)!
    const body = text('body', input.body)!
    const updated = await commitEdit(
      current,
      { title, body },
      expected,
      { kind: 'anonymous' },
      true,
      share.id
    )
    broadcastUpdate(current.id, updated)
    return ctx.response.send({ article: sharedArticle(updated) })
  }
}
