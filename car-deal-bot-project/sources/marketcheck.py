"""
Marketcheck source — ONE API key unlocks ~30 car sites.

Covered sites include:
  AutoTrader, Cars.com, CarGurus, TrueCar, Edmunds, KBB, Autobytel,
  AutoTempest, dealer websites nationwide, plus market-value analytics.

Pricing (as of late 2024):
  - Free tier:    1,000 requests/mo (barely enough for testing)
  - Starter:      ~$50/mo — 25k requests/mo (fine for a personal bot)
  - Growth/Pro:   higher tiers for real-time feeds

Setup:
  1. Sign up at https://apidocs.marketcheck.com/
  2. Copy your API key into .env as MARKETCHECK_API_KEY
  3. This source automatically turns on

API reference: https://apidocs.marketcheck.com/#cars-api
"""
from __future__ import annotations

import logging
import os
import time
from typing import Iterator, Optional

import requests

import config
from storage import Listing
from .base import Source


log = logging.getLogger(__name__)

SEARCH_URL = "https://mc-api.marketcheck.com/v2/search/car/active"

_MODEL_TO_SEARCH = {
    "honda civic": ("honda", "civic"),
    "toyota corolla": ("toyota", "corolla"),
    "toyota camry": ("toyota", "camry"),
    "mazda 3": ("mazda", "mazda3"),
    "mazda3": ("mazda", "mazda3"),
    "hyundai elantra": ("hyundai", "elantra"),
}


class MarketcheckSource(Source):
    name = "marketcheck"
    description = (
        "Marketcheck aggregate API — AutoTrader, Cars.com, CarGurus, "
        "TrueCar, Edmunds, 30+ sites (requires MARKETCHECK_API_KEY)"
    )

    def __init__(self, api_key: str):
        self.api_key = api_key

    def iter_listings(self) -> Iterator[Listing]:
        for query in config.SEARCH_QUERIES:
            mm = _MODEL_TO_SEARCH.get(query.lower().strip())
            if not mm:
                continue
            make, model = mm

            params = {
                "api_key": self.api_key,
                "make": make,
                "model": model,
                "year_range": f"{config.MIN_YEAR}-2026",
                "price_range": f"{config.MIN_PRICE}-{config.MAX_PRICE}",
                "miles_range": f"0-{config.MAX_MILES or 200000}",
                "zip": config.EBAY_ZIP_CODE,
                "radius": config.EBAY_MAX_DISTANCE_MILES,
                "sort_by": "price",
                "sort_order": "asc",
                "rows": 50,
                "start": 0,
            }

            try:
                resp = requests.get(
                    SEARCH_URL,
                    params=params,
                    headers={"User-Agent": config.USER_AGENT},
                    timeout=config.REQUEST_TIMEOUT_SECONDS,
                )
            except requests.RequestException as e:
                log.warning("Marketcheck fetch failed: %s", e)
                continue

            time.sleep(config.POLITE_DELAY)

            if resp.status_code == 401 or resp.status_code == 403:
                log.error("Marketcheck auth failed — check MARKETCHECK_API_KEY")
                return
            if resp.status_code == 429:
                log.warning("Marketcheck rate limit hit; stopping for this run")
                return
            if resp.status_code != 200:
                log.warning("Marketcheck HTTP %s", resp.status_code)
                continue

            try:
                data = resp.json()
            except ValueError:
                continue

            for it in data.get("listings", []):
                try:
                    url = it.get("vdp_url") or it.get("url")
                    if not url:
                        continue
                    price = it.get("price")
                    price = int(price) if price is not None else None
                    year = it.get("build", {}).get("year")
                    miles = it.get("miles")
                    trim = it.get("build", {}).get("trim", "") or ""
                    title = (
                        f"{year or ''} {make.title()} {model.title()} {trim}"
                    ).strip()
                    dealer = it.get("dealer", {}) or {}
                    location = (
                        f"{dealer.get('city', '')}, {dealer.get('state', '')}".strip(", ")
                        or it.get("source")
                        or "dealer"
                    )
                    # Capture which underlying site provided the listing.
                    sub_source = it.get("source") or "dealer"
                except (ValueError, TypeError, KeyError):
                    continue

                if price is None:
                    continue
                if price < config.MIN_PRICE or price > config.MAX_PRICE:
                    continue

                yield Listing(
                    url=url,
                    source=f"marketcheck:{sub_source}",
                    title=title,
                    price=price,
                    year=int(year) if year else None,
                    make=make,
                    model=model,
                    miles=int(miles) if miles else None,
                    location=location,
                )


def get_sources():
    key = os.environ.get("MARKETCHECK_API_KEY", "").strip()
    if not key:
        log.info("MARKETCHECK_API_KEY not set — Marketcheck disabled (no AutoTrader/Cars.com/CarGurus etc).")
        return []
    return [MarketcheckSource(api_key=key)]
