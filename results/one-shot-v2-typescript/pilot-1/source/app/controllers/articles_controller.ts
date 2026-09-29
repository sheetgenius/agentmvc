import db from '@adonisjs/lucid/services/db'
import type { HttpContext } from '@adonisjs/core/http'
import { current, profile, type User } from '../domain/auth.js'
import {
  articleBySlug,
  articleById,
  createArticle,
  formatArticle,
  listArticles,
  owned,
  published,
  publishArticle,
  updateArticle,
} from '../domain/articles.js'
import { fail, iso, page, payload, requiredText } from '../domain/common.js'
import { publishUpdate, revokeRoom } from '../domain/live.js'

async function commentView(row: Record<string, unknown>, viewer: User | null) {
  const user = (await db.from('users').where('id', Number(row.author_id)).first()) as User
  return {
    id: row.id,
    body: row.body,
    createdAt: iso(row.created_at as Date),
    updatedAt: iso(row.updated_at as Date),
    author: await profile(user, viewer),
  }
}
export default class ArticlesController {
  async list(ctx: HttpContext) {
    return listArticles(ctx, await current(ctx), 'public')
  }
  async feed(ctx: HttpContext) {
    return listArticles(ctx, (await current(ctx, true))!, 'feed')
  }
  async get(ctx: HttpContext) {
    const viewer = await current(ctx)
    return { article: formatArticle(await articleBySlug(ctx.params.slug, viewer)) }
  }
  async create(ctx: HttpContext) {
    const viewer = (await current(ctx, true))!
    return ctx.response
      .status(201)
      .send({ article: formatArticle(await createArticle(viewer, payload(ctx, 'article'))) })
  }
  async update(ctx: HttpContext) {
    const viewer = (await current(ctx, true))!
    const article = await articleBySlug(ctx.params.slug, viewer)
    const updated = await updateArticle(article, viewer, payload(ctx, 'article'), 'author')
    publishUpdate(updated)
    return { article: formatArticle(updated) }
  }
  async delete(ctx: HttpContext) {
    const viewer = (await current(ctx, true))!
    const article = await articleBySlug(ctx.params.slug, viewer)
    owned(article, viewer)
    const link = await db.from('shares').where('article_id', article.id).first()
    await db.from('articles').where('id', article.id).delete()
    if (link) revokeRoom(link.id)
    return ctx.response.noContent()
  }
  async publish(ctx: HttpContext) {
    const viewer = (await current(ctx, true))!
    const updated = await publishArticle(await articleBySlug(ctx.params.slug, viewer), viewer)
    publishUpdate(updated)
    return { article: formatArticle(updated) }
  }
  async tags() {
    const result = await db.rawQuery(
      `select distinct t.tag from article_tags t join articles a on a.id=t.article_id where a.status='published' order by t.tag`
    )
    return { tags: result.rows.map((r: { tag: string }) => r.tag) }
  }
  async favorite(ctx: HttpContext) {
    const viewer = (await current(ctx, true))!
    const article = await articleBySlug(ctx.params.slug, viewer)
    published(article)
    await db
      .table('favorites')
      .insert({ user_id: viewer.id, article_id: article.id })
      .onConflict()
      .ignore()
    return { article: formatArticle(await articleById(article.id, viewer)) }
  }
  async unfavorite(ctx: HttpContext) {
    const viewer = (await current(ctx, true))!
    const article = await articleBySlug(ctx.params.slug, viewer)
    published(article)
    await db.from('favorites').where({ user_id: viewer.id, article_id: article.id }).delete()
    return { article: formatArticle(await articleById(article.id, viewer)) }
  }
  async comments(ctx: HttpContext) {
    const viewer = await current(ctx)
    const article = await articleBySlug(ctx.params.slug, viewer)
    published(article)
    const { limit, offset } = page(ctx, 100)
    const result = await db.rawQuery(
      `select c.*, u.username, u.bio, u.image,
      exists(select 1 from follows f where f.follower_id=? and f.followed_id=c.author_id) as following
      from comments c join users u on u.id=c.author_id where c.article_id=?
      order by c.created_at asc, c.id asc limit ? offset ?`,
      [viewer?.id || 0, article.id, limit, offset]
    )
    return {
      comments: result.rows.map(
        (row: {
          id: number
          body: string
          created_at: Date
          updated_at: Date
          username: string
          bio: string | null
          image: string | null
          following: boolean
        }) => ({
          id: row.id,
          body: row.body,
          createdAt: iso(row.created_at),
          updatedAt: iso(row.updated_at),
          author: {
            username: row.username,
            bio: row.bio,
            image: row.image,
            following: row.following,
          },
        })
      ),
    }
  }
  async comment(ctx: HttpContext) {
    const viewer = (await current(ctx, true))!
    const article = await articleBySlug(ctx.params.slug, viewer)
    published(article)
    const body = requiredText(payload(ctx, 'comment'), 'body')
    const [row] = await db
      .table('comments')
      .insert({ article_id: article.id, author_id: viewer.id, body })
      .returning('*')
    return ctx.response.status(201).send({ comment: await commentView(row, viewer) })
  }
  async deleteComment(ctx: HttpContext) {
    const viewer = (await current(ctx, true))!
    const article = await articleBySlug(ctx.params.slug, viewer)
    published(article)
    const id = Number(ctx.params.id)
    if (!Number.isSafeInteger(id)) fail(404, 'comment', 'not found')
    const comment = await db.from('comments').where({ id, article_id: article.id }).first()
    if (!comment) fail(404, 'comment', 'not found')
    if (comment.author_id !== viewer.id) fail(403, 'comment', 'forbidden')
    await db.from('comments').where('id', id).delete()
    return ctx.response.noContent()
  }
}
