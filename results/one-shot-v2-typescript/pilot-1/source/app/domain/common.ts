import type { HttpContext } from '@adonisjs/core/http'

export class RuleError extends Error {
  constructor(
    public status: number,
    public field: string,
    public reason: string,
    public extra?: object
  ) {
    super(reason)
  }
  body() {
    return { errors: { [this.field]: [this.reason] }, ...this.extra }
  }
}
export const fail = (status: number, field: string, reason: string): never => {
  throw new RuleError(status, field, reason)
}
export function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail(422, 'body', 'is invalid')
  return value as Record<string, unknown>
}
export function payload(ctx: HttpContext, wrapper: string) {
  return object(object(ctx.request.body())[wrapper])
}
export function textField(data: Record<string, unknown>, name: string): string | undefined {
  const value = data[name]
  if (value === undefined) return undefined
  if (value === null || value === '') return fail(422, name, "can't be blank")
  if (typeof value !== 'string') return fail(422, name, 'is invalid')
  if (!value.trim()) return fail(422, name, "can't be blank")
  return value
}
export function requiredText(data: Record<string, unknown>, name: string): string {
  return textField(data, name) ?? fail(422, name, "can't be blank")
}
export function page(ctx: HttpContext, defaultLimit = 20) {
  const parse = (name: string, fallback: number, max: number) => {
    const raw = ctx.request.input(name)
    if (raw === undefined) return fallback
    const n = Number(raw)
    if (!Number.isSafeInteger(n) || n < 0) fail(422, name, 'is invalid')
    return Math.min(n, max)
  }
  return { limit: parse('limit', defaultLimit, 100), offset: parse('offset', 0, 1000000) }
}
export const iso = (value: Date | string | null): string | null =>
  value ? new Date(value).toISOString() : null
