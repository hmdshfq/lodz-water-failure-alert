import { Hono } from 'hono';

// --- Constants (match watcher.py) ---
const LISTING_URL = 'https://zwik.lodz.pl/pl/artykuly/302/awarie';
const BASE = 'https://zwik.lodz.pl';
const TG_API = 'https://api.telegram.org/bot{token}/sendMessage';
const UA = 'Mozilla/5.0 (zwik-watcher; +cloudflare-workers)';

async function fetchText(url) {
  const resp = await fetch(url, { headers: { 'User-Agent': UA } });
  if (!resp.ok) throw new Error(`HTTP ${resp.status} for ${url}`);
  return resp.text();
}

async function latestAnnouncementUrl() {
  const html = await fetchText(LISTING_URL);
  const m = html.match(/\/pl\/artykul\/302\/\d+\/komunikat[^"']*/);
  return m ? BASE + m[0] : LISTING_URL;
}

async function notify(env, text) {
  const url = TG_API.replace('{token}', env.TELEGRAM_TOKEN);
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: env.TELEGRAM_CHAT_ID,
      text,
      disable_web_page_preview: false,
    }),
  });
  if (!resp.ok) throw new Error(`Telegram API error: ${resp.status}`);
  await resp.text();
}

async function runCheck(env) {
  const needle = new RegExp(env.NEEDLE_PATTERN || '{location}', 'i');
  const url = await latestAnnouncementUrl();
  const page = await fetchText(url);
  const hit = needle.test(page);

  const previous = (await env.LAST_SEEN.get('last_seen')) || '';
  const current = hit ? url : '';

  if (hit && current !== previous) {
    await notify(env, `\uD83D\uDEB0 Water failure alert! Your residence appears in the latest outage notice.\n\n${url}`);
    await env.LAST_SEEN.put('last_seen', current);
    return `MATCH -> notified for ${url}`;
  } else if (hit) {
    return `MATCH but already notified for ${url}`;
  } else {
    await env.LAST_SEEN.put('last_seen', '');
    return 'no match';
  }
}

async function sendTestMessage(env) {
  await notify(env, '\u2705 ZWiK watcher test message. If you can read this, your Telegram token and chat ID are wired up correctly.');
  return 'test message sent';
}

const app = new Hono();

app.get('/test', async (c) => c.text(await sendTestMessage(c.env)));
app.get('/run', async (c) => c.text(await runCheck(c.env)));
app.get('/', (c) => c.text('ZWiK water watcher running. Routes: /test, /run'));

export default {
  fetch: app.fetch,
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runCheck(env));
  },
};

if (typeof globalThis.__selfCheck === 'undefined') {
  globalThis.__selfCheck = true;
  const sample = `<a href="/pl/artykul/302/1234/komunikat-2025-07-01">link</a>`;
  const assert = (cond, msg) => { if (!cond) throw new Error('SELF-CHECK FAIL: ' + msg); };
  const m = sample.match(/\/pl\/artykul\/302\/\d+\/komunikat[^"']*/);
  assert(m && m[0] === '/pl/artykul/302/1234/komunikat-2025-07-01', 'href regex');
  assert(new RegExp('mickiewicza\\s+4(?![0-9])', 'i').test('Mickiewicza 4 ulica'), 'needle ci');
  assert(!new RegExp('mickiewicza\\s+4(?![0-9])', 'i').test('Mickiewicza 42'), 'needle negative lookahead');
}