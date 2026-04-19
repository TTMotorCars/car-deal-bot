"""
Craigslist source — pulls the public cars+trucks RSS feed for every
configured region.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Iterator, Optional
from urllib.parse import quote_plus

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

_MODEL_ALIASES = {
    "mazda 3": ("mazda", "mazda3"),
    "mazda3": ("mazda", "mazda3"),
    "honda civic": ("honda", "civic"),
    "toyota corolla": ("toyota", "corolla"),
    "toyota camry": ("toyota", "camry"),
    "hyundai elantra": ("hyundai", "elantra"),
}


def _canonicalize(query: str):
    return _MODEL_ALIASES.get(query.lower().strip(), (None, None))


def _parse_year(s: str) -> Optional[int]:
    m = _YEAR_RE.search(s or "")
    return int(m.group(1)) if m else None


def _parse_miles(s: str) -> Optional[int]:
    m = _MILES_RE.search(s or "")
    if not m:
        return None
    raw = m.group(1).lower().replace(",", "").replace(" ", "")
    if raw.endswith("k"):
        try:
            return int(float(raw[:-1]) * 1000)
        except ValueError:
            return None
    try:
        return int(raw)
    except ValueError:
        return None


def _parse_price(s: str) -> Optional[int]:
    m = _PRICE_RE.search(s or "")
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except ValueError:
        return None


class CraigslistSource(Source):
    name = "craigslist"
    description = "Craigslist cars+trucks RSS across all configured regions"

    def _rss_url(self, region: str, query: str) -> str:
        q = quote_plus(query)
        return (
            f"https://{region}.craigslist.org/search/cta"
            f"?query={q}"
            f"&max_price={config.MAX_PRICE}"
            f"&min_price={config.MIN_PRICE}"
            f"&auto_min_year={config.MIN_YEAR}"
            + (f"&auto_max_miles={config.MAX_MILES}" if config.MAX_MILES else "")
            + "&format=rss"
        )

    def iter_listings(self) -> Iterator[Listing]:
        for query in config.SEARCH_QUERIES:
            make, model = _canonicalize(query)
            for region in config.CRAIGSLIST_REGIONS:
                url = self._rss_url(region, query)
                try:
                    resp = requests.get(
                        url,
                        headers={"User-Agent": config.USER_AGENT},
                        timeout=config.REQUEST_TIMEOUT_SECONDS,
                    )
                except requests.RequestException as e:
                    log.warning("[%s/%s] fetch failed: %s", region, query, e)
                    time.sleep(config.POLITE_DELAY)
                    continue

                time.sleep(config.POLITE_DELAY)

                if resp.status_code != 200:
                    log.warning(
                        "[%s/%s] HTTP %s", region, query, resp.status_code
                    )
                    continue

                feed = feedparser.parse(resp.content)
                for entry in feed.entries:
                    title = getattr(entry, "title", "") or ""
                    link = getattr(entry, "link", "") or ""
                    summary = getattr(entry, "summary", "") or ""
                    if not link:
                        continue

                    blob = f"{title} {summary}"
                    price = _parse_price(title) or _parse_price(summary)
                    year = _parse_year(blob)
                    miles = _parse_miles(blob)

                    if price is None:
                        continue
                    if price < config.MIN_PRICE or price > config.MAX_PRICE:
                        continue
                    if config.MAX_MILES and miles and miles > config.MAX_MILES:
                        continue
                    if year and year < config.MIN_YEAR:
                        continue

                    yield Listing(
                        url=link,
                        source=f"craigslist:{region}",
                        title=title.strip(),
                        price=price,
                        year=year,
                        make=make,
                        model=model,
                        miles=miles,
                        location=region,
                    )


def get_sources():
    return [CraigslistSource()]
