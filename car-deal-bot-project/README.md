# Car Deal Bot

Texts you the moment a below-market car shows up on any of ~8 sites (free) or 30+ sites (with one paid API key).

## What you get

A bot that runs every 15 minutes, scans every car site it can reach, and texts you only about **actual deals** — below-market-value listings, not every new posting. You wake up to three texts a day, each one an actionable link.

## Pick your path

### Path A — Easiest possible, zero coding (recommended)

1. Follow [**DEPLOY.md**](DEPLOY.md). It's a step-by-step with GitHub + Twilio.
2. Total time: ~20 minutes.
3. Total cost: ~$3–5/month (Twilio only).
4. You never touch code. Ever.

### Path B — Run on your computer

```bash
bash setup.sh
```

The script walks you through Twilio setup interactively. Then add a cron entry from `crontab.example`. Only runs while your computer is on.

## What it covers

**Free, built in:**
- Craigslist (22+ regions, IL + neighboring states)
- eBay Motors (free API key, 2-minute signup)
- CarMax (nationwide inventory)
- Carvana (nationwide inventory)
- Bring a Trailer, Hemmings (classic/enthusiast — off by default)
- Any RSS feed you paste into config

**One paid key unlocks:**
- AutoTrader, Cars.com, CarGurus, TrueCar, Edmunds, KBB, dealer inventory nationwide
- Pricing: ~$50/mo via Marketcheck API
- Optional — the bot works fine without it

**Not feasible (use their apps' native alerts instead):**
- Facebook Marketplace — they actively block bots; use the FB app's saved-search notifications
- OfferUp — same
- CarGurus direct — use Marketcheck, which licenses their data

See [SOURCES.md](SOURCES.md) for the full coverage table.

## What counts as a "deal"

A listing triggers a text if **either** is true:

1. The price is below $4,000 (configurable — the absolute-bargain floor).
2. The price is 15%+ below the 30-day rolling median for the same make/model/year range.

Dials are all in `config.py`. Make it pickier or looser to taste.

## Tweaking

Everything you might want to change lives in `config.py`:

| What | Where |
|---|---|
| Which cars | `SEARCH_QUERIES` |
| Max price | `MAX_PRICE` |
| How picky the deal detector is | `DEAL_THRESHOLD_PERCENT` |
| Which regions | `CRAIGSLIST_REGIONS` |
| Absolute bargain price | `INSTANT_FLAG_UNDER` |
| Text rate limit | `MAX_ALERTS_PER_RUN` |

## Troubleshooting

See the Troubleshooting section in [DEPLOY.md](DEPLOY.md). Most common:

- **Too many texts** → raise `DEAL_THRESHOLD_PERCENT` to 0.20.
- **No texts at all** → the bot needs 2–3 days of data before the market-comp math kicks in. Check GitHub Actions logs to confirm sources are running.
- **Twilio "unverified number"** → verify your phone in Twilio console, or upgrade the account.

## Files in this project

```
car-deal-bot/
├── README.md                   ← you are here
├── DEPLOY.md                   ← step-by-step 24/7 deployment (no-code)
├── SOURCES.md                  ← every site we cover, and why we don't cover others
├── config.py                   ← what to search for
├── main.py                     ← entry point
├── setup.sh                    ← one-command local setup
├── storage.py                  ← SQLite dedup + comp history
├── deal_detector.py            ← "is this a deal?" logic
├── notifier.py                 ← Twilio SMS
├── sources/
│   ├── base.py                 ← plugin base class
│   ├── craigslist.py
│   ├── ebay.py
│   ├── carmax.py
│   ├── carvana.py
│   ├── marketcheck.py          ← paid, unlocks AutoTrader/Cars.com/CarGurus/etc
│   ├── bringatrailer.py
│   ├── hemmings.py
│   └── generic_rss.py          ← paste any RSS URL into config.py
├── requirements.txt
├── Dockerfile                  ← for cloud/VPS hosting
├── crontab.example             ← for running on your own computer
└── .github/workflows/scan.yml  ← for running free 24/7 on GitHub Actions
```

## Adding a new site

1. Copy `sources/craigslist.py` to `sources/newsite.py`.
2. Rewrite the class to scrape/query the new site.
3. Add `"sources.newsite"` to the list in `sources/__init__.py`.
4. Done — main.py auto-discovers it.

## Legal and ethical notes

The bot hits public pages at a polite rate (1.5s between requests per site). Craigslist RSS and eBay/Marketcheck APIs are legitimate public interfaces. CarMax and Carvana are reverse-engineered from their public web search — if they ask you to stop (unlikely at personal scale), stop. Never spin up dozens of copies to brute-force sites; that's abuse, it benefits nobody, and it gets IPs banned. If you share the project, keep the polite delay.
