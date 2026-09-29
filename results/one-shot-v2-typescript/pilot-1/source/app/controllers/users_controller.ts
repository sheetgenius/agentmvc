import db from '@adonisjs/lucid/services/db'
import type { HttpContext } from '@adonisjs/core/http'
import {
  current,
  findProfile,
  login,
  profile,
  publicUser,
  register,
  updateUser,
} from '../domain/auth.js'
import { payload } from '../domain/common.js'
import { listArticles } from '../domain/articles.js'
import { createExport, formatExport, getExport } from '../domain/exports.js'

const attempts = new Map<string, { count: number; until: number }>()
export default class UsersController {
  async register({ request, response }: HttpContext) {
    const user = await register(payload({ request } as HttpContext, 'user'))
    return response.status(201).send({ user: await publicUser(user!) })
  }
  async login(ctx: HttpContext) {
    const email = String((ctx.request.body() as { user?: { email?: unknown } })?.user?.email || '')
    const key = `${ctx.request.ip()}:${email}`
    const previous = attempts.get(key)
    if (previous && previous.until > Date.now() && previous.count >= 20)
      return ctx.response.status(429).send({ errors: { credentials: ['rate limited'] } })
    try {
      const user = await login(payload(ctx, 'user'))
      attempts.delete(key)
      return { user: await publicUser(user!) }
    } catch (error) {
      if (previous && previous.until > Date.now()) previous.count++
      else attempts.set(key, { count: 1, until: Date.now() + 60000 })
      throw error
    }
  }
  async me(ctx: HttpContext) {
    return { user: await publicUser((await current(ctx, true))!) }
  }
  async update(ctx: HttpContext) {
    return {
      user: await publicUser(await updateUser((await current(ctx, true))!, payload(ctx, 'user'))),
    }
  }
  async getProfile(ctx: HttpContext) {
    const viewer = await current(ctx)
    return { profile: await profile(await findProfile(ctx.params.username), viewer) }
  }
  async follow(ctx: HttpContext) {
    const viewer = (await current(ctx, true))!
    const target = await findProfile(ctx.params.username)
    if (viewer.id !== target.id)
      await db
        .table('follows')
        .insert({ follower_id: viewer.id, followed_id: target.id })
        .onConflict()
        .ignore()
    return { profile: await profile(target, viewer) }
  }
  async unfollow(ctx: HttpContext) {
    const viewer = (await current(ctx, true))!
    const target = await findProfile(ctx.params.username)
    await db.from('follows').where({ follower_id: viewer.id, followed_id: target.id }).delete()
    return { profile: await profile(target, viewer) }
  }
  async drafts(ctx: HttpContext) {
    const viewer = (await current(ctx, true))!
    return listArticles(ctx, viewer, 'drafts')
  }
  async createExport(ctx: HttpContext) {
    const row = await createExport((await current(ctx, true))!)
    return ctx.response.status(202).send({ export: formatExport(row) })
  }
  async export(ctx: HttpContext) {
    return { export: formatExport(await getExport(ctx.params.id, (await current(ctx, true))!)) }
  }
}
