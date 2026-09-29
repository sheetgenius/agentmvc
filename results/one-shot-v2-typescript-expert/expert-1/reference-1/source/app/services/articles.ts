import { randomUUID } from 'node:crypto'
import db from '@adonisjs/lucid/services/db'
import { one, rows } from './store.js'
import type { Viewer } from './auth.js'
import { assertVisible, assertOwner, publicArticles, type ArticleState } from './article_policy.js'
import { absent, ApiError } from './errors.js'
import { page, type Fields } from './inputs.js'

export type ArticleRow = ArticleState & {
  slug: string
  title: string
  description: string
  body: string
  tag_list: string[]
  revision: number
  published_at: Date | null
  created_at: Date
  updated_at: Date
  username: string
  bio: string | null
  image: string | null
  favorites_count: number
  favorited: boolean
  following: boolean
}
const projection = `a.*, u.username, u.bio, u.image,
  (select count(*)::int from favorites f where f.article_id = a.id) as favorites_count,
  exists(select 1 from favorites f where f.article_id = a.id and f.user_id = ?) as favorited,
  exists(select 1 from follows f where f.followed_id = a.author_id and f.follower_id = ?) as following`
export const sharedArticle = (a: Pick<ArticleRow, 'slug' | 'title' | 'body' | 'revision'>) => ({
  slug: a.slug,
  title: a.title,
  body: a.body,
  revision: a.revision,
})
export function article(a: ArticleRow, includeBody = true) {
  return {
    slug: a.slug,
    title: a.title,
    description: a.description,
    ...(includeBody ? { body: a.body } : {}),
    tagList: a.tag_list,
    createdAt: a.created_at,
    updatedAt: a.updated_at,
    favorited: a.favorited,
    favoritesCount: a.favorites_count,
    author: { username: a.username, bio: a.bio, image: a.image, following: a.following },
    status: a.status,
    publishedAt: a.published_at,
    revision: a.revision,
  }
}
const callerId = (viewer: Viewer) => (viewer.kind === 'user' ? viewer.user.id : -1)
export async function byId(id: number, viewer: Viewer): Promise<ArticleRow | undefined> {
  return one<ArticleRow>(
    `select ${projection} from articles a join users u on u.id = a.author_id where a.id = ?`,
    [callerId(viewer), callerId(viewer), id]
  )
}
export async function bySlug(slug: string, viewer: Viewer): Promise<ArticleRow> {
  const row = await one<ArticleRow>(
    `select ${projection} from articles a join users u on u.id = a.author_id where a.slug = ?`,
    [callerId(viewer), callerId(viewer), slug]
  )
  assertVisible(row, viewer)
  return row
}
export async function owned(
  slug: string,
  viewer: Extract<Viewer, { kind: 'user' }>
): Promise<ArticleRow> {
  const row = await bySlug(slug, viewer)
  assertOwner(row, viewer.user.id)
  return row
}
export async function listArticles(
  viewer: Viewer,
  input: Fields,
  mode: 'public' | 'feed' | 'drafts'
) {
  const { limit, offset } = page(input)
  const clauses = [mode === 'drafts' ? "a.status = 'draft' and a.author_id = ?" : publicArticles]
  const binds: unknown[] = mode === 'drafts' ? [callerId(viewer)] : []
  if (mode === 'feed') {
    clauses.push(
      'exists(select 1 from follows f where f.followed_id = a.author_id and f.follower_id = ?)'
    )
    binds.push(callerId(viewer))
  }
  if (mode === 'public') {
    for (const [key, sql] of Object.entries({
      tag: 'a.tag_list @> array[?]::text[]',
      author: 'exists(select 1 from users x where x.id = a.author_id and x.username = ?)',
      favorited:
        'exists(select 1 from favorites f join users x on x.id = f.user_id where f.article_id = a.id and x.username = ?)',
    }))
      if (input[key] !== undefined) {
        clauses.push(sql)
        binds.push(String(input[key]))
      }
  }
  const where = clauses.join(' and ')
  const total = await one<{ count: number }>(
    `select count(*)::int as count from articles a where ${where}`,
    binds
  )
  const result = await rows<ArticleRow>(
    `with page as (select a.id from articles a where ${where} order by a.created_at desc, a.id desc limit ? offset ?)
    select ${projection} from page p join articles a on a.id = p.id join users u on u.id = a.author_id order by a.created_at desc, a.id desc`,
    [...binds, limit, offset, callerId(viewer), callerId(viewer)]
  )
  return { articles: result.map((row) => article(row, false)), articlesCount: total?.count ?? 0 }
}
export function slugFor(title: string): string {
  return `${
    title
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 180) || 'article'
  }-${randomUUID().slice(0, 8)}`
}
export type Edit = { title?: string; description?: string; body?: string; tagList?: string[] }
export async function commitEdit(
  current: ArticleRow,
  edit: Edit,
  expected: number | undefined,
  viewer: Viewer,
  shared = false,
  shareId?: string
) {
  const changes: string[] = []
  const binds: (string | number | string[])[] = []
  if (edit.title !== undefined) {
    changes.push('title = ?', 'slug = ?')
    binds.push(edit.title, slugFor(edit.title))
  }
  if (edit.description !== undefined) {
    changes.push('description = ?')
    binds.push(edit.description)
  }
  if (edit.body !== undefined) {
    changes.push('body = ?')
    binds.push(edit.body)
  }
  if (edit.tagList !== undefined) {
    changes.push('tag_list = ?::text[]')
    binds.push(edit.tagList)
  }
  changes.push('revision = revision + 1', 'updated_at = now()')
  const revisionCondition = expected === undefined ? '' : 'and revision = ?'
  const query = `update articles set ${changes.join(', ')} where id = ? ${revisionCondition} ${shareId ? 'and exists(select 1 from shares s where s.id = ? and s.article_id = articles.id and s.revoked_at is null)' : ''} returning id`
  binds.push(current.id)
  if (expected !== undefined) binds.push(expected)
  if (shareId) binds.push(shareId)
  const updated = shareId
    ? await db.transaction(async (trx) => {
        const locked = await trx.rawQuery('select id from articles where id = ? for update', [
          current.id,
        ])
        if (!locked.rows.length) throw absent('share')
        const active = await trx.rawQuery(
          'select 1 from shares where id = ? and article_id = ? and revoked_at is null',
          [shareId, current.id]
        )
        if (!active.rows.length) throw absent('share')
        const changed = await trx.rawQuery(query, binds)
        return changed.rows[0] as { id: number } | undefined
      })
    : await one<{ id: number }>(query, binds)
  if (!updated) {
    if (
      shareId &&
      !(await one('select 1 from shares where id = ? and revoked_at is null', [shareId]))
    )
      throw absent('share')
    const latest = await byId(current.id, viewer)
    if (!latest) throw absent('article')
    throw new ApiError(
      409,
      'revision',
      'is stale',
      shared ? sharedArticle(latest) : article(latest)
    )
  }
  return (await byId(current.id, viewer))!
}
