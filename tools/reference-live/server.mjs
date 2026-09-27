// Throwaway reference for validating the shared step-8 checks. Never copied to an agent workdir.
import http from 'node:http';
import crypto from 'node:crypto';
import ws from '../../frontend/node_modules/ws/index.js';
const {WebSocketServer} = ws;

const port = Number(process.env.PORT || 4199);
const users = new Map();
const articles = new Map();
const shares = new Map();
const rooms = new Map();
const random = () => crypto.randomBytes(24).toString('base64url');
const send = (res, status, data) => { res.writeHead(status, {'Content-Type': 'application/json'}); res.end(data == null ? '' : JSON.stringify(data)); };
const doc = article => ({slug: article.slug, title: article.title, body: article.body, revision: article.revision});
const slug = title => title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') + '-' + random().slice(0, 6);
const valid = (id, key) => { const share = shares.get(id); return share?.active && share.key === key ? share : null; };
const notify = (articleId, message) => {
  for (const ws of rooms.get(articleId) || []) if (ws.readyState === 1) ws.send(JSON.stringify(message));
};
const revoke = share => {
  if (!share) return;
  share.active = false;
  for (const ws of rooms.get(share.articleId) || []) {
    if (ws.shareId === share.id) { ws.send(JSON.stringify({type: 'revoked'})); ws.close(1008); }
  }
};

const server = http.createServer(async (req, res) => {
  const path = new URL(req.url, `http://localhost:${port}`).pathname;
  let body = {};
  if (req.method === 'POST' || req.method === 'PUT') {
    let text = '';
    for await (const chunk of req) text += chunk;
    if (text) try { body = JSON.parse(text); } catch { return send(res, 422, {errors: {body: ['is invalid']}}); }
  }
  if (req.method === 'GET' && path === '/api/tags') return send(res, 200, {tags: []});
  if (req.method === 'POST' && path === '/api/users') {
    const token = random(); users.set(token, body.user?.username);
    return send(res, 201, {user: {...body.user, token}});
  }
  const owner = users.get(req.headers.authorization?.replace(/^Token /, ''));
  if (req.method === 'POST' && path === '/api/articles') {
    const article = {id: random(), owner, title: body.article.title, body: body.article.body, revision: 1};
    article.slug = slug(article.title); articles.set(article.id, article);
    return send(res, 201, {article: {...doc(article), status: body.article.status || 'published'}});
  }
  const articleRoute = path.match(/^\/api\/articles\/([^/]+)$/);
  if (req.method === 'PUT' && articleRoute) {
    const article = [...articles.values()].find(a => a.slug === articleRoute[1] && a.owner === owner);
    if (!article) return send(res, 404, {errors: {article: ['not found']}});
    if (body.article?.revision !== article.revision) return send(res, 409, {errors: {revision: ['is stale']}});
    article.title = body.article.title ?? article.title;
    article.body = body.article.body ?? article.body;
    article.slug = slug(article.title); article.revision++;
    notify(article.id, {type: 'updated', article: doc(article)});
    return send(res, 200, {article: doc(article)});
  }
  const ownerRoute = path.match(/^\/api\/articles\/([^/]+)\/share$/);
  if (ownerRoute) {
    const article = [...articles.values()].find(a => a.slug === ownerRoute[1]);
    if (!article || article.owner !== owner) return send(res, 404, {errors: {article: ['not found']}});
    if (req.method === 'POST') {
      revoke([...shares.values()].find(s => s.articleId === article.id && s.active));
      const share = {id: random(), key: random(), articleId: article.id, active: true};
      shares.set(share.id, share); return send(res, 201, {share: {id: share.id, key: share.key}});
    }
    if (req.method === 'DELETE') { revoke([...shares.values()].find(s => s.articleId === article.id && s.active)); return send(res, 204); }
  }
  const shareRoute = path.match(/^\/api\/shares\/([^/]+)\/article$/);
  if (shareRoute && ['GET', 'PUT'].includes(req.method)) {
    const share = valid(shareRoute[1], req.headers['x-share-key']);
    if (!share) return send(res, 404, {errors: {share: ['not found']}});
    const article = articles.get(share.articleId);
    if (req.method === 'GET') return send(res, 200, {article: doc(article)});
    const fields = body.article;
    if (!fields || Object.keys(fields).sort().join(',') !== 'body,revision,title' ||
        typeof fields.title !== 'string' || typeof fields.body !== 'string' || !Number.isInteger(fields.revision))
      return send(res, 422, {errors: {article: ['is invalid']}});
    if (fields.revision !== article.revision) return send(res, 409, {errors: {revision: ['is stale']}, article: doc(article)});
    article.title = fields.title; article.body = fields.body; article.slug = slug(fields.title); article.revision++;
    notify(article.id, {type: 'updated', article: doc(article)});
    return send(res, 200, {article: doc(article)});
  }
  send(res, 404, {errors: {article: ['not found']}});
});

const wss = new WebSocketServer({noServer: true});
server.on('upgrade', (req, socket, head) => {
  const match = req.url.match(/^\/api\/shares\/([^/]+)\/live$/);
  if (!match) { socket.destroy(); return; }
  wss.handleUpgrade(req, socket, head, ws => {
    const id = match[1];
    const timer = setTimeout(() => ws.close(1008), 5000);
    ws.once('message', bytes => {
      clearTimeout(timer);
      let message;
      try { message = JSON.parse(bytes.toString()); } catch { message = {}; }
      const share = message.type === 'subscribe' && valid(id, message.key);
      if (!share) { ws.send(JSON.stringify({type: 'invalid_link'})); ws.close(1008); return; }
      const article = articles.get(share.articleId);
      if (!rooms.has(article.id)) rooms.set(article.id, new Set());
      const room = rooms.get(article.id);
      if (room.size >= 100) { ws.send(JSON.stringify({type: 'room_full', limit: 100})); ws.close(1013); return; }
      room.add(ws); ws.shareId = share.id;
      ws.send(JSON.stringify({type: 'ready', article: doc(article), presence: room.size}));
      notify(article.id, {type: 'presence', count: room.size});
      ws.on('close', () => { room.delete(ws); notify(article.id, {type: 'presence', count: room.size}); });
    });
  });
});

server.listen(port, '127.0.0.1', () => console.log(`reference live server on ${port}`));
