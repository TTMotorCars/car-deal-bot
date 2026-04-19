"""
Base class + registry for car listing sources.

To add a new site:
  1. Create a file in sources/ (e.g., sources/newcars.py).
  2. Subclass `Source`.
  3. Implement `iter_listings()`.
  4. Add the module name to `ALL_SOURCE_MODULES` in sources/__init__.py.

That's it — main.py auto-discovers every registered source.
"""
from __future__ import annotations

import abc
import logging
from typing import Iterator

from storage import Listing


log = logging.getLogger(__name__)


class Source(abc.ABC):
    # A short slug used in logs and the `source` column of the DB.
    # Example: "craigslist", "ebay", "carmax".
    name: str = ""

    # If True, the source is listed in the UI but iter_listings() returns
    # nothing unless the required env vars / config are present.
    # Keeps the list tidy and self-documenting.
    enabled: bool = True

    # Human-friendly summary for logging / status output.
    description: str = ""

    @abc.abstractmethod
    def iter_listings(self) -> Iterator[Listing]:
        """Yield Listing objects one at a time. Network errors should log +
        continue, never raise — one dead site shouldn't kill the run."""
        raise NotImplementedError

    # -------------- helpers subclasses can use ---------------------------

    def log_skipped(self, reason: str) -> None:
        log.info("[%s] skipped: %s", self.name, reason)

    def log_result(self, count: int) -> None:
        log.info("[%s] yielded %d listings", self.name, count)


def iter_all_listings(sources: list[Source]) -> Iterator[Listing]:
    """
    Walk every enabled source. Any source that raises is logged and skipped
    so one broken site can't take the whole run down.
    """
    for src in sources:
        if not src.enabled:
            log.info("[%s] disabled, skipping", src.name)
            continue
        count = 0
        try:
            for listing in src.iter_listings():
                count += 1
                yield listing
        except Exception as e:
            log.warning("[%s] crashed mid-run: %s", src.name, e)
        finally:
            src.log_result(count)
