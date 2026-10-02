// Room cap check for the LiveRooms revert (not a frozen gate): 100 members join, the 101st gets
// room_full, presence reaches 100; after one leaves, a newcomer is admitted with presence 100.
import assert from 'node:assert/strict';
import {seed, LiveClient} from './helpers.js';
const base = process.env.BACKEND_URL;
const share = await seed(base);
const clients = [];
try {
  for (let i = 1; i <= 100; i++) {
    const c = await new LiveClient(base, share.id).open(share.key);
    clients.push(c);
    assert.equal((await c.next('ready')).presence, i);
  }
  await clients[0].next('presence', m => m.count === 100);
  const extra = await new LiveClient(base, share.id).open(share.key);
  const full = await extra.next('room_full');
  assert.equal(full.limit, 100);
  clients[50].close();
  await clients[0].next('presence', m => m.count === 99);
  const late = await new LiveClient(base, share.id).open(share.key);
  clients.push(late);
  assert.equal((await late.next('ready')).presence, 100);
  console.log('PASS live cap: 100 members, 101st room_full, leave/rejoin presence 100');
} finally {
  clients.forEach(c => c.close());
}
