"""
Bring a Trailer — enthusiast/auction site with a stable public RSS feed.

Off by default (not cheap commuters). Flip `BRING_A_TRAILER_ENABLED=1` in
.env to turn it on. Good for catching classic or unusual deals.
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

RSS_URL = "https://bringatrailer.com/feed/"

_YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
_PRICE_RE = re.compile(r"\$\s?([\d,]+)")


class BringATrailerSource(Source):
    name = "bring_a_trailer"
    description = "Bring a Trailer public RSS feed (enthusiast auctions)"

    def iter_listings(self) -> Iterator[Listing]:
        try:
            resp = requests.get(
                RSS_URL,
                headers={"User-Agent": config.USER_AGENT},
                timeout=config.REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as e:
            log.warning("BaT fetch failed: %s", e)
            return
        time.sleep(config.POLITE_DELAY)

        if resp.status_code != 200:
            return

        feed = feedparser.parse(resp.content)
        for entry in feed.entries:
            title = getattr(entry, "title", "") or ""
            url = getattr(entry, "link", "") or ""
            if not url:
                continue

            year_match = _YEAR_RE.search(title)
            year = int(year_match.group(1)) if year_match else None

            # BaT listings are auctions — no fixed price in RSS. We yield
            # with price=None; the deal detector will skip (no price)
            # unless you extend this module to fetch current high bid.
            yield Listing(
                url=url,
                source="bring_a_trailer",
                title=title,
                price=None,
                year=year,
                make=None,
                model=None,
                miles=None,
                location="online auction",
            )


def get_sources():
    if os.environ.get("BRING_A_TRAILER_ENABLED", "").strip() != "1":
        return []
    return [BringATrailerSource()]
