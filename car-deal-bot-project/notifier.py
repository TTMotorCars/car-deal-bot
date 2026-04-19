"""
SMS notifier using Twilio.

Env vars required (see .env.example):
  TWILIO_ACCOUNT_SID
  TWILIO_AUTH_TOKEN
  TWILIO_FROM_NUMBER       (your Twilio phone number, e.g., +13125551212)
  ALERT_TO_NUMBER          (your real phone, e.g., +17735551212)

If DRY_RUN=1 is set, we print instead of sending — useful for testing.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from storage import Listing
from deal_detector import DealVerdict


log = logging.getLogger(__name__)


def _format_body(listing: Listing, verdict: DealVerdict) -> str:
    pieces = []
    pieces.append("🚗 Deal alert")

    header_bits = []
    if listing.year:
        header_bits.append(str(listing.year))
    if listing.make:
        header_bits.append(listing.make.title())
    if listing.model:
        header_bits.append(listing.model.title())
    if header_bits:
        pieces.append(" ".join(header_bits))

    if listing.price is not None:
        pieces.append(f"${listing.price:,}")

    if listing.miles:
        pieces.append(f"{listing.miles:,} mi")

    if listing.location:
        pieces.append(f"@ {listing.location}")

    pieces.append(f"Why: {verdict.reason}")
    pieces.append(listing.url)
    return "\n".join(pieces)


def send_sms(listing: Listing, verdict: DealVerdict) -> bool:
    body = _format_body(listing, verdict)

    if os.environ.get("DRY_RUN") == "1":
        print("----- DRY RUN SMS -----")
        print(body)
        print("-----------------------")
        return True

    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    from_num = os.environ.get("TWILIO_FROM_NUMBER", "").strip()
    to_num = os.environ.get("ALERT_TO_NUMBER", "").strip()

    missing = [
        name for name, val in [
            ("TWILIO_ACCOUNT_SID", account_sid),
            ("TWILIO_AUTH_TOKEN", auth_token),
            ("TWILIO_FROM_NUMBER", from_num),
            ("ALERT_TO_NUMBER", to_num),
        ] if not val
    ]
    if missing:
        log.error(
            "Cannot send SMS — missing env vars: %s. "
            "Set DRY_RUN=1 to test without Twilio.",
            ", ".join(missing),
        )
        return False

    try:
        # Imported lazily so a missing dependency doesn't crash dry-runs.
        from twilio.rest import Client
    except ImportError:
        log.error("twilio package not installed. Run: pip install twilio")
        return False

    try:
        client = Client(account_sid, auth_token)
        client.messages.create(body=body, from_=from_num, to=to_num)
        return True
    except Exception as e:
        log.error("Twilio send failed: %s", e)
        return False
