import env from '#start/env'
import { defineConfig } from '@adonisjs/lucid'

export default defineConfig({
  connection: 'pg',
  connections: {
    pg: {
      client: 'pg',
      connection: env.get('DATABASE_URL'),
      migrations: { naturalSort: true, paths: ['database/migrations'] },
    },
  },
})
