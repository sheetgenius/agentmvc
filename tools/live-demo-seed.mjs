const backend = process.argv[2];
const origin = process.env.DEMO_ORIGIN;
const suffix = `${Date.now()}${Math.random().toString(36).slice(2, 7)}`;

async function request(path, body, token) {
  const response = await fetch(`${backend}/api${path}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', ...(token && {Authorization: `Token ${token}`})},
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(`${path}: ${response.status} ${JSON.stringify(data)}`);
  return data;
}

const {user} = await request('/users', {user: {
  username: `demo_${suffix}`, email: `demo_${suffix}@example.test`, password: 'demo-password-123',
}});
const {article} = await request('/articles', {article: {
  title: `Shared demo ${suffix}`, description: 'Live editing demo', body: 'Open this link in another browser and start editing.', status: 'draft',
}}, user.token);
const {share} = await request(`/articles/${article.slug}/share`, {}, user.token);
console.log(`\n${origin}/edit/${share.id}#key=${share.key}\n`);
