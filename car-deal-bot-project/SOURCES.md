# Car Site Coverage

An honest accounting of which sites the bot supports, which require a paid key, and which aren't feasible.

## Free and supported out of the box

| Site | Status | How |
|---|---|---|
| Craigslist | ✅ Built-in | Public RSS feed across ~22 regions |
| eBay Motors | ✅ Built-in | Free Finding API (requires free key signup) |
| CarMax | ✅ Built-in | Reverse-engineered public search endpoint. Nationwide inventory. May need occasional endpoint refresh |
| Carvana | ✅ Built-in | Reverse-engineered public search endpoint. Nationwide inventory. May need occasional endpoint refresh |
| Bring a Trailer | ✅ Built-in (off by default) | Public RSS. Auctions, no fixed prices. Enable with `BRING_A_TRAILER_ENABLED=1` |
| Hemmings | ✅ Built-in (off by default) | Public RSS. Classic cars. Enable with `HEMMINGS_ENABLED=1` |
| Any site with an RSS feed | ✅ Built-in | Paste the URL into `GENERIC_RSS_FEEDS` in config.py |

## One paid key unlocks ~30 major sites

Sign up at [apidocs.marketcheck.com](https://apidocs.marketcheck.com/) (~$50/mo starter tier) and paste the key into `MARKETCHECK_API_KEY`. That single key gives you:

- AutoTrader
- Cars.com
- CarGurus
- TrueCar
- Edmunds
- KBB (listings & market values)
- AutoTempest aggregated inventory
- Dealer websites nationwide (tens of thousands)
- Plus VIN-based market value analytics

Marketcheck is the most cost-effective way to cover all these sites. Individually hitting them would either require a more expensive enterprise API from each, or fragile scraping that breaks constantly.

## Not feasible

| Site | Why |
|---|---|
| **Facebook Marketplace** | Active anti-bot measures. Any automation violates their ToS and breaks within days of deployment. Use the FB app's own saved-search notifications instead. |
| **OfferUp** | Same story — heavy anti-bot, no API. Use their app's notifications. |
| **CarGurus (direct)** | Aggressive anti-bot at their front door. Use Marketcheck, which licenses their data. |
| **Nextdoor Marketplace** | No public API, no automated access for third parties. |

## Consumer alternatives (free, no code)

If you want belt-and-suspenders coverage, install these apps and turn on native notifications:

- **Facebook Marketplace** (only reliable way to get FB alerts)
- **CarGurus** (great for price-drop alerts on their aggregated dealer data)
- **AutoTrader** / **Cars.com** (native saved searches)
- **AutoTempest.com** — aggregator across multiple sites with email alerts

Stacking these with the bot gives you near-complete coverage.

## Adding a new site yourself

1. Create `sources/newsite.py`.
2. Subclass `Source`, implement `iter_listings()`.
3. Add `"sources.newsite"` to `ALL_SOURCE_MODULES` in `sources/__init__.py`.

See `sources/craigslist.py` as the cleanest reference implementation.
