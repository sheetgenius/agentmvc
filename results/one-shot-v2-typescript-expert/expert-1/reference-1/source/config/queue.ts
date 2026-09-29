import { defineConfig, drivers } from '@adonisjs/queue'

export default defineConfig({
  default: 'database',
  adapters: { database: drivers.database({ connectionName: 'pg' }) },
  worker: { concurrency: 2, idleDelay: '1s' },
  locations: ['./app/jobs/**/*.{ts,js}'],
})
