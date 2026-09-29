import { test } from '@japa/runner'
import {
  checkRevision,
  owned,
  published,
  visibleTo,
  type ArticleRow,
} from '../../app/domain/articles.js'
import { RuleError } from '../../app/domain/common.js'
import type { User } from '../../app/domain/auth.js'

const author: User = {
  id: 1,
  username: 'author',
  email: 'a@test.com',
  password_hash: '',
  bio: null,
  image: null,
}
const stranger: User = { ...author, id: 2, username: 'stranger' }
const article: ArticleRow = {
  id: 10,
  slug: 'one',
  title: 'One',
  description: 'd',
  body: 'b',
  author_id: 1,
  status: 'draft',
  revision: 2,
  published_at: null,
  created_at: new Date(),
  updated_at: new Date(),
  username: 'author',
  bio: null,
  image: null,
  tag_list: [],
  favorites_count: 0,
  favorited: false,
  following: false,
}
function rejected(run: () => void): RuleError {
  try {
    run()
  } catch (error) {
    if (error instanceof RuleError) return error
    throw error
  }
  throw new Error('expected policy rejection')
}

test('draft visibility and ownership remain distinct across read and mutation', ({ assert }) => {
  assert.isTrue(visibleTo(article, author))
  assert.isFalse(visibleTo(article, stranger))
  assert.isFalse(visibleTo(article, null))
  assert.equal(rejected(() => owned({ ...article, status: 'published' }, stranger)).status, 403)
  assert.equal(rejected(() => published(article)).status, 422)
  assert.isTrue(visibleTo({ ...article, status: 'published' }, stranger))
})

test('revision checks reject wrong types and return the current wire view on conflict', ({
  assert,
}) => {
  checkRevision(article, undefined, 'author')
  checkRevision(article, 2, 'share')
  assert.equal(rejected(() => checkRevision(article, '2', 'author')).status, 422)
  assert.equal(rejected(() => checkRevision(article, undefined, 'share')).status, 422)
  const error = rejected(() => checkRevision(article, 1, 'share'))
  assert.equal(error.status, 409)
  assert.deepEqual(error.extra, { article: { slug: 'one', title: 'One', body: 'b', revision: 2 } })
})
