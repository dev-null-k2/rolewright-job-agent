// Captures the README screenshots from the real tracker page (app/rolewright.html) with fictional demo data.
// Usage: python3 demo_data.py > demo.json && node shoot.js   (needs: npm i playwright && npx playwright install chromium)
const {chromium} = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '../..');
const OUT = path.join(ROOT, 'docs/media');
const DEMO = JSON.parse(fs.readFileSync(path.join(__dirname, 'demo.json'), 'utf8'));
const BODY = fs.readFileSync(path.join(ROOT, 'app/rolewright.html'), 'utf8');
const PAGE = `<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>${BODY}</body></html>`;

const server = http.createServer((q, r) => { r.writeHead(q.url === '/' ? 200 : 404, {'content-type': 'text/html; charset=utf-8'}); r.end(q.url === '/' ? PAGE : ''); });

function runtime(D) {
  const snap = arr => ({docs: arr.map(x => ({id: x.id, data: () => x})), metadata: {fromCache: false}, size: arr.length});
  const noop = async () => ({});
  const db = {
    collection: c => ({onSnapshot: f => { setTimeout(() => f(snap(D[c] || [])), 5); return () => {}; }, add: async () => ({id: 'x'})}),
    doc: p => {
      const [c, id] = p.split('/');
      const data = c === 'meta' ? D.meta[id] : (D[c] || []).find(x => x.id === id);
      return {onSnapshot: f => { setTimeout(() => f({exists: !!data, id, data: () => data}), 10); return () => {}; }, update: noop, set: noop, delete: noop};
    },
  };
  const sample = async (msgs, opts) => {
    const T = opts.tools || [];
    const call = (n, a) => { const t = T.find(t => t.name === n); return t ? t.execute(a) : null; };
    const r = call('search_roles', {status: 'new', sort: 'score', minPay: 1, limit: 3});
    const ids = (r && r.rows || []).slice(0, 3).map(x => x.id);
    call('show_roles', {ids});
    const text = "Start with these three. Each matches 5/5, lists pay, and has a message ready that passed every check:\n\n" +
      "1. **Northwind AI**, Forward Deployed Engineer: the recruiter's email is published on the posting, so send this one first.\n" +
      "2. **Lumen Labs**, Applied AI Engineer: remote, and your tailored resume leads with the support assistant.\n" +
      "3. **Harborline Health**, AI Engineer: the hiring manager is named, and the cover letter is ready.\n\n" +
      "After that, Lattice Grid's interview is Wednesday. Your prep notes are on its card.";
    for (let i = 40; i <= text.length; i += 40) opts.onText && opts.onText({text: text.slice(0, i)});
    opts.onText && opts.onText({text});
    return {text, truncated: false};
  };
  sample.limits = async () => ({tools: true});
  try { localStorage.setItem('rw_phone', '(555) 010-4242'); } catch (e) {}
  window.claude = {use: async name => ({db, sample, downloads: {save: async () => {}}, user: {me: async () => ({name: 'Maya'})}})[name] || null};
}

(async () => {
  await new Promise(r => server.listen(8781, r));
  fs.mkdirSync(OUT, {recursive: true});
  const browser = await chromium.launch();
  const errors = [];
  for (const scheme of ['light', 'dark']) {
    const ctx = await browser.newContext({viewport: {width: 1280, height: 860}, deviceScaleFactor: 2, colorScheme: scheme});
    const page = await ctx.newPage();
    page.on('pageerror', e => errors.push(e.message));
    await page.addInitScript(runtime, DEMO);
    await page.addInitScript(() => { const T = new Date('2026-11-09T16:20:00Z').getTime(); const O = Date; window.Date = class extends O { constructor(...a) { super(...(a.length ? a : [T])); } static now() { return T; } }; });
    await page.goto('http://localhost:8781/');
    await page.waitForTimeout(2500);
    const shot = async (name, clip) => { await page.waitForTimeout(400); await page.screenshot({path: path.join(OUT, `${name}-${scheme}.png`), ...(clip ? {clip} : {})}); };

    await shot('home');

    await page.keyboard.press('f');
    await page.waitForTimeout(600);
    await shot('focus', {x: 0, y: 0, width: 1280, height: 800});
    await page.keyboard.press('Escape');

    await page.click('#t-roles');
    await page.waitForTimeout(500);
    const held = await page.evaluate(() => [...document.querySelectorAll('#roles .note')].map(n => n.textContent).filter(t => /held back/.test(t)));
    if (held.length) console.log(scheme, 'held back:', held.slice(0, 5));
    await page.evaluate(() => document.querySelector('#roles [data-rprev]').click());
    await page.waitForTimeout(700);
    await shot('resume');
    await page.keyboard.press('Escape');

    await page.click('#t-today');
    await page.waitForTimeout(400);
    const q = page.locator('#askq');
    if (await q.count()) {
      await q.fill('What should I do first today?');
      await q.press('Enter');
      await page.waitForTimeout(1500);
      await page.evaluate(() => { const c = document.querySelector('#ask'); if (c) window.scrollTo(0, c.getBoundingClientRect().top + window.scrollY - 20); });
      await shot('ask');
    }
    await ctx.close();
  }
  await browser.close();
  server.close();
  console.log(errors.length ? 'page errors: ' + errors.join(' | ') : 'ok, no page errors');
})();
