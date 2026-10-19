from datetime import date

import httpx
import pytest
import respx
from connector_nbk.extract import FeedError, extract, parse_rates
from connector_nbk.settings import NbkSettings

URL = "https://nbk.test/rss/get_rates.cfm"

FEED = """<?xml version="1.0" encoding="utf-8"?>
<rates>
    <title>Official exchange rates of National Bank of Republic Kazakhstan</title>
    <date>17.10.2026</date>
    <item>
        <fullname>ДОЛЛАР США</fullname>
        <title>USD</title>
        <description>482.15</description>
        <quant>1</quant>
        <index>DOWN</index>
        <change>-1.20</change>
    </item>
    <item>
        <fullname>РОССИЙСКИЙ РУБЛЬ</fullname>
        <title>RUB</title>
        <description>5.91</description>
        <quant>1</quant>
        <index>UP</index>
        <change>+0.02</change>
    </item>
</rates>"""


@respx.mock
def test_one_record_per_currency() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200, text=FEED))
    settings = NbkSettings(url=URL)

    with httpx.Client() as http:
        records = list(extract(date(2026, 10, 17), http=http, settings=settings))

    assert route.calls[0].request.url.params["fdate"] == "17.10.2026"
    assert [r.key for r in records] == ["USD", "RUB"]
    assert records[0].payload == {
        "rates_date": "17.10.2026",
        "fullname": "ДОЛЛАР США",
        "title": "USD",
        "description": "482.15",
        "quant": "1",
        "index": "DOWN",
        "change": "-1.20",
    }


@pytest.mark.parametrize(
    "xml",
    [
        "<html><body>maintenance</body></html>",
        "<rates><date>17.10.2026</date></rates>",
        "<rates><date>17.10.2026</date><item><title>USD</title></item></rates>",
    ],
)
def test_rejects_unexpected_feed(xml: str) -> None:
    with pytest.raises(FeedError):
        parse_rates(xml)


def test_refuses_xml_entity_expansion() -> None:
    bomb = '<?xml version="1.0"?><!DOCTYPE r [<!ENTITY a "aaaa">]><rates>&a;</rates>'
    with pytest.raises(Exception, match="(?i)entit"):
        parse_rates(bomb)
