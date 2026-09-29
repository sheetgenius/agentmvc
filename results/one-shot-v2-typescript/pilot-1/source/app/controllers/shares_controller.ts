import type { HttpContext } from '@adonisjs/core/http'
import { current } from '../domain/auth.js'
import { articleBySlug, sharedArticle, updateArticle } from '../domain/articles.js'
import { payload } from '../domain/common.js'
import { publishUpdate } from '../domain/live.js'
import { removeShare, rotateShare, shareArticle } from '../domain/shares.js'

export default class SharesController {
  async create(ctx: HttpContext) {
    const viewer = (await current(ctx, true))!
    const article = await articleBySlug(ctx.params.slug, viewer)
    return ctx.response.status(201).send({ share: await rotateShare(article, viewer) })
  }
  async delete(ctx: HttpContext) {
    const viewer = (await current(ctx, true))!
    await removeShare(await articleBySlug(ctx.params.slug, viewer), viewer)
    return ctx.response.noContent()
  }
  async get(ctx: HttpContext) {
    return {
      article: sharedArticle(await shareArticle(ctx.params.id, ctx.request.header('x-share-key'))),
    }
  }
  async update(ctx: HttpContext) {
    const article = await shareArticle(ctx.params.id, ctx.request.header('x-share-key'))
    const updated = await updateArticle(article, null, payload(ctx, 'article'), 'share')
    publishUpdate(updated)
    return { article: sharedArticle(updated) }
  }
}
