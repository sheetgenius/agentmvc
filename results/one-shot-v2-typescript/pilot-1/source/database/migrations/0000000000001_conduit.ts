import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  async up() {
    this.schema.createTable('users', (t) => {
      t.increments('id').primary()
      t.string('username', 100).notNullable().unique()
      t.string('email', 320).notNullable().unique()
      t.text('password_hash').notNullable()
      t.text('bio').nullable()
      t.text('image').nullable()
      t.timestamps(true, true)
    })
    this.schema.createTable('follows', (t) => {
      t.integer('follower_id').notNullable().references('users.id').onDelete('CASCADE')
      t.integer('followed_id').notNullable().references('users.id').onDelete('CASCADE')
      t.primary(['follower_id', 'followed_id'])
    })
    this.schema.createTable('articles', (t) => {
      t.increments('id').primary()
      t.string('slug', 255).notNullable().unique()
      t.text('title').notNullable()
      t.text('description').notNullable()
      t.text('body').notNullable()
      t.integer('author_id').notNullable().references('users.id').onDelete('CASCADE')
      t.string('status', 20).notNullable().defaultTo('published')
      t.timestamp('published_at', { useTz: true }).nullable()
      t.integer('revision').notNullable().defaultTo(1)
      t.timestamps(true, true)
      t.check("status in ('draft', 'published')")
      t.check(
        "(status = 'draft' and published_at is null) or (status = 'published' and published_at is not null)"
      )
      t.check('revision > 0')
      t.index(['status', 'created_at'])
      t.index(['author_id', 'status', 'created_at'])
    })
    this.schema.createTable('article_tags', (t) => {
      t.integer('article_id').notNullable().references('articles.id').onDelete('CASCADE')
      t.string('tag', 255).notNullable()
      t.integer('position').notNullable()
      t.primary(['article_id', 'tag'])
      t.unique(['article_id', 'position'])
      t.index(['tag', 'article_id'])
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
      t.string('id', 80).primary()
      t.integer('article_id').notNullable().unique().references('articles.id').onDelete('CASCADE')
      t.string('key_hash', 64).notNullable()
      t.timestamps(true, true)
    })
    this.schema.createTable('exports', (t) => {
      t.increments('id').primary()
      t.integer('user_id').notNullable().references('users.id').onDelete('CASCADE')
      t.string('status', 20).notNullable().defaultTo('pending')
      t.jsonb('articles').nullable()
      t.timestamp('completed_at', { useTz: true }).nullable()
      t.timestamps(true, true)
      t.check("status in ('pending', 'done')")
      t.index(['user_id', 'id'])
    })
  }
  async down() {
    for (const table of [
      'exports',
      'shares',
      'comments',
      'favorites',
      'article_tags',
      'articles',
      'follows',
      'users',
    ])
      this.schema.dropTable(table)
  }
}
