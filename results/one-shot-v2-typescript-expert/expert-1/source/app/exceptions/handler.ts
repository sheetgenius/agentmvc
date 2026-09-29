import { ExceptionHandler } from '@adonisjs/core/http'
import type { HttpContext } from '@adonisjs/core/http'
import { ApiError } from '#services/errors'

export default class HttpExceptionHandler extends ExceptionHandler {
  protected debug = false
  async handle(error: unknown, ctx: HttpContext) {
    ctx.response.header('X-Content-Type-Options', 'nosniff')
    if (error instanceof ApiError) return ctx.response.status(error.status).send(error.body())
    if (error && typeof error === 'object' && 'code' in error && error.code === '23505') {
      const detail = 'detail' in error ? String(error.detail) : ''
      const field = detail.includes('username')
        ? 'username'
        : detail.includes('email')
          ? 'email'
          : 'article'
      return ctx.response.status(409).send({ errors: { [field]: ['has already been taken'] } })
    }
    if (
      error &&
      typeof error === 'object' &&
      'status' in error &&
      typeof error.status === 'number' &&
      error.status < 500
    ) {
      return ctx.response.status(error.status).send({ errors: { body: ['is invalid'] } })
    }
    return super.handle(error, ctx)
  }
}
