export async function request(path, {method = 'GET', key, token, body} = {}) {
  const response = await fetch(`/api${path}`, {
    method,
    headers: {
      Accept: 'application/json',
      ...(key && {'X-Share-Key': key}),
      ...(token && {Authorization: `Token ${token}`}),
      ...(body && {'Content-Type': 'application/json'}),
    },
    ...(body && {body: JSON.stringify(body)}),
  });
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) throw Object.assign(new Error(`Request failed (${response.status})`), {status: response.status, data});
  return data;
}
