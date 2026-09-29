import { invalid } from './errors.js'

export type Fields = Record<string, unknown>
export function object(input: unknown, outer: string): Fields {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw invalid(outer)
  const nested = (input as Fields)[outer]
  if (!nested || typeof nested !== 'object' || Array.isArray(nested)) throw invalid(outer)
  return nested as Fields
}
export function text(field: string, value: unknown, required = true): string | undefined {
  if (value === undefined && !required) return undefined
  if (value === null || value === '') throw invalid(field, "can't be blank")
  if (typeof value !== 'string') throw invalid(field)
  if (!value.trim()) throw invalid(field, "can't be blank")
  return value
}
export function password(value: unknown, required = true): string | undefined {
  const result = text('password', value, required)
  if (result !== undefined && result.length < 8) throw invalid('password', 'is too short')
  return result
}
export function nullableText(field: string, value: unknown): string | null | undefined {
  if (value === undefined) return undefined
  if (value === null || value === '') return null
  if (typeof value !== 'string') throw invalid(field)
  return value
}
export function tags(value: unknown): string[] | undefined {
  if (value === undefined) return undefined
  if (!Array.isArray(value) || value.some((tag) => typeof tag !== 'string'))
    throw invalid('tagList')
  if (value.length > 100) throw invalid('tagList')
  return [...new Set(value)]
}
export function revision(value: unknown, required = false): number | undefined {
  if (value === undefined && !required) return undefined
  if (typeof value !== 'number' || !Number.isSafeInteger(value)) throw invalid('revision')
  return value
}
export function page(input: Fields) {
  const parse = (field: string, fallback: number) => {
    if (input[field] === undefined) return fallback
    const value = Number(input[field])
    if (!Number.isSafeInteger(value) || value < 0) throw invalid(field)
    return value
  }
  return { limit: Math.min(parse('limit', 20), 100), offset: parse('offset', 0) }
}
