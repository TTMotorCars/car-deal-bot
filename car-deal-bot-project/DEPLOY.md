# How to make it run 24/7 (no-code guide)

This guide assumes zero coding knowledge. Follow it top to bottom and you'll have a bot that texts you car deals forever, totally hands-off, for about $3–5/month.

## Monthly cost estimate

| Item | Cost | Required? |
|---|---|---|
| Twilio phone number | $1.15/mo | Yes (for texts) |
| Twilio texts | ~$0.01/text, ~$2–3/mo realistic | Yes |
| GitHub Actions runner | $0 (public repo) | Yes (to run 24/7) |
| Marketcheck API (AutoTrader/Cars.com/CarGurus etc) | $50/mo | Optional |
| **Total minimum** | **~$3–5/mo** | |
| **Total with full dealer coverage** | **~$53–55/mo** | |

## Step-by-step

### Step 1 — Create a Twilio account (5 min)

1. Go to [twilio.com/try-twilio](https://www.twilio.com/try-twilio).
2. Sign up with email. Verify your real phone number.
3. On the dashboard, click **"Get a Twilio phone number"**. Pick one. Costs $1.15/mo — charged to your Twilio credit, not your card until you upgrade.
4. On the Twilio console homepage, write down these three things:
   - **Account SID** (starts with `AC...`)
   - **Auth Token** (click the eye icon to reveal)
   - **Phone number** you just bought, in format like `+13125551212`

That's Twilio done.

### Step 2 — Create a GitHub account and upload the bot (10 min)

1. Go to [github.com](https://github.com/) and sign up if you don't have an account.
2. Click the **+** icon top-right → **New repository**.
3. Name it whatever you want (e.g., `car-deal-bot`). Make it **Public** (this matters — free GitHub Actions minutes are unlimited on public repos).
4. Check **"Add a README file"** and click **Create repository**.
5. On the new repo page, click **Add file** → **Upload files**.
6. Drag in every file from this project folder except the `.env` file (never upload that — it has your Twilio password in it).
7. Scroll down, type "initial upload" as the message, click **Commit changes**.

### Step 3 — Add your secrets to GitHub (3 min)

This is how the bot knows your Twilio info without you uploading your password.

1. On your repo page, click **Settings** (top of the page).
2. Left sidebar: **Secrets and variables** → **Actions**.
3. Click **New repository secret**. Add each of these one by one (name exactly as shown):

| Name | Value |
|---|---|
| `TWILIO_ACCOUNT_SID` | Your SID from Twilio, starts with AC |
| `TWILIO_AUTH_TOKEN` | Your auth token |
| `TWILIO_FROM_NUMBER` | Your Twilio number (format `+13125551212`) |
| `ALERT_TO_NUMBER` | Your real phone (format `+17735551212`) |

Optional — if you signed up for free/paid APIs:

| Name | Value |
|---|---|
| `EBAY_APP_ID` | Your eBay developer App ID (free) |
| `MARKETCHECK_API_KEY` | Your Marketcheck API key (paid ~$50/mo) |

### Step 4 — Turn on the automation (30 seconds)

1. On your repo, click the **Actions** tab.
2. GitHub might show a yellow banner "Workflows aren't being run on this forked repository" — click **"I understand my workflows, go ahead and enable them"**.
3. On the left, click **"Scan for car deals"**.
4. A **Run workflow** button will appear — click it once to do your first test run.

That's it. From now on, GitHub will automatically scan every 15 minutes, day and night, forever.

### Step 5 — Verify it works

1. Back to the **Actions** tab. You'll see the run you just triggered.
2. Click into it to watch the logs.
3. If any deals match right now, you'll get a text within 2–3 minutes.
4. If none match, it'll still log "Run complete: scanned=..." — the bot is healthy, just no deals at that moment.

## Troubleshooting

**Twilio error "The 'To' number is unverified"** — Twilio trial accounts can only text numbers you've verified. Go to Twilio console → Phone Numbers → Verified Caller IDs → add your real phone. Or upgrade your Twilio account (~$20 minimum).

**GitHub Actions turned off after 60 days** — GitHub pauses schedules on repos with no activity. Just push any tiny edit to "poke" it, or click **Run workflow** manually to reset the timer.

**No deals coming through at all** — First 2–3 days the bot is learning "what's a normal price" for each car, so below-market detection needs comps to build up. Also check the Actions logs to confirm sources loaded successfully.

**Getting too many texts** — Edit `config.py` on GitHub (pencil icon). Raise `DEAL_THRESHOLD_PERCENT` from 0.15 to 0.20 (20% below market instead of 15%), or lower `MAX_ALERTS_PER_RUN` from 15 to 5.

**Want to add more cars** — Edit `config.py` on GitHub, add to `SEARCH_QUERIES`. Changes take effect on the next run.

## Running locally on your computer instead

If you'd rather run it on your laptop/desktop (cheaper if you already keep your computer on):

```bash
bash setup.sh
```

Then schedule it with cron (see `crontab.example`). Only works while your computer is on.
