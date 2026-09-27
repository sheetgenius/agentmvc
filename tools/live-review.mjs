// Supplemental independent checks, outside the frozen fixture given to backend agents.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {json, seed, LiveClient} from '../frontend/tests/helpers.js';

const require = createRequire(new URL('../frontend/package.json', import.meta.url));
const {chromium} = require('playwright');
const {WebSocket} = require('ws');
const [backend, frontend] = process.argv.slice(2);
if (!backend || !frontend) throw new Error('usage: node tools/live-review.mjs BACKEND_URL FRONTEND_ORIGIN');

const invalid = await seed(backend);
const browser = await chromium.launch();
try {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(`${frontend}/edit/${invalid.id}#key=wrong`);
  await page.getByRole('heading', {name: 'Link unavailable'}).waitFor({timeout: 5000});
  assert.equal((await page.locator('body').innerText()).includes('First version'), false);
  await context.close();
} finally {
  await browser.close();
}

const revoked = await seed(backend);
assert.equal((await json(backend, `/articles/${revoked.slug}/share`, {method: 'DELETE', token: revoked.token})).status, 204);
assert.equal((await json(backend, `/shares/${revoked.id}/article`, {
  method: 'PUT', key: revoked.key,
  body: {article: {title: 'Unauthorized', body: 'Unauthorized', revision: 1}},
})).status, 404);

const racing = await seed(backend);
let revision = 1;
for (let i = 0; i < 20; i++) {
  const client = await new LiveClient(backend, racing.id).open(racing.key);
  const saved = await json(backend, `/shares/${racing.id}/article`, {
    method: 'PUT', key: racing.key,
    body: {article: {title: `Racing ${i}`, body: `Version ${i}`, revision}},
  });
  assert.equal(saved.status, 200);
  revision = saved.data.article.revision;
  const ready = await client.next('ready');
  if (ready.article.revision < revision) {
    const updated = await client.next('updated', message => message.article.revision >= revision);
    assert.ok(updated.article.revision >= revision);
  }
  client.close();
}

const ownerEdit = await seed(backend);
const ownerClient = await new LiveClient(backend, ownerEdit.id).open(ownerEdit.key);
try {
  await ownerClient.next('ready');
  const saved = await json(backend, `/articles/${ownerEdit.slug}`, {
    method: 'PUT', token: ownerEdit.token, body: {article: {body: 'Saved by owner', revision: 1}},
  });
  assert.equal(saved.status, 200);
  assert.equal((await ownerClient.next('updated', message => message.article.revision === 2)).article.body, 'Saved by owner');
} finally {
  ownerClient.close();
}

const capacity = await seed(backend);
async function connect(key) {
  const socket = new WebSocket(`${backend.replace(/^http/, 'ws')}/api/shares/${capacity.id}/live`);
  const first = new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('socket admission timeout')), 10000);
    socket.once('error', reject);
    socket.once('message', bytes => { clearTimeout(timeout); resolve(JSON.parse(bytes.toString())); });
    socket.once('open', () => socket.send(JSON.stringify({type: 'subscribe', key})));
  });
  return {socket, message: await first};
}
const clients = [];
try {
  const admitted = await Promise.all(Array.from({length: 105}, () => connect(capacity.key)));
  clients.push(...admitted);
  assert.equal(admitted.filter(client => client.message.type === 'ready').length, 100);
  assert.equal(admitted.filter(client => client.message.type === 'room_full').length, 5);
  const bad = await connect('wrong');
  clients.push(bad);
  assert.equal(bad.message.type, 'invalid_link');
} finally {
  clients.forEach(client => client.socket.close());
}

console.log('PASS supplemental review: browser denial, revoked save, subscribe/save race, owner update, concurrent 100-slot admission');
