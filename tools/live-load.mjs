// Direct JSON/WebSocket workload. No browser or Lit code participates in timings.
import {createRequire} from 'node:module';
import {performance} from 'node:perf_hooks';

const require = createRequire(new URL('../frontend/package.json', import.meta.url));
const {WebSocket} = require('ws');
const [base, countText, savesText] = process.argv.slice(2);
const count = Number(countText);
const saves = Number(savesText);
const rooms = Math.ceil(count / 100);
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const report = value => console.log(JSON.stringify(value));
const percentile = (items, fraction) => {
  if (!items.length) return null;
  const sorted = [...items].sort((a, b) => a - b);
  return Math.round(sorted[Math.ceil(fraction * sorted.length) - 1] * 100) / 100;
};
const summary = values => ({count: values.length, p50_ms: percentile(values, .5), p95_ms: percentile(values, .95), p99_ms: percentile(values, .99)});

async function api(path, body, token) {
  const started = performance.now();
  const response = await fetch(`${base}/api${path}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', ...(token && {Authorization: `Token ${token}`})},
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(`${path}: ${response.status} ${JSON.stringify(data)}`);
  return {data, ms: performance.now() - started};
}

async function save(share, revision, index) {
  const body = {article: {title: share.title, body: `Save ${index}`, revision}};
  const started = performance.now();
  const response = await fetch(`${base}/api/shares/${share.id}/article`, {
    method: 'PUT', headers: {'Content-Type': 'application/json', 'X-Share-Key': share.key},
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (response.status !== 200) throw new Error(`save: ${response.status} ${JSON.stringify(data)}`);
  return {revision: data.article.revision, started, ms: performance.now() - started,
          payload_bytes: Buffer.byteLength(JSON.stringify(body))};
}

const suffix = `${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
const user = (await api('/users', {user: {
  username: `bench_${suffix}`, email: `bench_${suffix}@example.test`, password: 'password123',
}})).data.user;
const shares = [];
for (let i = 0; i < rooms; i++) {
  const title = `Live benchmark ${suffix} ${i}`;
  const article = (await api('/articles', {article: {title, description: 'Benchmark', body: 'Initial', status: 'draft'}}, user.token)).data.article;
  const share = (await api(`/articles/${article.slug}/share`, {}, user.token)).data.share;
  shares.push({...share, title, revision: 1});
}

const sockets = [];
const events = new Map();
let duplicate_revisions = 0;
let regressed_revisions = 0;
async function connect(room) {
  const share = shares[room];
  const socket = new WebSocket(`${base.replace(/^http/, 'ws')}/api/shares/${share.id}/live`);
  const entry = {socket, room, last: 0};
  const ready = new Promise((resolve, reject) => {
    socket.once('error', reject);
    socket.on('message', bytes => {
      const message = JSON.parse(bytes.toString());
      if (message.type === 'room_full' || message.type === 'invalid_link') reject(new Error(message.type));
      if (message.type === 'ready') { entry.last = message.article.revision; resolve(); }
      if (message.type === 'updated') {
        const revision = message.article.revision;
        if (revision === entry.last) duplicate_revisions++;
        if (revision < entry.last) regressed_revisions++;
        entry.last = revision;
        events.set(`${room}:${revision}:${sockets.indexOf(entry)}`, performance.now());
      }
    });
    socket.once('open', () => socket.send(JSON.stringify({type: 'subscribe', key: share.key})));
  });
  sockets.push(entry);
  await ready;
}

try {
  for (let start = 0; start < count; start += 20) {
    await Promise.all(Array.from({length: Math.min(20, count - start)}, (_, offset) => connect(Math.floor((start + offset) / 100))));
  }
  await pause(1000);
  report({event: 'idle_ready', subscribers: count, articles: rooms});
  await pause(4000);
  report({event: 'active_start'});
  const saved = [];
  const started = performance.now();
  for (let i = 0; i < saves; i++) {
    await pause(Math.max(0, started + i * 200 - performance.now()));
    const room = i % rooms;
    const result = await save(shares[room], shares[room].revision, i);
    shares[room].revision = result.revision;
    saved.push({...result, room});
  }
  await pause(Math.max(0, started + saves * 200 - performance.now()));
  const completed = performance.now();
  await pause(2000);
  const delivery = [];
  const deliverySamples = [];
  const missingSamples = [];
  let missing = 0;
  for (const item of saved) {
    sockets.forEach((entry, index) => {
      if (entry.room !== item.room) return;
      const received = events.get(`${item.room}:${item.revision}:${index}`);
      if (received === undefined) {
        missing++;
        missingSamples.push({room: item.room, revision: item.revision, socket: index});
      }
      else {
        const ms = received - item.started;
        delivery.push(ms);
        deliverySamples.push({room: item.room, revision: item.revision, socket: index, ms: Math.round(ms * 100) / 100});
      }
    });
  }
  report({event: 'result', subscribers: count, articles: rooms, saves, target_saves_per_second: 5,
          actual_saves_per_second: Math.round(saves / ((completed - started) / 1000) * 100) / 100,
          payload_bytes: saved[0]?.payload_bytes || 0, save_latency: summary(saved.map(item => item.ms)),
          delivery_latency: summary(delivery), missing, duplicate_revisions, regressed_revisions,
          save_samples: saved.map(item => ({room: item.room, revision: item.revision,
            sent_at_ms: Math.round((item.started - started) * 100) / 100, ms: Math.round(item.ms * 100) / 100,
            payload_bytes: item.payload_bytes})),
          delivery_samples: deliverySamples, missing_samples: missingSamples});
} finally {
  sockets.forEach(entry => entry.socket.close());
}
