import { BaseSchema } from '@adonisjs/lucid/schema'
import { QueueSchemaService } from '@adonisjs/queue'

export default class extends BaseSchema {
  async up() {
    const queue = new QueueSchemaService(this.db.getWriteClient())
    await queue.createJobsTable()
    await queue.createSchedulesTable()
  }

  async down() {
    const queue = new QueueSchemaService(this.db.getWriteClient())
    await queue.dropSchedulesTable()
    await queue.dropJobsTable()
  }
}
