import { BaseCommand } from '@adonisjs/core/ace'
import { rows } from '#services/store'
import BuildExport from '#jobs/build_export'

/** Re-enqueue pending outbox rows after a crash between INSERT and dispatch. */
export default class ReconcileExports extends BaseCommand {
  static commandName = 'exports:reconcile'
  static description = 'Re-enqueue unfinished article exports'
  static options = { startApp: true }
  async run() {
    const pending = await rows<{ id: number }>('select id from exports where status = ?', [
      'pending',
    ])
    for (const item of pending) await BuildExport.dispatch({ exportId: item.id })
    this.logger.info(`Re-enqueued ${pending.length} pending export(s)`)
  }
}
