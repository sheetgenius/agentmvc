import {LitElement, html, nothing} from 'lit';
import {request} from './api.js';
import {subscribe} from './live.js';

const articlePath = id => `/shares/${id}/article`;

class SharedEditor extends LitElement {
  static properties = {
    serverArticle: {state: true},
    draft: {state: true},
    baseRevision: {state: true},
    presence: {state: true},
    connection: {state: true},
    page: {state: true},
    conflict: {state: true},
    error: {state: true},
  };

  constructor() {
    super();
    this.serverArticle = null;
    this.draft = null;
    this.baseRevision = null;
    this.presence = 0;
    this.connection = 'connecting';
    this.page = 'loading';
    this.conflict = false;
    this.error = '';
    this.id = location.pathname.match(/^\/edit\/([A-Za-z0-9_-]+)$/)?.[1];
    this.key = new URLSearchParams(location.hash.slice(1)).get('key');
  }

  createRenderRoot() { return this; }

  connectedCallback() {
    super.connectedCallback();
    if (!this.id || !this.key) { this.page = 'invalid_link'; return; }
    this.open();
  }

  disconnectedCallback() {
    this.live?.close();
    super.disconnectedCallback();
  }

  async open() {
    try {
      const {article} = await request(articlePath(this.id), {key: this.key});
      this.adopt(article);
      this.live = subscribe(this.id, this.key, message => this.receive(message), status => { this.connection = status; });
    } catch (error) {
      this.page = error.status === 404 ? 'invalid_link' : 'error';
      this.error = error.message;
    }
  }

  adopt(article) {
    this.serverArticle = article;
    this.draft = {title: article.title, body: article.body};
    this.baseRevision = article.revision;
    this.conflict = false;
    this.page = 'editor';
  }

  get dirty() {
    return this.draft && this.serverArticle &&
      (this.draft.title !== this.serverArticle.title || this.draft.body !== this.serverArticle.body);
  }

  receive(message) {
    if (message.type === 'ready' || message.type === 'updated') {
      if (!this.serverArticle || message.article.revision > this.serverArticle.revision) {
        const dirty = this.dirty;
        this.serverArticle = message.article;
        if (!dirty) this.adopt(message.article);
      }
      if (message.type === 'ready') {
        this.presence = message.presence;
        this.page = 'editor';
      }
    }
    if (message.type === 'presence') this.presence = message.count;
    if (['room_full', 'invalid_link', 'revoked'].includes(message.type)) this.page = message.type;
  }

  change(field, event) {
    this.draft = {...this.draft, [field]: event.target.value};
  }

  async save() {
    this.error = '';
    try {
      const {article} = await request(articlePath(this.id), {
        method: 'PUT', key: this.key,
        body: {article: {...this.draft, revision: this.baseRevision}},
      });
      this.adopt(article);
    } catch (error) {
      if (error.status === 409 && error.data?.article) {
        this.serverArticle = error.data.article;
        this.conflict = true;
      } else {
        this.error = error.message;
      }
    }
  }

  async copyLink() {
    await navigator.clipboard.writeText(location.href);
  }

  render() {
    if (this.page === 'loading') return html`<main><p>Opening editor…</p></main>`;
    if (this.page === 'room_full') return html`<main class="notice"><h1>This editing room is full</h1><p>Up to 100 people can connect at once.</p><button @click=${() => { this.page = 'loading'; this.live.retry(); }}>Retry</button></main>`;
    if (this.page === 'invalid_link' || this.page === 'revoked') return html`<main class="notice"><h1>Link unavailable</h1><p>This editing link is invalid or has been revoked.</p></main>`;
    if (this.page === 'error') return html`<main class="notice"><h1>Could not open editor</h1><p>${this.error}</p></main>`;
    return html`
      <header><a class="brand" href="/">Conduit</a><span>Shared editor</span></header>
      <main>
        <div class="meta"><span>${this.connection}</span><span>${this.presence} here</span><span>Revision ${this.serverArticle.revision}</span></div>
        <label>Title <input name="title" .value=${this.draft.title} @input=${event => this.change('title', event)} /></label>
        <label>Body <textarea name="body" rows="16" .value=${this.draft.body} @input=${event => this.change('body', event)}></textarea></label>
        ${this.dirty && this.serverArticle.revision > this.baseRevision ? html`<p class="warning">A newer version is available. Your text is still here.</p>` : nothing}
        ${this.conflict ? html`<p class="warning">Someone saved a newer version. <button class="link" @click=${() => this.adopt(this.serverArticle)}>Load their version</button></p>` : nothing}
        ${this.error ? html`<p class="warning">${this.error}</p>` : nothing}
        <div class="actions"><button @click=${this.save} ?disabled=${!this.dirty}>Save</button><a href=${location.href} target="_blank" rel="noopener noreferrer">Open in another tab</a><button class="link" @click=${this.copyLink}>Copy editing link</button></div>
      </main>`;
  }
}

customElements.define('shared-editor', SharedEditor);
