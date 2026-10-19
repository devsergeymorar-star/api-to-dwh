from collections.abc import Iterator
from datetime import date

import httpx
from defusedxml import ElementTree
from dwh_common import RawRecord, request

from connector_nbk.settings import NbkSettings

# <item> children as published by the NBK feed; values are kept as strings (raw layer).
ITEM_FIELDS = ("fullname", "title", "description", "quant", "index", "change")


class FeedError(ValueError):
    """The feed does not look like the NBK rates document we expect."""


def parse_rates(xml: str) -> tuple[str, list[dict[str, str]]]:
    """Return (rates date as published, one dict per currency)."""
    root = ElementTree.fromstring(xml)
    if root.tag != "rates":
        raise FeedError(f"unexpected root element <{root.tag}>")
    rates_date = (root.findtext("date") or "").strip()
    items = [
        {field: (item.findtext(field) or "").strip() for field in ITEM_FIELDS}
        for item in root.iter("item")
    ]
    if not rates_date or not items:
        raise FeedError("feed has no date or no currencies")
    if any(not item["title"] or not item["description"] for item in items):
        raise FeedError("currency without code or rate")
    return rates_date, items


def extract(day: date, *, http: httpx.Client, settings: NbkSettings) -> Iterator[RawRecord]:
    """One record per currency: the official KZT rate set for `day`."""
    response = request(http, settings.url, {"fdate": day.strftime("%d.%m.%Y")})
    rates_date, items = parse_rates(response.text)
    for item in items:
        yield RawRecord(key=item["title"], payload={"rates_date": rates_date, **item})
