import {test, expect} from '@playwright/test';
import {seed, json, LiveClient} from './helpers.js';

const backend = process.env.BACKEND_URL || 'http://127.0.0.1:4101';
const editorUrl = share => `/edit/${share.id}#key=${share.key}`;

test('three independent browsers share edits and presence without losing a dirty draft', async ({browser}) => {
  const share = await seed(backend);
  const contexts = await Promise.all(Array.from({length: 3}, () => browser.newContext()));
  try {
    const pages = await Promise.all(contexts.map(context => context.newPage()));
    for (let i = 0; i < pages.length; i++) {
      await pages[i].goto(editorUrl(share));
      await expect(pages[i].getByText(`${i + 1} here`)).toBeVisible();
    }
    await expect(pages[0].getByText('3 here')).toBeVisible();
    await pages[0].getByLabel('Body').fill('Saved by browser one');
    await pages[0].getByRole('button', {name: 'Save'}).click();
    await expect(pages[1].getByLabel('Body')).toHaveValue('Saved by browser one');
    await expect(pages[2].getByLabel('Body')).toHaveValue('Saved by browser one');

    await pages[1].getByLabel('Body').fill('Unsaved in browser two');
    await pages[2].getByLabel('Body').fill('Saved by browser three');
    await pages[2].getByRole('button', {name: 'Save'}).click();
    await expect(pages[1].getByText('A newer version is available.')).toBeVisible();
    await expect(pages[1].getByLabel('Body')).toHaveValue('Unsaved in browser two');
    await pages[1].getByRole('button', {name: 'Save'}).click();
    await expect(pages[1].getByText('Someone saved a newer version.')).toBeVisible();
    await expect(pages[1].getByLabel('Body')).toHaveValue('Unsaved in browser two');
    await pages[1].getByRole('button', {name: 'Load their version'}).click();
    await expect(pages[1].getByLabel('Body')).toHaveValue('Saved by browser three');

    await pages[0].reload();
    await expect(pages[0].getByLabel('Body')).toHaveValue('Saved by browser three');
    await contexts[2].close();
    await expect(pages[0].getByText('2 here')).toBeVisible();
  } finally {
    await Promise.all(contexts.map(context => context.close().catch(() => {})));
  }
});

test('the 101st editor sees Room full and can retry after a slot opens', async ({browser}) => {
  const share = await seed(backend);
  const sockets = [];
  const context = await browser.newContext();
  try {
    for (let count = 1; count <= 100; count++) {
      const socket = await new LiveClient(backend, share.id).open(share.key);
      sockets.push(socket);
      expect((await socket.next('ready')).presence).toBe(count);
    }
    const page = await context.newPage();
    await page.goto(editorUrl(share));
    await expect(page.getByRole('heading', {name: 'This editing room is full'})).toBeVisible();
    expect((await json(backend, `/shares/${share.id}/article`, {
      method: 'PUT', key: share.key,
      body: {article: {title: 'Current title', body: 'Saved while full', revision: 1}},
    })).status).toBe(200);
    sockets[0].close();
    await sockets[1].next('presence', message => message.count === 99);
    await page.getByRole('button', {name: 'Retry'}).click();
    await expect(page.getByText('100 here')).toBeVisible();
    await expect(page.getByLabel('Body')).toHaveValue('Saved while full');
  } finally {
    sockets.forEach(socket => socket.close());
    await context.close();
  }
});

test('revoking the link ends access to the editor', async ({browser}) => {
  const share = await seed(backend);
  const context = await browser.newContext();
  try {
    const page = await context.newPage();
    await page.goto(editorUrl(share));
    await expect(page.getByText('1 here')).toBeVisible();
    expect((await json(backend, `/articles/${share.slug}/share`, {method: 'DELETE', token: share.token})).status).toBe(204);
    await expect(page.getByRole('heading', {name: 'Link unavailable'})).toBeVisible();
  } finally {
    await context.close();
  }
});

test('a delayed save response preserves newer typing and socket state', async ({browser}) => {
  const share = await seed(backend);
  const contexts = await Promise.all([browser.newContext(), browser.newContext()]);
  let release;
  const released = new Promise(resolve => { release = resolve; });
  let committed;
  const saved = new Promise(resolve => { committed = resolve; });
  try {
    const [first, second] = await Promise.all(contexts.map(context => context.newPage()));
    await Promise.all([first.goto(editorUrl(share)), second.goto(editorUrl(share))]);
    await expect(first.getByText('2 here')).toBeVisible();
    await first.route('**/api/shares/*/article', async route => {
      if (route.request().method() !== 'PUT') return route.continue();
      const response = await route.fetch();
      committed();
      await released;
      await route.fulfill({response});
    });

    await first.getByLabel('Body').fill('Sent version');
    await first.getByRole('button', {name: 'Save'}).click();
    await saved;
    await first.getByLabel('Body').fill('Typed during save');
    await expect(second.getByLabel('Body')).toHaveValue('Sent version');
    await second.getByLabel('Body').fill('Newer remote version');
    await second.getByRole('button', {name: 'Save'}).click();
    await expect(first.getByText('Revision 3')).toBeVisible();
    release();
    await expect(first.getByLabel('Body')).toHaveValue('Typed during save');
    await expect(first.getByText('A newer version is available.')).toBeVisible();
  } finally {
    release?.();
    await Promise.all(contexts.map(context => context.close().catch(() => {})));
  }
});
