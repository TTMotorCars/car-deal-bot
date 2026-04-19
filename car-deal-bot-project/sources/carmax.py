"""
CarMax source — uses their public search endpoint (the same one their
website's search page calls).

NOTE: This is not a documented public API. CarMax has been known to change
the path and payload shape occasionally. If the response format shifts we
log and skip; the deal bot keeps running on other sources. If you find
CarMax consistently returning zero results, open your browser's devtools on
carmax.com while searching, find the `search` XHR call, and update
`SEARCH_URL` / the field names below.
"""
from __future__ import annotations

import logging
import time
from typing import Iterator, Optional

import requests

import config
from storage import Listing
from .base import Source


log = logging.getLogger(__name__)

# As observed 2024+. Subject to change — see note above.
SEARCH_URL = "https://www.carmax.com/cars/api/search/run"

_MODEL_TO_SEARCH = {
    "honda civic": ("Honda", "Civic"),
    "toyota corolla": ("Toyota", "Corolla"),
    "toyota camry": ("Toyota", "Camry"),
    "mazda 3": ("Mazda", "Mazda3"),
    "mazda3": ("Mazda", "Mazda3"),
    "hyundai elantra": ("Hyundai", "Elantra"),
}


class CarMaxSource(Source):
    name = "carmax"
    description = "CarMax nationwide inventory (reverse-engineered JSON)"

    def iter_listings(self) -> Iterator[Listing]:
        for query in config.SEARCH_QUERIES:
            make_model = _MODEL_TO_SEARCH.get(query.lower().strip())
            if not make_model:
                continue
            make, model = make_model

            payload = {
                "makes": [make],
                "models": [model],
                "priceFrom": config.MIN_PRICE,
                "priceTo": config.MAX_PRICE,
                "yearFrom": config.MIN_YEAR,
                "mileageTo": config.MAX_MILES or 200000,
                "zip": config.EBAY_ZIP_CODE,   # reuse the zip from config
                "distance": "nationwide",
                "skip": 0,
                "take": 50,
                "sort": "price-low",
            }

            try:
                resp = requests.post(
                    SEARCH_URL,
                    json=payload,
                    headers={
                        "User-Agent": config.USER_AGENT,
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    timeout=config.REQUEST_TIMEOUT_SECONDS,
                )
            except requests.RequestException as e:
                log.warning("CarMax fetch failed: %s", e)
                continue

            time.sleep(config.POLITE_DELAY)

            if resp.status_code != 200:
                log.info("CarMax HTTP %s — may need endpoint refresh", resp.status_code)
                continue

            try:
                data = resp.json()
            except ValueError:
                continue

            # The response schema has varied. Try a few shapes.
            items = (
                data.get("items")
                or data.get("results")
                or (data.get("searchResponse", {}) or {}).get("items")
                or []
            )

            for it in items:
                try:
                    stock = it.get("stockNumber") or it.get("id") or ""
                    if not stock:
                        continue
                    url = f"https://www.carmax.com/car/{stock}"
                    price = int(it.get("price") or 0) or None
                    year = it.get("year")
                    miles = it.get("mileage") or it.get("odometer")
                    title = (
                        f"{year or ''} {make} {model} "
                        f"{it.get('trim', '') or ''}"
                    ).strip()
                    location = (
                        it.get("storeName")
                        or it.get("location")
                        or "CarMax"
                    )
                except (ValueError, TypeError, KeyError):
                    continue

                if price is None:
                    continue
                if price < config.MIN_PRICE or price > config.MAX_PRICE:
                    continue

                yield Listing(
                    url=url,
                    source="carmax",
                    title=title,
                    price=price,
                    year=int(year) if year else None,
                    make=make.lower(),
                    model=model.lower(),
                    miles=int(miles) if miles else None,
                    location=location,
                )


def get_sources():
    return [CarMaxSource()]
