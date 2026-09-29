import type { HttpContext } from '@adonisjs/core/http'
import type { NextFn } from '@adonisjs/core/types/http'
export default class HeadersMiddleware {
  async handle(ctx: HttpContext, next: NextFn) {
    ctx.response.header('X-Content-Type-Options', 'nosniff')
    ctx.response.header('Access-Control-Allow-Origin', '*')
    ctx.response.header('Access-Control-Allow-Headers', 'Authorization, Content-Type, X-Share-Key')
    ctx.response.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    if (ctx.request.method() === 'OPTIONS') return ctx.response.noContent()
    return next()
  }
}
