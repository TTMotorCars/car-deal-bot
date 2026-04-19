"""
Carvana source — uses their public inventory search endpoint.

Same caveat as CarMax: reverse-engineered, may break when Carvana tweaks
their front end. Log-and-skip on failure.
"""
from __future__ import annotations

import logging
import time
from typing import Iterator

import requests

import config
from storage import Listing
from .base import Source


log = logging.getLogger(__name__)

SEARCH_URL = "https://www.carvana.com/cars/api/v2/vehicle/search"

_MODEL_TO_SEARCH = {
    "honda civic": ("Honda", "Civic"),
    "toyota corolla": ("Toyota", "Corolla"),
    "toyota camry": ("Toyota", "Camry"),
    "mazda 3": ("Mazda", "Mazda3"),
    "mazda3": ("Mazda", "Mazda3"),
    "hyundai elantra": ("Hyundai", "Elantra"),
}


class CarvanaSource(Source):
    name = "carvana"
    description = "Carvana nationwide inventory (reverse-engineered JSON)"

    def iter_listings(self) -> Iterator[Listing]:
        for query in config.SEARCH_QUERIES:
            make_model = _MODEL_TO_SEARCH.get(query.lower().strip())
            if not make_model:
                continue
            make, model = make_model

            payload = {
                "pagination": {"offset": 0, "limit": 50},
                "sort": {"field": "price", "direction": "ASC"},
                "filters": {
                    "makes": [make],
                    "models": [model],
                    "priceRange": {
                        "min": config.MIN_PRICE,
                        "max": config.MAX_PRICE,
                    },
                    "yearRange": {
                        "min": config.MIN_YEAR,
                        "max": 2030,
                    },
                    "mileageRange": {
                        "min": 0,
                        "max": config.MAX_MILES or 200000,
                    },
                },
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
                log.warning("Carvana fetch failed: %s", e)
                continue

            time.sleep(config.POLITE_DELAY)

            if resp.status_code != 200:
                log.info(
                    "Carvana HTTP %s — endpoint may need refresh",
                    resp.status_code,
                )
                continue

            try:
                data = resp.json()
            except ValueError:
                continue

            items = (
                data.get("vehicles")
                or data.get("results")
                or data.get("items")
                or []
            )

            for it in items:
                try:
                    vehicle_id = (
                        it.get("vehicleId")
                        or it.get("id")
                        or it.get("stockNumber")
                    )
                    if not vehicle_id:
                        continue
                    url = f"https://www.carvana.com/vehicle/{vehicle_id}"
                    price = int(it.get("price") or it.get("listPrice") or 0) or None
                    year = it.get("year") or it.get("modelYear")
                    miles = it.get("mileage") or it.get("odometer")
                    trim = it.get("trim", "") or ""
                    title = f"{year or ''} {make} {model} {trim}".strip()
                except (ValueError, TypeError, KeyError):
                    continue

                if price is None:
                    continue
                if price < config.MIN_PRICE or price > config.MAX_PRICE:
                    continue

                yield Listing(
                    url=url,
                    source="carvana",
                    title=title,
                    price=price,
                    year=int(year) if year else None,
                    make=make.lower(),
                    model=model.lower(),
                    miles=int(miles) if miles else None,
                    location="Carvana (ships nationwide)",
                )


def get_sources():
    return [CarvanaSource()]
