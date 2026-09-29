import { BaseSchema } from '@adonisjs/lucid/schema'
export default class extends BaseSchema {
  async up() {
    await this.db.rawQuery('create index articles_tags_gin on articles using gin (tag_list)')
    await this.db.rawQuery(
      'create unique index shares_one_active on shares (article_id) where revoked_at is null'
    )
  }
  async down() {
    await this.db.rawQuery('drop index shares_one_active')
    await this.db.rawQuery('drop index articles_tags_gin')
  }
}
