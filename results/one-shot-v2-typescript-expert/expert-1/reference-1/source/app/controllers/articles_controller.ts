import type { HttpContext } from '@adonisjs/core/http'
import { one, rows } from '#services/store'
import { object, text, tags, revision } from '#services/inputs'
import { viewer, requireUser } from '#services/auth'
import { bySlug, byId, owned, article, listArticles, slugFor, commitEdit } from '#services/articles'
import { assertPublicInteraction } from '#services/article_policy'
import { absent, forbidden, invalid, ApiError } from '#services/errors'
import { broadcastUpdate, revokeRoom } from '#services/live'

type CommentRow = {
  id: number
  body: string
  created_at: Date
  updated_at: Date
  author_id: number
  username: string
  bio: string | null
  image: string | null
  following: boolean
}
function comment(row: CommentRow) {
  return {
    id: row.id,
    body: row.body,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
    author: { username: row.username, bio: row.bio, image: row.image, following: row.following },
  }
}
const commentProjection = `c.*, u.username, u.bio, u.image, exists(select 1 from follows f where f.followed_id = c.author_id and f.follower_id = ?) as following`
export default class ArticlesController {
  async list(ctx: HttpContext) {
    return ctx.response.send(await listArticles(await viewer(ctx), ctx.request.qs(), 'public'))
  }
  async feed(ctx: HttpContext) {
    const user = await requireUser(ctx)
    return ctx.response.send(await listArticles({ kind: 'user', user }, ctx.request.qs(), 'feed'))
  }
  async drafts(ctx: HttpContext) {
    const user = await requireUser(ctx)
    return ctx.response.send(await listArticles({ kind: 'user', user }, ctx.request.qs(), 'drafts'))
  }
  async show(ctx: HttpContext) {
    const caller = await viewer(ctx)
    return ctx.response.send({ article: article(await bySlug(ctx.params.slug, caller)) })
  }
  async create(ctx: HttpContext) {
    const user = await requireUser(ctx)
    const input = object(ctx.request.body(), 'article')
    const title = text('title', input.title)!
    const description = text('description', input.description)!
    const body = text('body', input.body)!
    const tagList = tags(input.tagList) ?? []
    const status = input.status ?? 'published'
    if (status !== 'published' && status !== 'draft') throw invalid('status')
    const created = await one<{ id: number }>(
      `insert into articles (author_id,slug,title,description,body,tag_list,status,published_at)
      values (?,?,?,?,?,?,?,case when ? = 'published' then now() else null end) returning id`,
      [user.id, slugFor(title), title, description, body, tagList, status, status]
    )
    const row = await byId(created!.id, { kind: 'user', user })
    return ctx.response.status(201).send({ article: article(row!) })
  }
  async update(ctx: HttpContext) {
    const user = await requireUser(ctx)
    const caller = { kind: 'user', user } as const
    const current = await owned(ctx.params.slug, caller)
    const input = object(ctx.request.body(), 'article')
    const expected = revision(input.revision)
    if (expected !== undefined && expected !== current.revision)
      throw new ApiError(409, 'revision', 'is stale', article(current))
    const edit = {
      title: text('title', input.title, false),
      description: text('description', input.description, false),
      body: text('body', input.body, false),
      tagList: tags(input.tagList),
    }
    const updated = await commitEdit(current, edit, expected, caller)
    broadcastUpdate(current.id, updated)
    return ctx.response.send({ article: article(updated) })
  }
  async destroy(ctx: HttpContext) {
    const user = await requireUser(ctx)
    const current = await owned(ctx.params.slug, { kind: 'user', user })
    const links = await rows<{ id: string }>(
      'delete from shares where article_id = ? returning id',
      [current.id]
    )
    for (const link of links) revokeRoom(link.id)
    await rows('delete from articles where id = ?', [current.id])
    return ctx.response.status(204).send(null)
  }
  async publish(ctx: HttpContext) {
    const user = await requireUser(ctx)
    const caller = { kind: 'user', user } as const
    const current = await owned(ctx.params.slug, caller)
    if (current.status === 'draft') {
      await rows(
        "update articles set status = 'published', published_at = now(), revision = revision + 1, updated_at = now() where id = ? and status = 'draft'",
        [current.id]
      )
      const updated = (await byId(current.id, caller))!
      broadcastUpdate(current.id, updated)
      return ctx.response.send({ article: article(updated) })
    }
    return ctx.response.send({ article: article(current) })
  }
  async tags(ctx: HttpContext) {
    const found = await rows<{ tag: string }>(
      `select distinct unnest(tag_list) as tag from articles where status = 'published' order by tag`
    )
    return ctx.response.send({ tags: found.map((row) => row.tag) })
  }
  async favorite(ctx: HttpContext) {
    return this.changeFavorite(ctx, true)
  }
  async unfavorite(ctx: HttpContext) {
    return this.changeFavorite(ctx, false)
  }
  private async changeFavorite(ctx: HttpContext, add: boolean) {
    const user = await requireUser(ctx)
    const caller = { kind: 'user', user } as const
    const current = await bySlug(ctx.params.slug, caller)
    assertPublicInteraction(current)
    if (add)
      await rows('insert into favorites (user_id,article_id) values (?,?) on conflict do nothing', [
        user.id,
        current.id,
      ])
    else
      await rows('delete from favorites where user_id = ? and article_id = ?', [
        user.id,
        current.id,
      ])
    return ctx.response.send({ article: article((await byId(current.id, caller))!) })
  }
  async comments(ctx: HttpContext) {
    const caller = await viewer(ctx)
    const current = await bySlug(ctx.params.slug, caller)
    const id = caller.kind === 'user' ? caller.user.id : -1
    const found = await rows<CommentRow>(
      `select ${commentProjection} from comments c join users u on u.id = c.author_id where c.article_id = ? order by c.created_at, c.id`,
      [id, current.id]
    )
    return ctx.response.send({ comments: found.map(comment) })
  }
  async addComment(ctx: HttpContext) {
    const user = await requireUser(ctx)
    const caller = { kind: 'user', user } as const
    const current = await bySlug(ctx.params.slug, caller)
    assertPublicInteraction(current)
    const input = object(ctx.request.body(), 'comment')
    const body = text('body', input.body)!
    const created = await one<{ id: number }>(
      'insert into comments (article_id,author_id,body) values (?,?,?) returning id',
      [current.id, user.id, body]
    )
    const found = await one<CommentRow>(
      `select ${commentProjection} from comments c join users u on u.id = c.author_id where c.id = ?`,
      [user.id, created!.id]
    )
    return ctx.response.status(201).send({ comment: comment(found!) })
  }
  async deleteComment(ctx: HttpContext) {
    const user = await requireUser(ctx)
    const current = await bySlug(ctx.params.slug, { kind: 'user', user })
    const id = Number(ctx.params.id)
    if (!Number.isSafeInteger(id)) throw absent('comment')
    const found = await one<{ author_id: number }>(
      'select author_id from comments where id = ? and article_id = ?',
      [id, current.id]
    )
    if (!found) throw absent('comment')
    if (found.author_id !== user.id) throw forbidden('comment')
    await rows('delete from comments where id = ?', [id])
    return ctx.response.status(204).send(null)
  }
}
