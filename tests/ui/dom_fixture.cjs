// Small deterministic DOM boundary for exercising shipped event handlers with node:test.
// It does not replace a browser acceptance journey or modify/instrument production source.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {webcrypto} = require('node:crypto');

const decode = text => String(text ?? '').replace(/&(amp|lt|gt|quot|#39);/g,
  (_, name) => ({amp: '&', lt: '<', gt: '>', quot: '"', '#39': "'"}[name]));
function attrs(text) {
  return Object.fromEntries([...text.matchAll(/([\w-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g)]
    .map(match => [match[1], decode(match[2] ?? match[3] ?? match[4] ?? '')]));
}
const camel = text => text.replace(/-([a-z])/g, (_, c) => c.toUpperCase());

class Element {
  constructor(document, tag = 'div', attributes = {}) {
    this.document = document; this.tagName = tag.toUpperCase(); this.attributes = {...attributes};
    this.children = []; this.fields = []; this.elements = {}; this.dataset = {}; this.listeners = {};
    this.disabled = false; this.hidden = false; this.open = false; this.removed = false;
    this.value = attributes.value || ''; this.checked = Object.hasOwn(attributes, 'checked');
    this.id = attributes.id; this.name = attributes.name; this.type = attributes.type || '';
    this.selectedOptions = []; this.contentWindow = {}; this._html = ''; this._text = '';
    this.className = attributes.class || '';
    this.classList = {add: () => {}, remove: () => {}};
    for (const [key, value] of Object.entries(attributes)) if (key.startsWith('data-')) this.dataset[camel(key.slice(5))] = value;
    if (this.id) document.ids.set(this.id, this);
    document.nodes.push(this);
  }
  append(...nodes) { for (const node of nodes) { node.parentElement = this; this.children.push(node); } }
  prepend(node) { node.parentElement = this; this.children.unshift(node); }
  replaceChildren(...nodes) { this.children = []; this.append(...nodes); }
  remove() { this.removed = true; if (this.parentElement) this.parentElement.children = this.parentElement.children.filter(n => n !== this); }
  get textContent() { return this._text || this.children.map(child => child.textContent).join(''); }
  set textContent(value) { this._text = String(value ?? ''); this.children = []; }
  get innerHTML() { return this._html; }
  set innerHTML(value) { this._html = String(value); this._text = ''; this.document.markup(this, this._html); }
  insertAdjacentHTML(position, value) { this._html += value; this.document.markup(this, value, this.ownerForm); }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return this.attributes[name] ?? null; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  removeEventListener(type, fn) { this.listeners[type] = (this.listeners[type] || []).filter(item => item !== fn); }
  showModal() { this.open = true; }
  close() { this.open = false; for (const fn of this.listeners.close || []) fn({target: this}); }
  click() { this.document.clicks.push(this); }
  submit() { this.document.submissions.push(this); }
  closest(selector) { return this.document.matches(this, selector) ? this : this.parentElement?.closest(selector) || null; }
  querySelectorAll(selector) {
    if (selector.startsWith('#')) return [this.document.ids.get(selector.slice(1))].filter(Boolean);
    const candidates = this.tagName === 'FORM' ? this.fields : this.document.nodes;
    return candidates.filter(node => !node.removed && this.document.matches(node, selector));
  }
  querySelector(selector) {
    if (selector === '.toolbar .actions') return this.document.toolbarActions;
    return this.querySelectorAll(selector)[0] || null;
  }
}

function createEnvironment({section = 'Fixture', fetch: responder = () => ({})} = {}) {
  const document = {ids: new Map(), nodes: [], listeners: {}, clicks: [], submissions: []};
  document.createElement = tag => new Element(document, tag);
  document.getElementById = id => document.ids.get(id) || null;
  document.matches = (node, selector) => {
    const match = selector.match(/^(\w+)?(?:\[([\w-]+)(?:="([^"]*)")?\])?$/);
    if (match) return (!match[1] || node.tagName.toLowerCase() === match[1]) &&
      (!match[2] || Object.hasOwn(node.attributes, match[2]) && (match[3] === undefined || node.attributes[match[2]] === match[3]));
    return selector.startsWith('.') && node.className.split(/\s+/).includes(selector.slice(1));
  };
  document.querySelector = selector => document.body.querySelector(selector);
  document.querySelectorAll = selector => document.body.querySelectorAll(selector);
  document.addEventListener = (name, fn) => (document.listeners[name] ||= []).push(fn);
  document.parseForm = (form, markup) => {
    const add = (tag, attributes, inner = '') => {
      const node = new Element(document, tag, attrs(attributes)); node.ownerForm = form; node.parentElement = form;
      if (tag === 'textarea') node.value = decode(inner);
      if (tag === 'select') {
        const options = [...inner.matchAll(/<option\b([^>]*)>([\s\S]*?)<\/option>/g)].map(match => {
          const options = attrs(match[1]); return {value: options.value ?? decode(match[2]), selected: Object.hasOwn(options, 'selected')};
        });
        node.selectedOptions = options.filter(option => option.selected);
        node.value = node.selectedOptions[0]?.value ?? options[0]?.value ?? '';
      }
      if (node.name) form.elements[node.name] = node;
      form.fields.push(node); return node;
    };
    for (const match of markup.matchAll(/<input\b([^>]*)>/g)) add('input', match[1]);
    for (const tag of ['textarea', 'select', 'button', 'output'])
      for (const match of markup.matchAll(new RegExp('<' + tag + '\\b([^>]*)>([\\s\\S]*?)<\\/' + tag + '>', 'g'))) add(tag, match[1], match[2]);
    for (const match of markup.matchAll(/<fieldset\b([^>]*)>/g)) add('fieldset', match[1]);
    for (const match of markup.matchAll(/<(?:div|section)\b([^>]*\bid="[^"]+"[^>]*)>/g)) add('div', match[1]);
  };
  document.markup = (owner, markup, owningForm) => {
    if (owningForm) { document.parseForm(owningForm, markup); return; }
    for (const match of markup.matchAll(/<form\b([^>]*)>([\s\S]*?)<\/form>/g)) {
      const form = new Element(document, 'form', attrs(match[1])); form.parentElement = owner;
      document.parseForm(form, match[2]);
    }
    for (const match of markup.matchAll(/<(\w+)\b([^>]*\bid="[^"]+"[^>]*)>/g)) {
      const values = attrs(match[2]);
      if (!document.ids.has(values.id) || ['iframe', 'output'].includes(match[1])) {
        const node = new Element(document, match[1], values); node.parentElement = owner;
      }
    }
    for (const match of markup.matchAll(/<button\b([^>]*\bdata-action="[^"]+"[^>]*)>/g)) {
      const node = new Element(document, 'button', attrs(match[1])); node.parentElement = owner;
    }
  };
  document.body = new Element(document, 'body');
  document.body.dataset = {section, euid: 'artifact-fixture', admin: 'true', writable: 'true', internal: 'true'};
  for (const id of ['content', 'editor', 'editor-body', 'notice', 'title', 'euid-lookup', 'lookup', 'message', 'tokens', 'new-token'])
    new Element(document, id === 'euid-lookup' ? 'form' : 'div', {id});
  document.toolbarActions = new Element(document, 'div', {class: 'actions'});
  const calls = [], assigned = [], copied = [], blobs = [], errors = [], windows = {};
  const location = {origin: 'https://dewey.example.test', pathname: '/fixture', search: '', assign: url => assigned.push(url)};
  class TestURL extends URL {
    static createObjectURL(blob) { blobs.push(blob); return 'blob:fixture'; }
    static revokeObjectURL() {}
  }
  class FormData {
    constructor(form) { this.rows = Object.entries(form.elements).filter(([, node]) => node.type !== 'checkbox' || node.checked).map(([name, node]) => [name, node.value]); }
    get(name) { return this.rows.find(row => row[0] === name)?.[1] ?? null; }
    [Symbol.iterator]() { return this.rows[Symbol.iterator](); }
  }
  const context = {document, location, URL: TestURL, URLSearchParams, Blob, FormData, crypto: webcrypto, AbortController, DOMException,
    navigator: {clipboard: {writeText: async text => copied.push(text)}}, history: {pushState() {}},
    setTimeout: () => 1, clearTimeout() {}, console,
    fetch: async (url, options = {}) => {
      calls.push({url: String(url), options});
      const result = await responder(String(url), options);
      const status = typeof result.status === 'number' ? result.status : 200;
      return {ok: status < 400, status,
        json: async () => Object.hasOwn(result, 'body') ? result.body : result};
    }, addEventListener: (type, fn) => (windows[type] ||= []).push(fn),
    removeEventListener: (type, fn) => { windows[type] = (windows[type] || []).filter(value => value !== fn); }};
  context.window = context;
  vm.createContext(context);
  const env = {context, document, calls, assigned, copied, blobs, errors, windows, location,
    node: id => document.getElementById(id),
    load(file) {
      const filename = path.resolve(__dirname, '../../dewey_service/static', file);
      new vm.Script(fs.readFileSync(filename, 'utf8'), {filename}).runInContext(context);
    },
    async submit(id) { const form = env.node(id); await form.onsubmit({target: form, currentTarget: form, preventDefault() {}}); await flush(); },
    async click(action, value = '') {
      const target = new Element(document, 'button', {'data-action': action, 'data-value': value});
      for (const handler of document.listeners.click || []) handler({target, preventDefault() {}});
      await flush();
    }};
  return env;
}

async function flush() { for (let i = 0; i < 6; i++) await new Promise(resolve => setImmediate(resolve)); }
const plain = value => JSON.parse(JSON.stringify(value));
module.exports = {createEnvironment, Element, flush, plain};
