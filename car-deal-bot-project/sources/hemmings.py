"""
Hemmings — classic car marketplace with a stable RSS feed.

Off by default. Enable with HEMMINGS_ENABLED=1 in .env.
"""
from __future__ import annotations

import logging
import os
import re
import time
from typing import Iterator, Optional

import feedparser
import requests

import config
from storage import Listing
from .base import Source


log = logging.getLogger(__name__)

RSS_URL = "https://www.hemmings.com/classifieds/dealer/feed.xml"

_YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
_PRICE_RE = re.compile(r"\$\s?([\d,]+)")


class HemmingsSource(Source):
    name = "hemmings"
    description = "Hemmings classic-car classifieds RSS"

    def iter_listings(self) -> Iterator[Listing]:
        try:
            resp = requests.get(
                RSS_URL,
                headers={"User-Agent": config.USER_AGENT},
                timeout=config.REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as e:
            log.warning("Hemmings fetch failed: %s", e)
            return
        time.sleep(config.POLITE_DELAY)

        if resp.status_code != 200:
            return

        feed = feedparser.parse(resp.content)
        for entry in feed.entries:
            title = getattr(entry, "title", "") or ""
            url = getattr(entry, "link", "") or ""
            summary = getattr(entry, "summary", "") or ""
            if not url:
                continue

            blob = f"{title} {summary}"
            price_match = _PRICE_RE.search(blob)
            price = (
                int(price_match.group(1).replace(",", ""))
                if price_match else None
            )
            year_match = _YEAR_RE.search(title)
            year = int(year_match.group(1)) if year_match else None

            if price is not None:
                if price < config.MIN_PRICE or price > config.MAX_PRICE:
                    continue

            yield Listing(
                url=url,
                source="hemmings",
                title=title,
                price=price,
                year=year,
                make=None,
                model=None,
                miles=None,
                location="Hemmings (classic)",
            )


def get_sources():
    if os.environ.get("HEMMINGS_ENABLED", "").strip() != "1":
        return []
    return [HemmingsSource()]
