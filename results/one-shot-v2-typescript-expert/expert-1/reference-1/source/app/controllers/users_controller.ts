import type { HttpContext } from '@adonisjs/core/http'
import { one, rows } from '#services/store'
import { object, text, password, nullableText } from '#services/inputs'
import { requireUser, userResponse, hashPassword, verifyPassword, viewer } from '#services/auth'
import { absent, forbidden, ApiError } from '#services/errors'
import { pruneExpiredFailures, type FailureWindow } from '#services/login_limit'

type User = {
  id: number
  username: string
  email: string
  password_hash: string
  bio: string | null
  image: string | null
}
const failures = new Map<string, FailureWindow>()
setInterval(() => pruneExpiredFailures(failures, Date.now()), 60_000).unref()
const loginTurns = new Map<string, Promise<void>>()
async function inLoginTurn<T>(key: string, action: () => Promise<T>): Promise<T> {
  const previous = loginTurns.get(key)
  let release!: () => void
  const turn = new Promise<void>((resolve) => (release = resolve))
  loginTurns.set(key, turn)
  if (previous) await previous
  try {
    return await action()
  } finally {
    if (loginTurns.get(key) === turn) loginTurns.delete(key)
    release()
  }
}
export default class UsersController {
  async register({ request, response }: HttpContext) {
    const input = object(request.body(), 'user')
    const username = text('username', input.username)!
    const email = text('email', input.email)!
    const secret = password(input.password)!
    const user = await one<User>(
      'insert into users (username,email,password_hash) values (?,?,?) returning *',
      [username, email, await hashPassword(secret)]
    )
    return response.status(201).send(await userResponse(user!))
  }
  async login({ request, response }: HttpContext) {
    const input = object(request.body(), 'user')
    const email = text('email', input.email)!
    const secret = text('password', input.password)!
    const key = email.toLowerCase()
    return inLoginTurn(key, async () => {
      const recent = failures.get(key)
      if (recent && recent.count >= 20 && recent.until > Date.now())
        throw new ApiError(429, 'credentials', 'rate limited')
      const user = await one<User>('select * from users where email = ?', [email])
      const valid = user && (await verifyPassword(user.password_hash, secret))
      if (!valid) {
        failures.set(key, {
          count: (recent?.until && recent.until > Date.now() ? recent.count : 0) + 1,
          until: Date.now() + 60_000,
        })
        throw new ApiError(401, 'credentials', 'invalid')
      }
      failures.delete(key)
      return response.send(await userResponse(user))
    })
  }
  async current(ctx: HttpContext) {
    return ctx.response.send(await userResponse(await requireUser(ctx)))
  }
  async update(ctx: HttpContext) {
    const current = await requireUser(ctx)
    const input = object(ctx.request.body(), 'user')
    const username = text('username', input.username, false)
    const email = text('email', input.email, false)
    const secret = password(input.password, false)
    const bio = nullableText('bio', input.bio)
    const image = nullableText('image', input.image)
    const user = await one<User>(
      `update users set username = coalesce(?,username), email = coalesce(?,email),
      password_hash = coalesce(?,password_hash), bio = case when ? then ? else bio end,
      image = case when ? then ? else image end where id = ? returning *`,
      [
        username ?? null,
        email ?? null,
        secret ? await hashPassword(secret) : null,
        bio !== undefined,
        bio ?? null,
        image !== undefined,
        image ?? null,
        current.id,
      ]
    )
    return ctx.response.send(await userResponse(user!))
  }
  async profile(ctx: HttpContext) {
    const caller = await viewer(ctx)
    const user = await one<User>('select * from users where username = ?', [ctx.params.username])
    if (!user) throw absent('profile')
    const following =
      caller.kind === 'user' &&
      !!(await one('select 1 from follows where follower_id = ? and followed_id = ?', [
        caller.user.id,
        user.id,
      ]))
    return ctx.response.send({
      profile: { username: user.username, bio: user.bio, image: user.image, following },
    })
  }
  async follow(ctx: HttpContext) {
    return this.changeFollow(ctx, true)
  }
  async unfollow(ctx: HttpContext) {
    return this.changeFollow(ctx, false)
  }
  private async changeFollow(ctx: HttpContext, add: boolean) {
    const caller = await requireUser(ctx)
    const user = await one<User>('select * from users where username = ?', [ctx.params.username])
    if (!user) throw absent('profile')
    if (caller.id === user.id && add) throw forbidden('profile')
    if (add)
      await rows(
        'insert into follows (follower_id, followed_id) values (?,?) on conflict do nothing',
        [caller.id, user.id]
      )
    else
      await rows('delete from follows where follower_id = ? and followed_id = ?', [
        caller.id,
        user.id,
      ])
    return ctx.response.send({
      profile: {
        username: user.username,
        bio: user.bio,
        image: user.image,
        following: add && caller.id !== user.id,
      },
    })
  }
}
