import type { HttpContext } from '@adonisjs/core/http'
import type { NextFn } from '@adonisjs/core/types/http'

export default class ProtocolHeadersMiddleware {
  async handle(ctx: HttpContext, next: NextFn) {
    ctx.response.header('Access-Control-Allow-Origin', '*')
    ctx.response.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Share-Key')
    ctx.response.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    ctx.response.header('X-Content-Type-Options', 'nosniff')
    if (ctx.request.method() === 'OPTIONS') return ctx.response.status(204).send(null)
    return next()
  }
}
