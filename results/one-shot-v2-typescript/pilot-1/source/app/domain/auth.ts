import db from '@adonisjs/lucid/services/db'
import hash from '@adonisjs/core/services/hash'
import { SignJWT, jwtVerify } from 'jose'
import { fail, requiredText } from './common.js'
import type { HttpContext } from '@adonisjs/core/http'

const secret = new TextEncoder().encode(process.env.SECRET_KEY_BASE)
export interface User {
  id: number
  username: string
  email: string
  password_hash: string
  bio: string | null
  image: string | null
}
const selectUser = () => db.from('users')
export async function token(user: User) {
  return new SignJWT({})
    .setProtectedHeader({ alg: 'HS256' })
    .setSubject(String(user.id))
    .setIssuedAt()
    .setExpirationTime('30d')
    .sign(secret)
}
export async function current(ctx: HttpContext, required = false): Promise<User | null> {
  const header = ctx.request.header('authorization')
  if (!header) {
    if (required) fail(401, 'token', 'is missing')
    return null
  }
  const match = /^Token (\S+)$/.exec(header)
  if (!match) fail(401, 'token', 'is invalid')
  try {
    const { payload } = await jwtVerify(match![1], secret, { algorithms: ['HS256'] })
    if (!/^\d+$/.test(payload.sub || '')) throw Error('subject')
    const user = await selectUser().where('id', Number(payload.sub)).first()
    if (!user) throw Error('user')
    return user as User
  } catch {
    return fail(401, 'token', 'is invalid')
  }
}
export async function publicUser(user: User) {
  return {
    email: user.email,
    token: await token(user),
    username: user.username,
    bio: user.bio,
    image: user.image,
  }
}
function emailPassword(data: Record<string, unknown>) {
  return { email: requiredText(data, 'email'), password: requiredText(data, 'password') }
}
export async function register(data: Record<string, unknown>) {
  const input = { username: requiredText(data, 'username'), ...emailPassword(data) }
  if (input.password.length < 8) fail(422, 'password', 'is invalid')
  const existing = await selectUser()
    .where('username', input.username)
    .orWhere('email', input.email)
    .first()
  if (existing)
    fail(409, existing.username === input.username ? 'username' : 'email', 'has already been taken')
  try {
    const [user] = await db
      .table('users')
      .insert({
        username: input.username,
        email: input.email,
        password_hash: await hash.make(input.password),
      })
      .returning('*')
    return user as User
  } catch (error) {
    if (isUnique(error)) fail(409, uniqueField(error), 'has already been taken')
    throw error
  }
}
function isUnique(error: unknown) {
  return objectError(error)?.code === '23505'
}
function objectError(error: unknown): { code?: string; constraint?: string } | null {
  return error && typeof error === 'object'
    ? (error as { code?: string; constraint?: string })
    : null
}
function uniqueField(error: unknown) {
  return objectError(error)?.constraint?.includes('username') ? 'username' : 'email'
}
export async function login(data: Record<string, unknown>) {
  const input = emailPassword(data)
  const user = (await selectUser().where('email', input.email).first()) as User | undefined
  if (!user || !(await hash.verify(user.password_hash, input.password)))
    fail(401, 'credentials', 'invalid')
  return user
}
export async function updateUser(user: User, data: Record<string, unknown>) {
  const changes: Record<string, unknown> = {}
  for (const field of ['username', 'email'] as const)
    if (field in data) changes[field] = requiredText(data, field)
  for (const field of ['bio', 'image'] as const)
    if (field in data) {
      if (data[field] !== null && typeof data[field] !== 'string') fail(422, field, 'is invalid')
      changes[field] = data[field] || null
    }
  if ('password' in data) {
    const password = requiredText(data, 'password')
    if (password.length < 8) fail(422, 'password', 'is invalid')
    changes.password_hash = await hash.make(password)
  }
  if (!Object.keys(changes).length) return user
  try {
    const [updated] = await db.from('users').where('id', user.id).update(changes).returning('*')
    return updated as User
  } catch (error) {
    if (isUnique(error)) fail(409, uniqueField(error), 'has already been taken')
    throw error
  }
}
export async function profile(target: User, viewer: User | null) {
  const following = viewer
    ? !!(await db.from('follows').where({ follower_id: viewer.id, followed_id: target.id }).first())
    : false
  return { username: target.username, bio: target.bio, image: target.image, following }
}
export async function findProfile(username: string) {
  const user = await selectUser().where('username', username).first()
  if (!user) fail(404, 'profile', 'not found')
  return user as User
}
