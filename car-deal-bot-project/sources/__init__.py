"""
Source registry. Every enabled source gets its `get_sources()` called at
startup. To add a new site, append its module name here.
"""
from __future__ import annotations

import importlib
import logging
from typing import List

from .base import Source, iter_all_listings


log = logging.getLogger(__name__)


# Order doesn't affect correctness. Free sources first so they fill comps
# before paid sources run.
ALL_SOURCE_MODULES = [
    "sources.craigslist",
    "sources.ebay",
    "sources.carmax",
    "sources.carvana",
    "sources.bringatrailer",
    "sources.hemmings",
    "sources.generic_rss",
    "sources.marketcheck",   # paid — noop unless MARKETCHECK_API_KEY is set
]


def load_all() -> List[Source]:
    """
    Import each source module and call its `get_sources()` factory. Returns
    a flat list of Source instances in registration order.
    """
    sources: List[Source] = []
    for mod_name in ALL_SOURCE_MODULES:
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:
            log.error("Failed to import %s: %s", mod_name, e)
            continue

        factory = getattr(mod, "get_sources", None)
        if factory is None:
            log.warning("%s has no get_sources() — skipping", mod_name)
            continue

        try:
            produced = factory()
        except Exception as e:
            log.error("%s.get_sources() raised: %s", mod_name, e)
            continue

        for s in produced:
            sources.append(s)
            log.info("Loaded source: %s (%s)", s.name, s.description)
    return sources


__all__ = ["Source", "iter_all_listings", "load_all"]
