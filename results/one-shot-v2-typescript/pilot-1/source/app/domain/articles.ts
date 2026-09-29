import db from '@adonisjs/lucid/services/db'
import { randomUUID } from 'node:crypto'
import type { User } from './auth.js'
import { fail, iso, requiredText, textField, RuleError } from './common.js'
import type { HttpContext } from '@adonisjs/core/http'

export interface ArticleRow {
  id: number
  slug: string
  title: string
  description: string
  body: string
  author_id: number
  status: 'draft' | 'published'
  revision: number
  published_at: Date | null
  created_at: Date
  updated_at: Date
  username: string
  bio: string | null
  image: string | null
  tag_list: string[]
  favorites_count: number
  favorited: boolean
  following: boolean
}
const slugFor = (title: string) =>
  `${
    title
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 180) || 'article'
  }-${randomUUID().slice(0, 8)}`
const projection = `a.*, u.username, u.bio, u.image,
  coalesce((select json_agg(t.tag order by t.position) from article_tags t where t.article_id=a.id), '[]'::json) as tag_list,
  (select count(*)::int from favorites f where f.article_id=a.id) as favorites_count,
  exists(select 1 from favorites f where f.article_id=a.id and f.user_id=?) as favorited,
  exists(select 1 from follows f where f.follower_id=? and f.followed_id=a.author_id) as following`
