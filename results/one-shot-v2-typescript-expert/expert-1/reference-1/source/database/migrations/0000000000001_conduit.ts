import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  async up() {
    this.schema.createTable('users', (t) => {
      t.increments('id').primary()
      t.string('username', 100).notNullable().unique()
      t.string('email', 255).notNullable().unique()
      t.text('password_hash').notNullable()
      t.text('bio').nullable()
      t.text('image').nullable()
    })
    this.schema.createTable('follows', (t) => {
      t.integer('follower_id').notNullable().references('users.id').onDelete('CASCADE')
      t.integer('followed_id').notNullable().references('users.id').onDelete('CASCADE')
      t.primary(['follower_id', 'followed_id'])
      t.check('follower_id <> followed_id')
    })
    this.schema.createTable('articles', (t) => {
      t.increments('id').primary()
      t.integer('author_id').notNullable().references('users.id').onDelete('CASCADE')
      t.string('slug', 255).notNullable().unique()
      t.text('title').notNullable()
      t.text('description').notNullable()
      t.text('body').notNullable()
      t.specificType('tag_list', 'text[]').notNullable().defaultTo('{}')
      t.string('status', 16).notNullable().defaultTo('published')
      t.timestamp('published_at', { useTz: true }).nullable()
      t.integer('revision').notNullable().defaultTo(1)
      t.timestamps(true, true)
      t.check("status in ('draft','published')")
      t.check(
        "(status = 'draft' AND published_at IS NULL) OR (status = 'published' AND published_at IS NOT NULL)"
      )
      t.check('revision >= 1')
      t.index(['status', 'created_at', 'id'])
      t.index(['author_id', 'status', 'created_at'])
    })
    this.schema.createTable('favorites', (t) => {
      t.integer('user_id').notNullable().references('users.id').onDelete('CASCADE')
      t.integer('article_id').notNullable().references('articles.id').onDelete('CASCADE')
      t.primary(['user_id', 'article_id'])
      t.index(['article_id'])
    })
    this.schema.createTable('comments', (t) => {
      t.increments('id').primary()
      t.integer('article_id').notNullable().references('articles.id').onDelete('CASCADE')
      t.integer('author_id').notNullable().references('users.id').onDelete('CASCADE')
      t.text('body').notNullable()
      t.timestamps(true, true)
      t.index(['article_id', 'created_at'])
    })
    this.schema.createTable('shares', (t) => {
      t.uuid('id').primary()
      t.integer('article_id').notNullable().references('articles.id').onDelete('CASCADE')
      t.text('key_hash').notNullable()
      t.timestamp('revoked_at', { useTz: true }).nullable()
    })
    this.schema.createTable('exports', (t) => {
      t.increments('id').primary()
      t.integer('user_id').notNullable().references('users.id').onDelete('CASCADE')
      t.string('status', 16).notNullable().defaultTo('pending')
      t.jsonb('articles').nullable()
      t.timestamp('created_at', { useTz: true }).notNullable().defaultTo(this.now())
      t.timestamp('completed_at', { useTz: true }).nullable()
      t.check("status in ('pending','done')")
    })
  }
  async down() {
    for (const table of [
      'exports',
      'shares',
      'comments',
      'favorites',
      'articles',
      'follows',
      'users',
    ])
      this.schema.dropTable(table)
  }
}
