import {WebSocket} from 'ws';

export async function json(base, path, {method = 'GET', token, key, body} = {}) {
  const response = await fetch(`${base}/api${path}`, {
    method,
    headers: {
      Accept: 'application/json',
      ...(token && {Authorization: `Token ${token}`}),
      ...(key && {'X-Share-Key': key}),
      ...(body && {'Content-Type': 'application/json'}),
    },
    ...(body && {body: JSON.stringify(body)}),
  });
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  return {status: response.status, data};
}

export async function seed(base) {
  const suffix = `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  const registration = await json(base, '/users', {
    method: 'POST', body: {user: {username: `live_${suffix}`, email: `live_${suffix}@test.com`, password: 'password123'}},
  });
  if (registration.status !== 201) throw new Error(`Registration failed: ${JSON.stringify(registration)}`);
  const token = registration.data.user.token;
  const created = await json(base, '/articles', {
    method: 'POST', token,
    body: {article: {title: `Live ${suffix}`, description: 'Shared draft', body: 'First version', status: 'draft'}},
  });
  if (created.status !== 201) throw new Error(`Article creation failed: ${JSON.stringify(created)}`);
  const slug = created.data.article.slug;
  const shared = await json(base, `/articles/${slug}/share`, {method: 'POST', token});
  if (shared.status !== 201) throw new Error(`Share creation failed: ${JSON.stringify(shared)}`);
  return {token, slug, ...shared.data.share};
}

export class LiveClient {
  constructor(base, id, key) {
    this.messages = [];
    this.waiters = [];
    this.socket = new WebSocket(`${base.replace(/^http/, 'ws')}/api/shares/${id}/live`);
    this.socket.on('message', bytes => {
      const message = JSON.parse(bytes.toString());
      const index = this.waiters.findIndex(waiter => waiter.test(message));
      if (index < 0) this.messages.push(message);
      else this.waiters.splice(index, 1)[0].resolve(message);
    });
  }

  async open(key) {
    await new Promise((resolve, reject) => {
      this.socket.once('open', resolve);
      this.socket.once('error', reject);
    });
    this.socket.send(JSON.stringify({type: 'subscribe', key}));
    return this;
  }

  next(type, condition = () => true, timeout = 10000) {
    const test = message => message.type === type && condition(message);
    const index = this.messages.findIndex(test);
    if (index >= 0) return Promise.resolve(this.messages.splice(index, 1)[0]);
    return new Promise((resolve, reject) => {
      const waiter = {test, resolve: message => { clearTimeout(timer); resolve(message); }};
      const timer = setTimeout(() => {
        this.waiters = this.waiters.filter(value => value !== waiter);
        reject(new Error(`Timed out waiting for ${type}; received ${JSON.stringify(this.messages)}`));
      }, timeout);
      this.waiters.push(waiter);
    });
  }

  close() { this.socket.close(); }
}
