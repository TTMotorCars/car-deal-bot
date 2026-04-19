"""
eBay Motors — uses the Finding API (free, requires developer App ID).

Setup: sign up at https://developer.ebay.com, create a Production keyset,
paste the App ID into .env as EBAY_APP_ID. Leave blank to disable.
"""
from __future__ import annotations

import logging
import os
import re
import time
from typing import Iterator, Optional

import requests

import config
from storage import Listing
from .base import Source


log = logging.getLogger(__name__)

FINDING_ENDPOINT = "https://svcs.ebay.com/services/search/FindingService/v1"
EBAY_MOTORS_GLOBAL_ID = "EBAY-MOTOR"

_MODEL_ALIASES = {
    "mazda 3": ("mazda", "mazda3"),
    "mazda3": ("mazda", "mazda3"),
    "honda civic": ("honda", "civic"),
    "toyota corolla": ("toyota", "corolla"),
    "toyota camry": ("toyota", "camry"),
    "hyundai elantra": ("hyundai", "elantra"),
}

_YEAR_RE = re.compile(r"\b(19[89]\d|20[0-2]\d)\b")
_MILES_RE = re.compile(
    # Order matters: match "95k" before bare "95" so "95k miles" == 95000.
    r"(\d{1,3}\s?[kK]|\d{2,3}(?:[,\s]?\d{3})?)\s*(?:mi|miles)\b",
    re.IGNORECASE,
)


def _canonicalize(query: str):
    return _MODEL_ALIASES.get(query.lower().strip(), (None, None))


def _year(s: str) -> Optional[int]:
    m = _YEAR_RE.search(s or "")
    return int(m.group(1)) if m else None


def _miles(s: str) -> Optional[int]:
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


class EbayMotorsSource(Source):
    name = "ebay_motors"
    description = "eBay Motors Finding API (requires free EBAY_APP_ID)"

    def __init__(self, app_id: str):
        self.app_id = app_id

    def iter_listings(self) -> Iterator[Listing]:
        for query in config.SEARCH_QUERIES:
            make, model = _canonicalize(query)
            params = {
                "OPERATION-NAME": "findItemsByKeywords",
                "SERVICE-VERSION": "1.0.0",
                "SECURITY-APPNAME": self.app_id,
                "GLOBAL-ID": EBAY_MOTORS_GLOBAL_ID,
                "RESPONSE-DATA-FORMAT": "JSON",
                "REST-PAYLOAD": "",
                "keywords": query,
                "paginationInput.entriesPerPage": "50",
                "sortOrder": "PricePlusShippingLowest",
                "buyerPostalCode": config.EBAY_ZIP_CODE,
                "itemFilter(0).name": "MaxPrice",
                "itemFilter(0).value": str(config.MAX_PRICE),
                "itemFilter(0).paramName": "Currency",
                "itemFilter(0).paramValue": "USD",
                "itemFilter(1).name": "MinPrice",
                "itemFilter(1).value": str(config.MIN_PRICE),
                "itemFilter(2).name": "MaxDistance",
                "itemFilter(2).value": str(config.EBAY_MAX_DISTANCE_MILES),
                "itemFilter(3).name": "LocatedIn",
                "itemFilter(3).value": "US",
            }

            try:
                resp = requests.get(
                    FINDING_ENDPOINT,
                    params=params,
                    headers={"User-Agent": config.USER_AGENT},
                    timeout=config.REQUEST_TIMEOUT_SECONDS,
                )
            except requests.RequestException as e:
                log.warning("eBay fetch failed: %s", e)
                continue

            time.sleep(config.POLITE_DELAY)

            if resp.status_code != 200:
                log.warning("eBay HTTP %s: %s", resp.status_code, resp.text[:200])
                continue

            try:
                data = resp.json()
                items = (
                    data["findItemsByKeywordsResponse"][0]
                    ["searchResult"][0].get("item", [])
                )
            except (ValueError, KeyError, IndexError):
                continue

            for it in items:
                try:
                    title = it.get("title", [""])[0]
                    url = it.get("viewItemURL", [""])[0]
                    price_info = (
                        it.get("sellingStatus", [{}])[0]
                        .get("currentPrice", [{}])[0]
                    )
                    price = price_info.get("__value__")
                    price = int(float(price)) if price is not None else None
                    location = it.get("location", [""])[0]
                except (KeyError, IndexError, ValueError, TypeError):
                    continue

                if not url or price is None:
                    continue
                if price < config.MIN_PRICE or price > config.MAX_PRICE:
                    continue

                yield Listing(
                    url=url,
                    source="ebay_motors",
                    title=title,
                    price=price,
                    year=_year(title),
                    make=make,
                    model=model,
                    miles=_miles(title),
                    location=location,
                )


def get_sources():
    if not config.EBAY_ENABLED:
        return []
    app_id = os.environ.get("EBAY_APP_ID", "").strip()
    if not app_id:
        log.info("EBAY_APP_ID not set — eBay Motors disabled.")
        return []
    return [EbayMotorsSource(app_id=app_id)]
