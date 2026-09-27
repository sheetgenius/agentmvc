// One k6 scenario per run, selected with -e SCENARIO=<name>; the same script and data for every stack.
// Constant load: VUS virtual users for DURATION. Each request picks inputs from the seeded data.
import http from "k6/http";
import { check } from "k6";

const seed = JSON.parse(open("/work/seed.json"));
const BASE = __ENV.BASE_URL;
const pick = (list) => list[Math.floor(Math.random() * list.length)];
// Every request is a normal JSON API client request.
const anonymous = { headers: { Accept: "application/json" } };
const auth = () => ({ headers: { Accept: "application/json", Authorization: `Token ${pick(seed.users).token}`, "Content-Type": "application/json" } });

export const options = {
  vus: Number(__ENV.VUS || 16),
  duration: __ENV.DURATION || "15s",
  summaryTrendStats: ["avg", "med", "p(95)", "p(99)", "max"],
};

const scenarios = {
  list_anonymous: () => http.get(`${BASE}/api/articles?limit=20&offset=${Math.floor(Math.random() * 100)}`, anonymous),
  list_signed_in: () => http.get(`${BASE}/api/articles?limit=20`, auth()),
  list_by_tag: () => http.get(`${BASE}/api/articles?limit=20&tag=${pick(seed.tags)}`, anonymous),
  feed: () => http.get(`${BASE}/api/articles/feed?limit=20`, auth()),
  article: () => http.get(`${BASE}/api/articles/${pick(seed.slugs)}`, auth()),
  comments: () => http.get(`${BASE}/api/articles/${pick(seed.slugs)}/comments`, anonymous),
  tags: () => http.get(`${BASE}/api/tags`, anonymous),
  favorite_toggle: () => {
    const params = auth();
    const slug = pick(seed.slugs);
    http.post(`${BASE}/api/articles/${slug}/favorite`, null, params);
    return http.del(`${BASE}/api/articles/${slug}/favorite`, null, params);
  },
  create_article: () => http.post(`${BASE}/api/articles`, JSON.stringify({ article: {
    title: `Load ${__VU}-${__ITER}-${Math.random()}`, description: "load", body: "load body", tagList: [pick(seed.tags)] } }),
    auth()),
};

export default function () {
  const response = scenarios[__ENV.SCENARIO]();
  check(response, { "status 2xx": (r) => r.status >= 200 && r.status < 300 });
}
