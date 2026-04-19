"""
Decides which listings are "deals" worth texting about.

Two independent triggers — a listing is flagged if EITHER fires:

1. INSTANT_FLAG_UNDER — any listing below this price is automatically worth
   a look. (e.g., a $3,500 Civic, period.)

2. BELOW-MARKET — compare listing price to the median of similar cars (same
   make + model, +/- 2 years) we've seen in the last 30 days. If below the
   median by DEAL_THRESHOLD_PERCENT, flag it.

   Fallback: if we don't have enough comps yet, use MAX_PRICE / 2 as a naive
   "cheap enough" proxy.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Optional

import config
from storage import Listing, Storage


@dataclass
class DealVerdict:
    is_deal: bool
    reason: str
    median_comp: Optional[int]   # None if no comps available
    pct_below_median: Optional[float]  # e.g., 0.22 means 22% below median


def evaluate(listing: Listing, storage: Storage) -> DealVerdict:
    price = listing.price
    if price is None:
        return DealVerdict(False, "no price", None, None)

    # Trigger 1: absolute bargain floor.
    if price < config.INSTANT_FLAG_UNDER:
        return DealVerdict(
            True,
            f"under ${config.INSTANT_FLAG_UNDER} (absolute floor)",
            None,
            None,
        )

    # Trigger 2: below-market comparison.
    if listing.make and listing.model and listing.year:
        comps = storage.recent_comps(
            make=listing.make,
            model=listing.model,
            year=listing.year,
        )
        if len(comps) >= config.MIN_COMPS_FOR_MEDIAN:
            median = int(statistics.median(comps))
            pct_below = (median - price) / median
            if pct_below >= config.DEAL_THRESHOLD_PERCENT:
                return DealVerdict(
                    True,
                    f"{int(pct_below * 100)}% below median of ${median:,} "
                    f"(n={len(comps)} comps)",
                    median,
                    pct_below,
                )
            return DealVerdict(
                False,
                f"priced near market (median ${median:,}, n={len(comps)})",
                median,
                pct_below,
            )

    # Fallback when we don't have enough comps yet — naive: "cheap half".
    naive_deal_ceiling = config.MAX_PRICE // 2
    if price <= naive_deal_ceiling:
        return DealVerdict(
            True,
            f"under ${naive_deal_ceiling} (no comps yet, naive fallback)",
            None,
            None,
        )

    return DealVerdict(False, "no comps yet + above naive floor", None, None)
