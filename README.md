# ZWiK Łódź Water Failure Watcher and Notifier

_Never get caught mid-shower again_

**Telegram alerts for water failures in Łódź, powered by ZWiK web scraping.**

---

## The Story

After getting stranded **twice** in the shower with shampoo in my hair and zero water pressure, I decided enough was enough. 

ZWiK Łódź posts water outage schedules on their website—but who checks that before hopping in the shower? This script does it for you.

---

## What it does

- **Crawls** the [official ZWiK Łódź website](https://zwik.lodz.pl/) at regular intervals
- **Detects** new water failure announcements
- **Pushes** instant notifications to your Telegram (or group/channel)
- **Runs quietly** in the background—you'll only hear from it when something breaks (literally)

---

## What it watches

It scrapes the stable failures listing (`.../artykuly/302/awarie`), finds the newest daily *komunikat* article, and searches that page. This avoids the stale-URL problem: the daily announcement URL changes every day, so watching a single date-specific page would break tomorrow.

---

## One-time setup

### 1. Create a Telegram bot
1. In Telegram, message **@BotFather** → `/newbot` → follow the prompts.
2. Copy the **bot token** it gives you (looks like `123456:ABC-DEF...`).

### 2. Get your chat ID
1. Send any message to your new bot (search its username, tap Start, say "hi").
2. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser.
3. Find `"chat":{"id":<NUMBER>}` — that number is your **chat ID**.

### 3. Create a KV namespace for state
```bash
npx wrangler kv namespace create LAST_SEEN
```
Copy the `id` from the output into `wrangler.jsonc` under `kv_namespaces[0].id`.

### 4. Set secrets and deploy
```bash
npm install
npx wrangler secret put TELEGRAM_TOKEN      # your bot token
npx wrangler secret put TELEGRAM_CHAT_ID    # your chat ID
npx wrangler secret put NEEDLE_PATTERN      # regex pattern for your residence
npx wrangler deploy
```

### 5. Test it
```bash
npx wrangler dev
```
- Visit `http://localhost:8787/test` to send a test Telegram message and verify your bot credentials work.
- Visit `http://localhost:8787/run` to run the full scrape + match + notify pipeline manually.
- To test the match pipeline, set `NEEDLE_PATTERN` to something currently on the page (via `.dev.vars` for local dev), hit `/run`, then revert.

---

## Notes

- **Notified once per occurrence.** State is stored in a Cloudflare KV namespace (`LAST_SEEN`). When the notice clears and later reappears, you get pinged again. For an hourly ping the whole time it's listed, delete the state logic in `src/index.js`.
- **Timing.** Cron runs every 3 hours via Cloudflare Cron Triggers. Cloudflare's scheduling is more reliable than GitHub Actions (no runner queue delays).
- **Cost.** Free tier covers this easily (Workers free plan: 100k requests/day; KV: 100k reads/day, 1k writes/day — ~8 cron runs/day is negligible).
- **Routes.** `GET /test` sends a test notification. `GET /run` runs the full check manually. The scheduled handler runs `runCheck` automatically every 3 hours.

---

## License

MIT — use it, break it, improve it.