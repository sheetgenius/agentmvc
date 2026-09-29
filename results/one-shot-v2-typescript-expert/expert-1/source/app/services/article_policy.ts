import type { Viewer } from './auth.js'
import { absent, forbidden, invalid } from './errors.js'

export type ArticleState = { id: number; author_id: number; status: 'draft' | 'published' }
export const publicArticles = "a.status = 'published'"
export function canRead(article: ArticleState, viewer: Viewer): boolean {
  return (
    article.status === 'published' ||
    (viewer.kind === 'user' && viewer.user.id === article.author_id)
  )
}
export function assertVisible(
  article: ArticleState | undefined,
  viewer: Viewer
): asserts article is ArticleState {
  if (!article || !canRead(article, viewer)) throw absent('article')
}
export function assertOwner(article: ArticleState, userId: number): void {
  if (article.author_id !== userId) throw forbidden('article')
}
export function assertPublicInteraction(article: ArticleState): void {
  if (article.status === 'draft') throw invalid('article', 'is a draft')
}
