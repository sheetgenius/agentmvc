import db from '@adonisjs/lucid/services/db'

/** Parameterized SQL boundary: result types are declared beside each query's caller. */
export async function rows<T>(sql: string, values: unknown[] = []): Promise<T[]> {
  const result = await db.rawQuery(sql, values)
  return result.rows as T[]
}
export async function one<T>(sql: string, values: unknown[] = []): Promise<T | undefined> {
  const found = await rows<T>(sql, values)
  return found[0]
}
