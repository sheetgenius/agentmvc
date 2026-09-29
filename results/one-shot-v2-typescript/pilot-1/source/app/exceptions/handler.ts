import { ExceptionHandler } from '@adonisjs/core/http'
import type { HttpContext } from '@adonisjs/core/http'
import { RuleError } from '../domain/common.js'
export default class HttpExceptionHandler extends ExceptionHandler {
  protected debug = false
  async handle(error: unknown, ctx: HttpContext) {
    if (error instanceof RuleError) return ctx.response.status(error.status).send(error.body())
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
