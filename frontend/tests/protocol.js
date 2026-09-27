import assert from 'node:assert/strict';
import {json, seed, LiveClient} from './helpers.js';

const base = process.env.BACKEND_URL || `http://127.0.0.1:${process.argv[2] || 4101}`;
const share = await seed(base);
const clients = [];

try {
  const bad = await new LiveClient(base, share.id).open('wrong');
  assert.equal((await bad.next('invalid_link')).type, 'invalid_link');
  bad.close();

  const waiting = new LiveClient(base, share.id);
  await new Promise((resolve, reject) => {
    waiting.socket.once('open', resolve);
    waiting.socket.once('error', reject);
  });
  await new Promise(resolve => setTimeout(resolve, 100));
  assert.deepEqual(waiting.messages, [], 'socket disclosed data before authorization');
  waiting.socket.send(JSON.stringify({type: 'subscribe', key: share.key}));
  clients.push(waiting);
  assert.equal((await waiting.next('ready')).presence, 1);

  for (let count = 2; count <= 3; count++) {
    const client = await new LiveClient(base, share.id).open(share.key);
    clients.push(client);
    const ready = await client.next('ready');
    assert.equal(ready.presence, count);
    assert.equal(ready.article.revision, 1);
  }
  assert.equal((await clients[0].next('presence', message => message.count === 3)).count, 3);

  const saved = await json(base, `/shares/${share.id}/article`, {
    method: 'PUT', key: share.key,
    body: {article: {title: 'Live new title', body: 'Live new body', revision: 1}},
  });
  assert.equal(saved.status, 200);
  assert.equal(saved.data.article.revision, 2);
  await Promise.all(clients.map(client => client.next('updated', message => message.article.revision === 2)));

  const stale = await json(base, `/shares/${share.id}/article`, {
    method: 'PUT', key: share.key,
    body: {article: {title: 'stale', body: 'stale', revision: 1}},
  });
  assert.equal(stale.status, 409);
  assert.equal(stale.data.article.revision, 2);

  clients[2].close();
  assert.equal((await clients[0].next('presence', message => message.count === 2)).count, 2);
  const rejoined = await new LiveClient(base, share.id).open(share.key);
  clients.push(rejoined);
  assert.equal((await rejoined.next('ready')).article.revision, 2);

  const revoked = await json(base, `/articles/${saved.data.article.slug}/share`, {method: 'DELETE', token: share.token});
  assert.equal(revoked.status, 204);
  assert.equal((await clients[0].next('revoked')).type, 'revoked');
  assert.equal((await json(base, `/shares/${share.id}/article`, {key: share.key})).status, 404);
  console.log('PASS live protocol: authorization, presence, updates, conflict, reconnect, revocation');
} finally {
  clients.forEach(client => client.close());
}
