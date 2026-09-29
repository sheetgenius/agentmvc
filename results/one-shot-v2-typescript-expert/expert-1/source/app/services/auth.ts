import { SignJWT, jwtVerify } from 'jose'
import hash from '@adonisjs/core/services/hash'
import type { HttpContext } from '@adonisjs/core/http'
import { one } from './store.js'
import { missing } from './errors.js'

type UserRow = {
  id: number
  username: string
  email: string
  password_hash: string
  bio: string | null
  image: string | null
}
export type Viewer = { kind: 'anonymous' } | { kind: 'user'; user: UserRow }
const secret = new TextEncoder().encode(process.env.SECRET_KEY_BASE ?? '')
export async function token(user: UserRow): Promise<string> {
  return new SignJWT({ sub: String(user.id) })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('7d')
    .sign(secret)
}
export async function resolveViewer(header: string | undefined): Promise<Viewer> {
  if (!header) return { kind: 'anonymous' }
  if (!header.startsWith('Token ')) throw missing()
  try {
    const { payload } = await jwtVerify(header.slice(6), secret, { algorithms: ['HS256'] })
    const id = Number(payload.sub)
    if (!Number.isSafeInteger(id)) throw new Error('bad subject')
    const user = await one<UserRow>('select * from users where id = ?', [id])
    if (!user) throw new Error('missing user')
    return { kind: 'user', user }
  } catch {
    throw missing()
  }
}
export async function viewer(ctx: HttpContext): Promise<Viewer> {
  return resolveViewer(ctx.request.header('authorization'))
}
export async function requireUser(ctx: HttpContext): Promise<UserRow> {
  const caller = await viewer(ctx)
  if (caller.kind === 'anonymous') throw missing()
  return caller.user
}
export async function userResponse(user: UserRow) {
  return {
    user: {
      email: user.email,
      token: await token(user),
      username: user.username,
      bio: user.bio,
      image: user.image,
    },
  }
}
export const hashPassword = (value: string) => hash.make(value)
export const verifyPassword = (stored: string, value: string) => hash.verify(stored, value)
