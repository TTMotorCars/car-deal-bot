"""
Car Deal Bot — main entry point.

Every registered source is loaded at startup; one run scans all of them
and texts you about any new below-market listings.

Usage:
  python main.py                 # real run
  DRY_RUN=1 python main.py       # print instead of texting
  python main.py --stats         # show DB stats and exit
  python main.py --list-sources  # show which sources are active + why
"""
from __future__ import annotations

import argparse
import logging
import sys

from dotenv import load_dotenv

import config
from deal_detector import evaluate
from notifier import send_sms
import sources
from storage import Storage


def setup_logging(verbose: bool):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run_once(storage: Storage) -> dict:
    log = logging.getLogger("run")

    active_sources = sources.load_all()
    if not active_sources:
        log.error("No sources loaded — did you set any API keys in .env?")
        return {"scanned": 0, "new": 0, "deals": 0, "sent": 0}

    log.info("Active sources: %s", ", ".join(s.name for s in active_sources))

    scanned = 0
    new_listings = 0
    deals_found = 0
    sent = 0

    for listing in sources.iter_all_listings(active_sources):
        scanned += 1

        if storage.already_seen(listing.url):
            continue

        new_listings += 1
        verdict = evaluate(listing, storage)

        alerted = False
        if verdict.is_deal:
            deals_found += 1
            log.info(
                "DEAL [%s]: %s | $%s | %s",
                listing.source,
                listing.title[:60],
                listing.price,
                verdict.reason,
            )
            if sent < config.MAX_ALERTS_PER_RUN:
                if send_sms(listing, verdict):
                    sent += 1
                    alerted = True

        storage.record(listing, alerted=alerted)

    summary = {
        "scanned": scanned,
        "new": new_listings,
        "deals": deals_found,
        "sent": sent,
    }
    log.info("Run complete: %s", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Car deal bot")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--list-sources", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    setup_logging(args.verbose)

    if args.list_sources:
        # Log info while loading so user can see which ones activated.
        for s in sources.load_all():
            print(f"  {s.name:20} {s.description}")
        return 0

    storage = Storage(config.DEDUPE_DB_PATH)

    if args.stats:
        print(storage.stats())
        return 0

    try:
        run_once(storage)
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception:
        logging.exception("Bot crashed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
