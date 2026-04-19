"""
Generic RSS source — paste any RSS/Atom URL into config.GENERIC_RSS_FEEDS
and the bot will monitor it.

Use cases:
  * Dealer websites that expose an RSS feed of new inventory
  * Forum FS sections (e.g., car-specific forums)
  * Third-party aggregators that publish RSS

Each feed item is treated as a single listing. Price/year/miles are parsed
heuristically from title + summary — same regex approach Craigslist uses.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Iterator, Optional

import feedparser
import requests

import config
from storage import Listing
from .base import Source


log = logging.getLogger(__name__)

_YEAR_RE = re.compile(r"\b(19[89]\d|20[0-2]\d)\b")
_MILES_RE = re.compile(
    # Order matters: match "95k" before bare "95" so "95k miles" == 95000.
    r"(\d{1,3}\s?[kK]|\d{2,3}(?:[,\s]?\d{3})?)\s*(?:mi|miles)\b",
    re.IGNORECASE,
)
_PRICE_RE = re.compile(r"\$\s?([\d,]+)")


def _parse(s: str):
    price = _PRICE_RE.search(s)
    year = _YEAR_RE.search(s)
    miles = _MILES_RE.search(s)

    price_v = int(price.group(1).replace(",", "")) if price else None
    year_v = int(year.group(1)) if year else None

    miles_v: Optional[int] = None
    if miles:
        raw = miles.group(1).lower().replace(",", "").replace(" ", "")
        if raw.endswith("k"):
            try:
                miles_v = int(float(raw[:-1]) * 1000)
            except ValueError:
                miles_v = None
        else:
            try:
                miles_v = int(raw)
            except ValueError:
                miles_v = None
    return price_v, year_v, miles_v


class GenericRssSource(Source):
    def __init__(self, url: str, label: str):
        self.url = url
        self.label = label
        self.name = f"rss:{label}"
        self.description = f"Custom RSS feed: {label}"

    def iter_listings(self) -> Iterator[Listing]:
        try:
            resp = requests.get(
                self.url,
                headers={"User-Agent": config.USER_AGENT},
                timeout=config.REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as e:
            log.warning("[%s] fetch failed: %s", self.label, e)
            return

        time.sleep(config.POLITE_DELAY)
        if resp.status_code != 200:
            log.warning("[%s] HTTP %s", self.label, resp.status_code)
            return

        feed = feedparser.parse(resp.content)
        for entry in feed.entries:
            title = getattr(entry, "title", "") or ""
            url = getattr(entry, "link", "") or ""
            summary = getattr(entry, "summary", "") or ""
            if not url:
                continue

            blob = f"{title} {summary}"
            price, year, miles = _parse(blob)

            if price is None:
                # If the feed doesn't list prices, still record but deal
                # detector will ignore it (no price).
                pass
            elif price < config.MIN_PRICE or price > config.MAX_PRICE:
                continue

            yield Listing(
                url=url,
                source=f"rss:{self.label}",
                title=title,
                price=price,
                year=year,
                make=None,
                model=None,
                miles=miles,
                location=self.label,
            )


def get_sources():
    feeds = getattr(config, "GENERIC_RSS_FEEDS", [])
    return [GenericRssSource(url=f["url"], label=f["label"]) for f in feeds]
