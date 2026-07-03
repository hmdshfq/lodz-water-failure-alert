# ZWiK Łódź Water Failure Watcher and Notifier — Never get caught mid-shower again

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

### 3. Create the repo and add secrets
1. Create a new GitHub repo and push these files to it.
2. Repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `TELEGRAM_TOKEN` = your bot token
   - `TELEGRAM_CHAT_ID` = your chat ID
   - `NEEDLE_PATTERN` = the regex pattern to watch for your residence

### 4. Test it
- Repo → **Actions** tab → select **Test ZWiK watcher notification** → **Run workflow**.
- If you get Telegram message "ZWiK watcher test message", your bot credentials work.
- To test the full scrape + match + notify pipeline, change `NEEDLE_PATTERN` in
  GitHub secrets to something currently on the page, run
  the main **ZWiK Łódź water failure watcher** workflow, then revert.

### 5 Test locally
- Add a `.env` file with `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, and `NEEDLE_PATTERN` set to your bot token, chat ID, and regex pattern, respectively.
- Run `python3 watcher.py` to test the script locally.
---

## Notes

- **Notified once per occurrence.** State is stored in `last_seen.txt`, which
  the workflow commits back to the repo. When the notice clears and later
  reappears, you get pinged again. For an hourly ping the whole time it's
  listed, delete the state logic in `watcher.py`.
- **Timing.** Cron is UTC and GitHub can delay scheduled runs on busy runners
  by several minutes. Fine for an hourly check.
- **Cost.** Free for public repos. Private repos use free Actions minutes
  (~1–2 min/run × 24/day is well within the monthly allowance).

---

## License

MIT — use it, break it, improve it.
