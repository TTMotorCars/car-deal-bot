"""
SQLite storage: tracks listings we've already texted the user about, and keeps
a rolling price history so the deal-detector has comps to compare against.
"""
from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterable, Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_listings (
    url             TEXT PRIMARY KEY,
    source          TEXT NOT NULL,
    title           TEXT,
    price           INTEGER,
    year            INTEGER,
    make            TEXT,
    model           TEXT,
    miles           INTEGER,
    location        TEXT,
    first_seen_ts   INTEGER NOT NULL,
    alerted         INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_seen_make_model_year
    ON seen_listings(make, model, year);

CREATE INDEX IF NOT EXISTS idx_seen_first_seen
    ON seen_listings(first_seen_ts);
"""


@dataclass
class Listing:
    url: str
    source: str
    title: str
    price: Optional[int]
    year: Optional[int]
    make: Optional[str]
    model: Optional[str]
    miles: Optional[int]
    location: Optional[str]


class Storage:
    def __init__(self, path: str):
        self.path = path
        with self._conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Dedup
    # ------------------------------------------------------------------
    def already_seen(self, url: str) -> bool:
        with self._conn() as c:
            row = c.execute(
                "SELECT 1 FROM seen_listings WHERE url = ?", (url,)
            ).fetchone()
            return row is not None

    def record(self, listing: Listing, alerted: bool) -> None:
        """Insert (or replace) the listing. `alerted=True` means we texted it."""
        with self._conn() as c:
            c.execute(
                """
                INSERT OR REPLACE INTO seen_listings
                (url, source, title, price, year, make, model, miles, location,
                 first_seen_ts, alerted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    listing.url,
                    listing.source,
                    listing.title,
                    listing.price,
                    listing.year,
                    listing.make,
                    listing.model,
                    listing.miles,
                    listing.location,
                    int(time.time()),
                    1 if alerted else 0,
                ),
            )

    # ------------------------------------------------------------------
    # Market-value comps
    # ------------------------------------------------------------------
    def recent_comps(
        self,
        make: str,
        model: str,
        year: int,
        year_window: int = 2,
        days: int = 30,
    ) -> list[int]:
        """
        Return prices of similar cars seen in the last `days`.
        Matches same make + model, within +/- `year_window` years.
        """
        if not make or not model or not year:
            return []
        cutoff = int(time.time()) - days * 86400
        with self._conn() as c:
            rows = c.execute(
                """
                SELECT price FROM seen_listings
                WHERE make = ?
                  AND model = ?
                  AND year BETWEEN ? AND ?
                  AND price IS NOT NULL
                  AND price > 0
                  AND first_seen_ts >= ?
                """,
                (
                    make.lower(),
                    model.lower(),
                    year - year_window,
                    year + year_window,
                    cutoff,
                ),
            ).fetchall()
            return [r["price"] for r in rows]

    def stats(self) -> dict:
        with self._conn() as c:
            total = c.execute("SELECT COUNT(*) AS n FROM seen_listings").fetchone()["n"]
            alerted = c.execute(
                "SELECT COUNT(*) AS n FROM seen_listings WHERE alerted = 1"
            ).fetchone()["n"]
            return {"total_seen": total, "total_alerted": alerted}