export async function articleById(id: number, viewer: User | null): Promise<ArticleRow> {
  const result = await db.rawQuery(
    `select ${projection} from articles a join users u on u.id=a.author_id where a.id=?`,
    [viewer?.id || 0, viewer?.id || 0, id]
  )
  if (!result.rows[0]) fail(404, 'article', 'not found')
  return result.rows[0] as ArticleRow
}
export async function articleBySlug(slug: string, viewer: User | null): Promise<ArticleRow> {
  const result = await db.rawQuery(
    `select ${projection} from articles a join users u on u.id=a.author_id where a.slug=?`,
    [viewer?.id || 0, viewer?.id || 0, slug]
  )
  const article = result.rows[0] as ArticleRow | undefined
  if (!article || !visibleTo(article, viewer)) return fail(404, 'article', 'not found')
  return article
}
export function visibleTo(article: Pick<ArticleRow, 'status' | 'author_id'>, viewer: User | null) {
  return article.status === 'published' || article.author_id === viewer?.id
}
export function owned(article: ArticleRow, viewer: User) {
  if (article.author_id !== viewer.id) fail(403, 'article', 'forbidden')
}
export function published(article: ArticleRow) {
  if (article.status === 'draft') fail(422, 'article', 'is a draft')
}
export function formatArticle(a: ArticleRow) {
  const value = {
    slug: a.slug,
    title: a.title,
    description: a.description,
    body: a.body,
    tagList: a.tag_list,
    createdAt: iso(a.created_at),
    updatedAt: iso(a.updated_at),
    favorited: a.favorited,
    favoritesCount: a.favorites_count,
    author: { username: a.username, bio: a.bio, image: a.image, following: a.following },
    status: a.status,
    publishedAt: iso(a.published_at),
    revision: a.revision,
  }
  return value
}
export function summaryArticle(a: ArticleRow) {
  const { body: ignoredBody, ...summary } = formatArticle(a)
  void ignoredBody
  return summary
}
export function sharedArticle(a: ArticleRow) {
  return { slug: a.slug, title: a.title, body: a.body, revision: a.revision }
}
export function validateTags(value: unknown): string[] {
  if (
    !Array.isArray(value) ||
    value.length > 100 ||
    value.some((x) => typeof x !== 'string' || !x.trim() || x.length > 255)
  )
    fail(422, 'tagList', 'is invalid')
  return [...new Set(value as string[])]
}
async function replaceTags(id: number, tags: string[], trx: Pick<typeof db, 'from' | 'table'>) {
  await trx.from('article_tags').where('article_id', id).delete()
  if (tags.length)
    await trx
      .table('article_tags')
      .insert(tags.map((tag, position) => ({ article_id: id, tag, position })))
}
export async function createArticle(viewer: User, data: Record<string, unknown>) {
  const title = requiredText(data, 'title')
  const description = requiredText(data, 'description')
  const body = requiredText(data, 'body')
  const status = data.status ?? 'published'
  if (status !== 'draft' && status !== 'published') fail(422, 'status', 'is invalid')
  const tags = data.tagList === undefined ? [] : validateTags(data.tagList)
  const id = await db.transaction(async (trx) => {
    const [row] = await trx
      .table('articles')
      .insert({
        slug: slugFor(title),
        title,
        description,
        body,
        author_id: viewer.id,
        status,
        published_at: status === 'published' ? new Date() : null,
      })
      .returning('id')
    await replaceTags(row.id, tags, trx)
    return row.id as number
  })
  return articleById(id, viewer)
}
export function checkRevision(current: ArticleRow, revision: unknown, mode: 'author' | 'share') {
  if (revision !== undefined && (typeof revision !== 'number' || !Number.isInteger(revision)))
    fail(422, 'revision', 'is invalid')
  if (mode === 'share' && revision === undefined) fail(422, 'revision', 'is invalid')
  if (revision !== undefined && revision !== current.revision)
    throw new RuleError(409, 'revision', 'is stale', {
      article: mode === 'share' ? sharedArticle(current) : formatArticle(current),
    })
}
export async function updateArticle(
  current: ArticleRow,
  viewer: User | null,
  data: Record<string, unknown>,
  mode: 'author' | 'share'
) {
  if (mode === 'author') {
    if (!viewer) fail(401, 'token', 'is missing')
    owned(current, viewer!)
  }
  checkRevision(current, data.revision, mode)
  if (
    mode === 'share' &&
    Object.keys(data).some((key) => !['title', 'body', 'revision'].includes(key))
  )
    fail(422, 'article', 'is invalid')
  const fields = mode === 'share' ? ['title', 'body'] : ['title', 'description', 'body']
  const changes: Record<string, unknown> = {
    revision:
      mode === 'author' && data.revision === undefined
        ? db.raw('revision + 1')
        : current.revision + 1,
    updated_at: new Date(),
  }
  for (const field of fields) {
    const value = mode === 'share' ? requiredText(data, field) : textField(data, field)
    if (value !== undefined) changes[field] = value
  }
  if (changes.title) changes.slug = slugFor(changes.title as string)
  const tags =
    mode === 'author' && data.tagList !== undefined ? validateTags(data.tagList) : undefined
  const updated = await db.transaction(async (trx) => {
    const query = trx.from('articles').where('id', current.id)
    if (data.revision !== undefined) query.where('revision', current.revision)
    const [row] = await query.update(changes).returning('id')
    if (!row) return false
    if (tags) await replaceTags(current.id, tags, trx)
    return true
  })
  const latest = await articleById(current.id, viewer)
  if (!updated)
    throw new RuleError(409, 'revision', 'is stale', {
      article: mode === 'share' ? sharedArticle(latest) : formatArticle(latest),
    })
  return latest
}
export async function publishArticle(a: ArticleRow, viewer: User) {
  owned(a, viewer)
  if (a.status === 'published') return articleById(a.id, viewer)
  await db
    .from('articles')
    .where({ id: a.id, status: 'draft' })
    .update({
      status: 'published',
      published_at: new Date(),
      revision: db.raw('revision + 1'),
      updated_at: new Date(),
    })
  return articleById(a.id, viewer)
}
export async function listArticles(
  ctx: HttpContext,
  viewer: User | null,
  kind: 'public' | 'feed' | 'drafts'
) {
  const { page } = await import('./common.js')
  const { limit, offset } = page(ctx)
  const where = [kind === 'drafts' ? `a.status='draft' and a.author_id=?` : `a.status='published'`]
  const args: unknown[] = kind === 'drafts' ? [viewer!.id] : []
  if (kind === 'feed') {
    where.push(
      'exists(select 1 from follows x where x.followed_id=a.author_id and x.follower_id=?)'
    )
    args.push(viewer!.id)
  }
  if (kind === 'public') {
    for (const [filter, clause] of [
      ['tag', 'exists(select 1 from article_tags x where x.article_id=a.id and x.tag=?)'],
      ['author', 'exists(select 1 from users x where x.id=a.author_id and x.username=?)'],
      [
        'favorited',
        'exists(select 1 from favorites f join users x on x.id=f.user_id where f.article_id=a.id and x.username=?)',
      ],
    ]) {
      const value = ctx.request.input(filter)
      if (value !== undefined) {
        where.push(clause)
        args.push(String(value))
      }
    }
  }
  const condition = where.join(' and ')
  const count = await db.rawQuery(
    `select count(*)::int as count from articles a where ${condition}`,
    args
  )
  const rows = await db.rawQuery(
    `select ${projection} from articles a join users u on u.id=a.author_id where ${condition} order by a.created_at desc, a.id desc limit ? offset ?`,
    [viewer?.id || 0, viewer?.id || 0, ...args, limit, offset]
  )
  return {
    articles: (rows.rows as ArticleRow[]).map(summaryArticle),
    articlesCount: count.rows[0].count as number,
  }
}
